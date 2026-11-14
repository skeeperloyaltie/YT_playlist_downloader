import os
import sys
import time
import re
import shutil
import urllib.parse
import argparse
import platform
import subprocess
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

def detect_environment():
    """
    Detects platform, architecture, and environment:
    - Android / Termux
    - Windows
    - macOS
    - Linux
    """
    is_termux = bool(
        os.environ.get("TERMUX_VERSION")
        or "com.termux" in os.environ.get("PREFIX", "")
        or os.path.exists("/data/data/com.termux")
    )
    is_android = (
        is_termux
        or bool(os.environ.get("ANDROID_ROOT"))
        or bool(os.environ.get("ANDROID_DATA"))
        or hasattr(sys, "getandroidapilevel")
        or os.path.exists("/system/build.prop")
    )

    sys_name = platform.system()
    arch = platform.machine() or "unknown"

    if is_termux:
        desc = f"Android / Termux ({arch})"
    elif is_android:
        desc = f"Android ({arch})"
    elif sys_name == "Windows":
        desc = f"Windows ({arch})"
    elif sys_name == "Darwin":
        desc = f"macOS ({arch})"
    else:
        desc = f"Linux ({arch})"

    return {
        'system': sys_name,
        'machine': arch,
        'is_android': is_android,
        'is_termux': is_termux,
        'description': desc
    }

def get_default_download_directory():
    """
    Dynamically determines the appropriate default download directory based on OS and architecture:
    - On Android / Termux: targets shared public device storage (/storage/shared/Music,
      ~/storage/shared/Music, ~/storage/music, /storage/emulated/0/Music, /sdcard/Music).
    - On Windows, macOS, Linux: defaults to user's ~/Music/ directory.
    """
    env = detect_environment()

    if env['is_android']:
        # Termux & Android shared storage paths in priority order
        candidates = [
            os.path.expanduser("~/storage/shared/Music"),
            os.path.expanduser("~/storage/music"),
            "/storage/shared/Music",
            "/storage/emulated/0/Music",
            "/sdcard/Music",
        ]

        # Return first existing directory
        for path in candidates:
            if os.path.isdir(path):
                return path

        # If ~/storage/shared exists (created by termux-setup-storage), create Music under it
        shared_root = os.path.expanduser("~/storage/shared")
        if os.path.isdir(shared_root):
            music_dir = os.path.join(shared_root, "Music")
            try:
                os.makedirs(music_dir, exist_ok=True)
                return music_dir
            except Exception:
                pass

        # If /storage/shared exists
        if os.path.isdir("/storage/shared"):
            music_dir = "/storage/shared/Music"
            try:
                os.makedirs(music_dir, exist_ok=True)
                return music_dir
            except Exception:
                pass

        # If /storage/emulated/0 exists
        if os.path.isdir("/storage/emulated/0"):
            music_dir = "/storage/emulated/0/Music"
            try:
                os.makedirs(music_dir, exist_ok=True)
                return music_dir
            except Exception:
                pass

        # If /sdcard exists
        if os.path.isdir("/sdcard"):
            music_dir = "/sdcard/Music"
            try:
                os.makedirs(music_dir, exist_ok=True)
                return music_dir
            except Exception:
                pass

        # Default fallback for Termux
        return os.path.expanduser("~/storage/shared/Music")

    # Windows / macOS / Linux
    return os.path.expanduser("~/Music/")

def normalize_download_directory(dir_path):
    """
    Normalizes download directory path.
    Specifically checks if a path is defaulting to Termux's app-specific scoped media directory
    (e.g., .../storage/shared/Android/media/com.termux) and redirects it to the shared Music folder.
    """
    if not dir_path:
        return get_default_download_directory()

    expanded = os.path.expanduser(os.path.expandvars(dir_path.strip()))

    # If the path points to Termux's scoped app-media directory under storage/shared:
    # redirect it directly to the shared Music directory
    if "Android/media/com.termux" in expanded:
        normalized = re.sub(r'Android/media/com\.termux.*', 'Music', expanded)
        return normalized

    return expanded

def find_ffmpeg(custom_location=None):
    """
    Locates the ffmpeg executable across platforms and common install paths.
    Returns the path to ffmpeg or None if not found.
    """
    if custom_location:
        if os.path.isfile(custom_location):
            return custom_location
        candidate = os.path.join(custom_location, "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")
        if os.path.isfile(candidate):
            return candidate

    # 1. Standard PATH
    which_ffmpeg = shutil.which("ffmpeg")
    if which_ffmpeg:
        return which_ffmpeg

    # 2. Termux specific paths
    termux_paths = [
        "/data/data/com.termux/files/usr/bin/ffmpeg",
        os.path.expanduser("~/../usr/bin/ffmpeg"),
    ]
    for p in termux_paths:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p

    # 3. Windows common paths
    if sys.platform == "win32":
        win_candidates = [
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Links\ffmpeg.exe"),
            r"C:\ffmpeg\bin\ffmpeg.exe",
            os.path.expandvars(r"%ProgramFiles%\ffmpeg\bin\ffmpeg.exe"),
            os.path.expandvars(r"%USERPROFILE%\scoop\shims\ffmpeg.exe"),
            r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg.exe"),
            os.path.join(os.getcwd(), "ffmpeg.exe"),
        ]
        winget_pkg_dir = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
        if os.path.isdir(winget_pkg_dir):
            try:
                for entry in os.listdir(winget_pkg_dir):
                    if "ffmpeg" in entry.lower():
                        nested = os.path.join(winget_pkg_dir, entry)
                        for root, _, files in os.walk(nested):
                            if "ffmpeg.exe" in files:
                                win_candidates.append(os.path.join(root, "ffmpeg.exe"))
            except Exception:
                pass

        for p in win_candidates:
            if os.path.isfile(p):
                return p

    # 4. Linux / macOS common paths
    unix_candidates = [
        "/usr/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
        "/opt/homebrew/bin/ffmpeg",
        "/usr/local/opt/ffmpeg/bin/ffmpeg",
    ]
    for p in unix_candidates:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p

    return None

def ensure_ffmpeg(custom_location=None, interactive=True):
    """
    Checks if ffmpeg exists. If missing, guides the user and offers auto-install on Termux.
    Returns (ffmpeg_path, has_ffmpeg).
    """
    ffmpeg_path = find_ffmpeg(custom_location)
    if ffmpeg_path:
        return ffmpeg_path, True

    env = detect_environment()
    print("\n" + "=" * 62)
    print(" [!] FFmpeg is NOT detected on this system!")
    print("     YouTube natively serves audio in WebM (Opus) or M4A.")
    print("     FFmpeg is required to convert downloaded audio to MP3.")
    print("=" * 62)

    if env['is_termux']:
        print("\n[*] Detected Environment: Termux (Android)")
        print("    You can install FFmpeg with one command:")
        print("    --> pkg install ffmpeg -y\n")
        if interactive and sys.stdin.isatty():
            try:
                ans = input("Would you like to install FFmpeg now via 'pkg install ffmpeg'? (y/n) [y]: ").strip().lower()
                if ans in ('y', 'yes', ''):
                    print("[*] Running 'pkg install -y ffmpeg'...")
                    res = subprocess.run(["pkg", "install", "-y", "ffmpeg"])
                    if res.returncode == 0:
                        ffmpeg_path = find_ffmpeg()
                        if ffmpeg_path:
                            print(f"[✓] FFmpeg successfully installed: {ffmpeg_path}\n")
                            return ffmpeg_path, True
                        else:
                            print("[!] FFmpeg package installed, but binary not found in PATH.\n")
                    else:
                        print("[!] 'pkg install ffmpeg' failed. Please run 'pkg install ffmpeg' manually in Termux.\n")
            except Exception as e:
                print(f"[!] Could not run automatic install: {e}\n")
    elif env['system'] == "Windows":
        print("\n[*] To enable MP3 conversion on Windows, install FFmpeg:")
        print("    Run in PowerShell/Terminal: winget install Gyan.FFmpeg")
        print("    Or via Scoop: scoop install ffmpeg\n")
    elif env['system'] == "Darwin":
        print("\n[*] To enable MP3 conversion on macOS, install FFmpeg:")
        print("    Run in Terminal: brew install ffmpeg\n")
    else:
        print("\n[*] To enable MP3 conversion on Linux, install FFmpeg:")
        print("    Run: sudo apt install ffmpeg  (or your distribution's package manager)\n")

    return None, False

def convert_existing_webm(directory, ffmpeg_path=None, remove_source=True):
    """
    Finds all .webm files in directory (and subdirectories), converts them to .mp3 using FFmpeg,
    and removes the original .webm files.
    """
    ffmpeg_bin = ffmpeg_path or find_ffmpeg()
    if not ffmpeg_bin:
        print("[!] Cannot convert existing .webm files: FFmpeg is not installed.")
        return []

    directory = normalize_download_directory(directory)
    if not os.path.isdir(directory):
        return []

    webm_files = []
    for root, _, files in os.walk(directory):
        for f in files:
            if f.lower().endswith(".webm"):
                webm_files.append(os.path.join(root, f))

    if not webm_files:
        return []

    print(f"\n[i] Found {len(webm_files)} existing .webm file(s) in '{directory}'.")
    print("    Converting to MP3 (192kbps)...")

    converted = []
    for webm_path in webm_files:
        base_name, _ = os.path.splitext(webm_path)
        mp3_path = f"{base_name}.mp3"

        # If MP3 already exists and is non-empty, remove redundant webm
        if os.path.isfile(mp3_path) and os.path.getsize(mp3_path) > 0:
            print(f"  [✓] MP3 already exists: '{os.path.basename(mp3_path)}'.")
            if remove_source:
                try:
                    os.remove(webm_path)
                    print(f"      Removed leftover '{os.path.basename(webm_path)}'.")
                except Exception as e:
                    print(f"      Could not remove '{webm_path}': {e}")
            converted.append(mp3_path)
            continue

        print(f"  --> Converting: '{os.path.basename(webm_path)}' -> '{os.path.basename(mp3_path)}'...")
        cmd = [
            ffmpeg_bin,
            "-y",
            "-i", webm_path,
            "-vn",
            "-ar", "44100",
            "-ac", "2",
            "-b:a", "192k",
            mp3_path
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0 and os.path.isfile(mp3_path) and os.path.getsize(mp3_path) > 0:
                print(f"  [✓] Converted successfully: '{os.path.basename(mp3_path)}'")
                if remove_source:
                    try:
                        os.remove(webm_path)
                    except Exception:
                        pass
                converted.append(mp3_path)
            else:
                err_msg = res.stderr.strip().splitlines()[-1] if res.stderr else "Unknown error"
                print(f"  [!] Conversion failed for '{os.path.basename(webm_path)}': {err_msg}")
        except Exception as e:
            print(f"  [!] Exception during conversion of '{webm_path}': {e}")

    print(f"[✓] Converted {len(converted)}/{len(webm_files)} file(s) to MP3.\n")
    return converted

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

def get_base_ydl_opts(directory, browser_cookie=None, cookie_file=None, ffmpeg_path=None):
    """Configures yt-dlp download options with FFmpeg detection and cookie support."""
    has_ffmpeg = bool(ffmpeg_path)

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
        opts['ffmpeg_location'] = ffmpeg_path
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

def download_single_song(video_url, video_title, directory, base_ydl_opts, ffmpeg_path=None):
    """Download a single song into directory thread-safely."""
    directory = normalize_download_directory(directory)
    safe_title = sanitize_filename(video_title)
    expected_mp3 = os.path.join(directory, f"{safe_title}.mp3")
    expected_webm = os.path.join(directory, f"{safe_title}.webm")

    # Fast skip if MP3 already exists locally
    if os.path.isfile(expected_mp3) and os.path.getsize(expected_mp3) > 0:
        if os.path.isfile(expected_webm):
            try:
                os.remove(expected_webm)
            except Exception:
                pass
        print(f"Skipping (already exists): {safe_title}.mp3")
        return f"{safe_title}.mp3"

    # If WebM exists from previous download and we have ffmpeg, convert it directly
    if os.path.isfile(expected_webm) and os.path.getsize(expected_webm) > 0 and ffmpeg_path:
        print(f"Found existing WebM for '{video_title}'. Converting directly to MP3...")
        cmd = [
            ffmpeg_path, "-y", "-i", expected_webm,
            "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", expected_mp3
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0 and os.path.isfile(expected_mp3) and os.path.getsize(expected_mp3) > 0:
                try:
                    os.remove(expected_webm)
                except Exception:
                    pass
                print(f"Successfully converted: {safe_title}.mp3")
                return f"{safe_title}.mp3"
        except Exception:
            pass

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

        # Verify outcome: ensure MP3 is produced and leftover WebM is cleaned up
        if os.path.isfile(expected_mp3):
            if os.path.isfile(expected_webm):
                try:
                    os.remove(expected_webm)
                except Exception:
                    pass
            return f"{safe_title}.mp3"
        elif os.path.isfile(expected_webm):
            # If yt-dlp downloaded raw webm, convert it using ffmpeg if available
            if ffmpeg_path:
                print(f"Converting downloaded WebM to MP3: {safe_title}...")
                cmd = [
                    ffmpeg_path, "-y", "-i", expected_webm,
                    "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", expected_mp3
                ]
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if res.returncode == 0 and os.path.isfile(expected_mp3):
                    try:
                        os.remove(expected_webm)
                    except Exception:
                        pass
                    return f"{safe_title}.mp3"
            return f"{safe_title}.webm"

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

def download_playlist(playlist_url, directory, max_concurrent=4, browser_cookie=None, cookie_file=None, max_mix_songs=50, ffmpeg_path=None):
    """
    Downloads all songs from a YouTube Playlist or YouTube Mix (both saved and unsaved).
    Supports:
    - YouTube Mix / Radio (list=RD..., list=UL...): dynamic mix extraction
    - Saved Playlists (list=PL..., list=OLAK...): full extraction
    - Liked Videos (list=LL) & Watch Later (list=WL): cookie authentication support with graceful fallback
    - Single video links
    """
    directory = normalize_download_directory(directory)
    if not os.path.exists(directory):
        try:
            os.makedirs(directory, exist_ok=True)
        except Exception as e:
            print(f"[!] Warning: Could not create directory '{directory}': {e}")

    # Automatically convert any existing WebM files sitting in the destination directory
    if ffmpeg_path:
        convert_existing_webm(directory, ffmpeg_path)

    parsed_info = normalize_youtube_url(playlist_url)
    clean_url = parsed_info['clean_url']
    url_type = parsed_info['type']
    list_id = parsed_info['list_id']
    video_id = parsed_info['video_id']
    is_private = parsed_info['is_private']

    base_opts, has_ffmpeg = get_base_ydl_opts(directory, browser_cookie, cookie_file, ffmpeg_path)

    if not has_ffmpeg:
        print("[!] Notice: FFmpeg is not installed or not in PATH.")
        print("    Audio will be saved in best native format (.m4a/.webm) without MP3 conversion.")
        print("    To get MP3s, install ffmpeg (e.g. `winget install Gyan.FFmpeg` or `pkg install ffmpeg`).\n")

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
                    executor.submit(download_single_song, url, title, directory, base_opts, ffmpeg_path): title
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

            # Auto-convert any lingering webm files in directory after download
            if ffmpeg_path:
                convert_existing_webm(directory, ffmpeg_path)

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
    print("\033[1;33m   M-Pesa Support: 0716642889\033[0m")
    print()

    if youtube_dl is None:
        print("[!] Error: 'yt-dlp' is not installed.")
        print("    Please install project requirements via:")
        print("    pip install -r requirements.txt\n")
        sys.exit(1)

    env = detect_environment()
    default_dir = get_default_download_directory()

    parser = argparse.ArgumentParser(description="Download YouTube Playlists, Mixes (Radio), and Songs as MP3")
    parser.add_argument("urls", nargs="*", help="YouTube URLs to download (playlists, mixes, or songs)")
    parser.add_argument("-d", "--dir", default=None, help=f"Download directory (default: {default_dir})")
    parser.add_argument("-c", "--concurrent", type=int, default=4, help="Max concurrent downloads (default: 4)")
    parser.add_argument("-b", "--browser", default=None, help="Browser to load YouTube cookies from (e.g. chrome, edge, firefox, brave)")
    parser.add_argument("--cookies", default=None, help="Path to cookies.txt file for private playlists (e.g. Liked Videos 'LL')")
    parser.add_argument("-m", "--mix-limit", type=int, default=50, help="Max songs to download for dynamic YouTube Mixes (default: 50)")
    parser.add_argument("--convert", "--convert-only", dest="convert_only", action="store_true", help="Convert all existing .webm files in directory to .mp3 and exit")
    parser.add_argument("--ffmpeg-location", default=None, help="Path to ffmpeg executable or directory")

    args = parser.parse_args()

    download_directory = normalize_download_directory(args.dir) if args.dir else default_dir
    ffmpeg_path, has_ffmpeg = ensure_ffmpeg(args.ffmpeg_location, interactive=True)

    # Handle conversion only mode
    if args.convert_only:
        print(f"\nScanning for existing .webm files in: {download_directory}")
        convert_existing_webm(download_directory, ffmpeg_path)
        print("Conversion complete. Exiting...")
        return

    # If existing webm files are found in destination, convert them immediately
    if has_ffmpeg and os.path.isdir(download_directory):
        convert_existing_webm(download_directory, ffmpeg_path)

    links = args.urls
    browser_cookie = args.browser
    cookie_file = args.cookies
    max_concurrent = args.concurrent
    mix_limit = args.mix_limit

    if env['is_termux'] and not os.path.exists(os.path.expanduser("~/storage")):
        print("[!] Note: Termux detected. If downloads cannot write to shared storage,")
        print("    run 'termux-setup-storage' in Termux to grant storage permissions.\n")

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
    print(f"Platform: {env['description']}")
    print(f"Download Directory: {download_directory}")
    print(f"FFmpeg Status: {'Enabled (' + ffmpeg_path + ')' if has_ffmpeg else 'Not installed (MP3 conversion disabled)'}")
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
            max_mix_songs=mix_limit,
            ffmpeg_path=ffmpeg_path
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
