import os
import sys
import time
import re
import shutil
import urllib.parse
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import yt_dlp as youtube_dl
except ImportError:
    youtube_dl = None

try:
    import pyfiglet
except ImportError:
    pyfiglet = None

class NetworkError(Exception):
    pass

def sanitize_filename(name):
    """Sanitize title to match Windows and cross-platform filename constraints."""
    if not name:
        return "Unknown_Title"
    # Replace illegal characters: < > : " / \ | ? *
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
    sanitized = re.sub(r'[\x00-\x1f\x7f]', '', sanitized)
    sanitized = sanitized.strip('. ')
    return sanitized or "Unknown_Title"

def normalize_youtube_url(url):
    """
    Normalizes YouTube URLs for proper playlist and mix handling:
    - YouTube Mixes (list=RD... or list=UL...): Mixes are dynamic and require
      preserving the anchor video ID (v=...) to build the radio queue properly.
    - Standard playlists (list=PL..., list=OLAK...): Canonical playlist URL.
    - User/Private playlists (list=LL, list=WL): Liked Videos / Watch Later.
    - Single video: Standalone watch URL.
    """
    url = url.strip()
    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query)

    list_id = qs.get('list', [None])[0]
    video_id = qs.get('v', [None])[0]

    # Handle youtu.be shortlinks with ?list=...
    if 'youtu.be' in parsed.netloc:
        path_id = parsed.path.lstrip('/')
        if path_id:
            video_id = path_id

    is_mix = bool(list_id and (list_id.startswith(('RD', 'UL', 'PU')) or 'radio' in qs))
    is_liked_videos = (list_id == 'LL')
    is_watch_later = (list_id == 'WL')

    if is_mix:
        # YouTube Mixes MUST preserve both seed video_id and list_id
        if video_id and list_id:
            clean_url = f"https://www.youtube.com/watch?v={video_id}&list={list_id}"
        elif list_id:
            clean_url = f"https://www.youtube.com/watch?list={list_id}"
        else:
            clean_url = url
        return {
            'type': 'mix',
            'clean_url': clean_url,
            'list_id': list_id,
            'video_id': video_id,
            'is_private': False
        }

    if list_id:
        clean_url = f"https://www.youtube.com/playlist?list={list_id}"
        return {
            'type': 'playlist',
            'clean_url': clean_url,
            'list_id': list_id,
            'video_id': video_id,
            'is_private': is_liked_videos or is_watch_later
        }

    if video_id:
        clean_url = f"https://www.youtube.com/watch?v={video_id}"
        return {
            'type': 'video',
            'clean_url': clean_url,
            'list_id': None,
            'video_id': video_id,
            'is_private': False
        }

    return {
        'type': 'unknown',
        'clean_url': url,
        'list_id': None,
        'video_id': None,
        'is_private': False
    }

def get_base_ydl_opts(directory, browser_cookie=None, cookie_file=None):
    """Configures yt-dlp download options with FFmpeg detection and cookie support."""
    has_ffmpeg = bool(shutil.which('ffmpeg'))

    opts = {
        'ignoreerrors': True,
        'retries': 10,
        'fragment_retries': 10,
        'concurrent_fragments': 4,
        'http_chunk_size': 10485760,
        'download_archive': os.path.join(directory, '.download_archive.txt'),
        'outtmpl': os.path.join(directory, '%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': True,
    }

    if has_ffmpeg:
        opts['format'] = 'bestaudio/best'
        opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        # Fallback if FFmpeg is not installed: download native best audio stream
        opts['format'] = 'bestaudio/best'

    # Support cookies for private playlists (e.g. Liked Videos 'LL', Watch Later 'WL')
    if cookie_file and os.path.isfile(cookie_file):
        opts['cookiefile'] = cookie_file
    elif browser_cookie and browser_cookie.lower() not in ('none', 'no', ''):
        opts['cookiesfrombrowser'] = (browser_cookie.lower(),)

    return opts, has_ffmpeg

def download_single_song(video_url, video_title, directory, base_ydl_opts):
    """Download a single song into directory thread-safely."""
    safe_title = sanitize_filename(video_title)
    expected_mp3 = os.path.join(directory, f"{safe_title}.mp3")

    # Fast skip if file already exists locally
    if os.path.isfile(expected_mp3):
        print(f"Skipping (already exists): {safe_title}.mp3")
        return f"{safe_title}.mp3"

    single_opts = base_ydl_opts.copy()
    single_opts.update({
        'noplaylist': True,  # Prevent worker threads from re-extracting playlists
        'extract_flat': False,
        'outtmpl': os.path.join(directory, '%(title)s.%(ext)s'),
    })

    try:
        with youtube_dl.YoutubeDL(single_opts) as ydl:
            print(f"Downloading: {video_title}")
            error_code = ydl.download([video_url])
            if error_code != 0:
                print(f"Download returned code {error_code} for '{video_title}'.")
                return None
        return f"{safe_title}.mp3"
    except youtube_dl.utils.DownloadError as e:
        err = str(e)
        if "network" in err.lower() or "connection" in err.lower():
            raise NetworkError(f"Network error for '{video_title}': {err}")
        print(f"Error downloading '{video_title}': {err}. Skipping...")
        return None
    except Exception as e:
        print(f"Unexpected error for '{video_title}': {str(e)}. Skipping...")
        return None

def download_playlist(playlist_url, directory, max_concurrent=4, browser_cookie=None, cookie_file=None, max_mix_songs=50):
    """
    Downloads all songs from a YouTube Playlist or YouTube Mix (both saved and unsaved).
    Supports:
    - YouTube Mix / Radio (list=RD..., list=UL...): dynamic mix extraction
    - Saved Playlists (list=PL..., list=OLAK...): full extraction
    - Liked Videos (list=LL) & Watch Later (list=WL): cookie authentication support with graceful fallback
    - Single video links
    """
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

    parsed_info = normalize_youtube_url(playlist_url)
    clean_url = parsed_info['clean_url']
    url_type = parsed_info['type']
    list_id = parsed_info['list_id']
    video_id = parsed_info['video_id']
    is_private = parsed_info['is_private']

    base_opts, has_ffmpeg = get_base_ydl_opts(directory, browser_cookie, cookie_file)

    if not has_ffmpeg:
        print("[!] Notice: FFmpeg is not installed or not in PATH.")
        print("    Audio will be saved in best native format (.m4a/.webm) without MP3 conversion.")
        print("    To get MP3s, install ffmpeg (e.g. `winget install Gyan.FFmpeg`).\n")

    # Options for fast playlist/mix metadata extraction
    extract_opts = base_opts.copy()
    extract_opts.update({
        'extract_flat': 'in_playlist',
        'noplaylist': False,
        'skip_download': True,
    })

    # For dynamic YouTube mixes, set a limit to avoid endless pagination
    if url_type == 'mix' and max_mix_songs:
        extract_opts['playlistend'] = max_mix_songs

    print(f"\nAnalyzing URL: {playlist_url}")
    if url_type == 'mix':
        print(f"Detected YouTube Mix (Dynamic Radio): {clean_url}")
    elif url_type == 'playlist':
        print(f"Detected YouTube Playlist (ID: {list_id}): {clean_url}")
    elif url_type == 'video':
        print(f"Detected Single Video: {clean_url}")

    print("Extracting metadata...")
    time.sleep(1)

    try:
        with youtube_dl.YoutubeDL(extract_opts) as ydl:
            try:
                info = ydl.extract_info(clean_url, download=False)
            except youtube_dl.utils.DownloadError as e:
                err_str = str(e)
                # Check for private playlist / authentication errors (e.g. list=LL without cookies)
                if any(w in err_str.lower() for w in ("private", "sign in", "login", "cookie")):
                    print(f"\n[!] Access denied to playlist '{list_id}': {err_str}")
                    if is_private or list_id == 'LL':
                        print("    Note: 'Liked Videos' (list=LL) is private and requires YouTube account cookies.")
                        print("    You can run with browser cookies enabled (e.g. Chrome/Edge) to download all liked songs.")
                    # Gracefully fall back to downloading the seed song if one was in the URL
                    if video_id:
                        fallback_url = f"https://www.youtube.com/watch?v={video_id}"
                        print(f"\n[*] Gracefully falling back to downloading the seed song: {fallback_url}")
                        res = download_single_song(fallback_url, f"Song_{video_id}", directory, base_opts)
                        return [res] if res else []
                raise

            if not info:
                print("Could not retrieve playlist metadata.")
                return []

            # Handle single video (no 'entries' field)
            raw_entries = info.get('entries')
            if raw_entries is None:
                print("Single video detected, treating as single-item download.")
                v_title = info.get('title', f"Song_{video_id or 'unknown'}")
                v_url = clean_url if clean_url else playlist_url
                res = download_single_song(v_url, v_title, directory, base_opts)
                return [res] if res else []

            # Convert generator/iterator to list safely
            entries = [e for e in raw_entries if e is not None]

            playlist_title = info.get('title') or ('YouTube Mix' if url_type == 'mix' else 'YouTube Playlist')
            print(f"Found {url_type.capitalize()}: '{playlist_title}' with {len(entries)} song(s)")

            if not entries:
                if video_id:
                    fallback_url = f"https://www.youtube.com/watch?v={video_id}"
                    print(f"No songs extracted in playlist, falling back to seed song: {fallback_url}")
                    res = download_single_song(fallback_url, f"Song_{video_id}", directory, base_opts)
                    return [res] if res else []
                print("No downloadable songs found.")
                return []

            # Prepare individual song download tasks
            download_tasks = []
            for entry in entries:
                v_title = entry.get('title', 'Unknown Title')
                if v_title in ('[Private video]', '[Deleted video]'):
                    print(f"Skipping unavailable video: {v_title}")
                    continue

                v_id = entry.get('id')
                v_url = entry.get('url') or entry.get('webpage_url')

                # Build clean watch URL to ensure worker threads do not re-trigger playlist mode
                if v_id:
                    clean_song_url = f"https://www.youtube.com/watch?v={v_id}"
                elif v_url:
                    if not v_url.startswith(('http://', 'https://')):
                        clean_song_url = f"https://www.youtube.com/watch?v={v_url.split(':')[-1]}"
                    else:
                        clean_song_url = v_url
                else:
                    print(f"No valid URL or ID for '{v_title}', skipping...")
                    continue

                download_tasks.append((clean_song_url, v_title))

            # Download songs concurrently
            video_list = []
            failed_downloads = []

            with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
                future_to_title = {
                    executor.submit(download_single_song, url, title, directory, base_opts): title
                    for url, title in download_tasks
                }
                for future in as_completed(future_to_title):
                    title = future_to_title[future]
                    try:
                        video_file = future.result()
                        if video_file:
                            video_list.append(video_file)
                        else:
                            failed_downloads.append(title)
                    except NetworkError as e:
                        print(f"\n[!] Network error: {e}. Aborting playlist.")
                        raise
                    except Exception as e:
                        print(f"\n[!] Error for '{title}': {e}. Skipping...")
                        failed_downloads.append(title)

            if failed_downloads:
                print("\nFailed to download the following songs:")
                for title in failed_downloads:
                    print(f"- {title}")

            print(f"\nSuccessfully downloaded {len(video_list)}/{len(download_tasks)} songs!")
            return video_list

    except NetworkError as e:
        print(f"Critical network error: {e}. Aborting playlist download.")
        return []
    except Exception as e:
        print(f"Unexpected error processing playlist: {e}. Aborting playlist download.")
        return []

def main():
    # Banner
    if pyfiglet:
        result = pyfiglet.figlet_format("YOUTUBE PLAYLIST DOWNLOADER")
        print(result)
    else:
        print("=" * 50)
        print("          YOUTUBE PLAYLIST DOWNLOADER")
        print("=" * 50)
    print("\033[1;34m          Created By a Skeeper\033[0m")
    print("\033[2;32m     do not suck on using the application\033[0m")
    print("\033[2;32m            skeeperloyaltie\033[0m")
    print("\033[1;32m   Mail: skeeperloyaltie@pm.me\033[0m")
    print()

    if youtube_dl is None:
        print("[!] Error: 'yt-dlp' is not installed.")
        print("    Please install project requirements via:")
        print("    pip install -r requirements.txt\n")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Download YouTube Playlists, Mixes (Radio), and Songs as MP3")
    parser.add_argument("urls", nargs="*", help="YouTube URLs to download (playlists, mixes, or songs)")
    parser.add_argument("-d", "--dir", default=os.path.expanduser("~/Music/"), help="Download directory (default: ~/Music/)")
    parser.add_argument("-c", "--concurrent", type=int, default=4, help="Max concurrent downloads (default: 4)")
    parser.add_argument("-b", "--browser", default=None, help="Browser to load YouTube cookies from (e.g. chrome, edge, firefox, brave)")
    parser.add_argument("--cookies", default=None, help="Path to cookies.txt file for private playlists (e.g. Liked Videos 'LL')")
    parser.add_argument("-m", "--mix-limit", type=int, default=50, help="Max songs to download for dynamic YouTube Mixes (default: 50)")

    args = parser.parse_args()

    links = args.urls
    browser_cookie = args.browser
    cookie_file = args.cookies
    download_directory = args.dir
    max_concurrent = args.concurrent
    mix_limit = args.mix_limit

    # Interactive mode if no URLs provided on CLI
    if not links:
        links = []
        while len(links) < 5:
            link = input("Enter a YouTube playlist/mix URL (or press Enter to finish): ").strip()
            if not link:
                break
            links.append(link)

        if not links:
            print("No links provided. Exiting...")
            return

        # Check if any URL contains a private playlist (like list=LL or list=WL)
        has_private = any(normalize_youtube_url(l)['is_private'] for l in links)
        if has_private and not browser_cookie and not cookie_file:
            print("\n[i] Detected a private playlist (e.g. Liked Videos 'list=LL').")
            browser_choice = input("Enter browser to load cookies from (chrome/edge/firefox/brave/none) [none]: ").strip()
            if browser_choice and browser_choice.lower() != 'none':
                browser_cookie = browser_choice

    print("\nYouTube Links to process:")
    for link in links:
        print(f"- {link}")
    print(f"Download Directory: {download_directory}")
    print(f"Max Concurrent: {max_concurrent}")
    if browser_cookie:
        print(f"Cookies from browser: {browser_cookie}")
    if cookie_file:
        print(f"Cookies from file: {cookie_file}")
    print()

    for playlist_url in links:
        downloaded = download_playlist(
            playlist_url=playlist_url,
            directory=download_directory,
            max_concurrent=max_concurrent,
            browser_cookie=browser_cookie,
            cookie_file=cookie_file,
            max_mix_songs=mix_limit
        )

        if downloaded:
            print("\nDownloaded files for this playlist:")
            for f in downloaded:
                print(f"  ✓ {f}")
        else:
            print("No files downloaded for this playlist.")

        time.sleep(1)

    print("\nWow - we did it - Thanks for helping!")

if __name__ == '__main__':
    main()
