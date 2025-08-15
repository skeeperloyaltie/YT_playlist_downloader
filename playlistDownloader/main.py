import yt_dlp
import os
import time
import sys
import pyfiglet
import platform
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

class NetworkError(Exception):
    pass

class SilentLogger:
    def debug(self, msg):
        pass
    def warning(self, msg):
        pass
    def error(self, msg):
        print(f"yt-dlp error: {msg}")

def check_ffmpeg():
    if not shutil.which('ffmpeg'):
        print("Error: ffmpeg is not installed or not found in PATH. Please install ffmpeg.")
        sys.exit(1)

def check_permissions(directory):
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except Exception as e:
            return False, f"Cannot create directory {directory}: {str(e)}"
    if not os.access(directory, os.W_OK):
        return False, f"No write permission for {directory}"
    return True, None

def get_default_directory(file_format):
    system = platform.system().lower()
    is_termux = os.path.exists(os.path.expanduser("~/storage/shared"))
    if is_termux:
        base_dir = os.path.expanduser("~/storage/shared")
        return os.path.join(base_dir, "Music" if file_format == 'audio' else "Videos")
    elif system == "linux":
        return os.path.expanduser("~/Music" if file_format == 'audio' else "~/Videos")
    elif system == "windows":
        return os.path.expanduser(os.path.join("~", "Music" if file_format == 'audio' else "Videos"))
    else:
        return os.path.join(os.getcwd(), "Music" if file_format == 'audio' else "Videos")

def download_single_item(video_url, video_title, directory, ydl_opts, file_format):
    try:
        with yt_dlp.YoutubeDL({**ydl_opts, 'simulate': True}) as ydl:
            info = ydl.extract_info(video_url, download=False)
            expected_filename = ydl.prepare_filename(info)
            if os.path.isfile(expected_filename):
                print(f'{expected_filename} already exists, skipping...')
                return expected_filename
    except Exception as e:
        print(f"Error checking file existence for {video_title}: {str(e)}")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Downloading: {video_title} as {file_format.upper()}...")
            ydl.download([video_url])
            if os.path.isfile(expected_filename) and os.path.getsize(expected_filename) > 0:
                print(f"Completed: {expected_filename}")
                return expected_filename
            else:
                print(f"Failed: {video_title} (file missing or empty)")
                return None
    except yt_dlp.utils.DownloadError as e:
        if "network" in str(e).lower() or "connection" in str(e).lower():
            raise NetworkError(f"Network error for '{video_title}': {str(e)}")
        print(f"Failed: {video_title} ({str(e)})")
        return None
    except Exception as e:
        print(f"Failed: {video_title} (Unexpected error: {str(e)})")
        return None

def download_playlist(playlist_url, directory, file_format='audio', max_concurrent=2):
    has_permission, error_msg = check_permissions(directory)
    if not has_permission:
        print(f"Error: {error_msg}")
        if os.path.exists(os.path.expanduser("~/storage")):
            print("Please run 'termux-setup-storage' to grant storage access.")
        else:
            print("Please ensure the directory is writable or choose a different location.")
        return [], []

    ydl_opts = {
        'outtmpl': os.path.join(directory, '%(title)s.%(ext)s'),
        'noplaylist': False,
        'extract_flat': False,
        'playlist_items': '1-3000',
        'ignoreerrors': True,
        'retries': 10,
        'fragment_retries': 10,
        'concurrent_fragments': 4,
        'http_chunk_size': 10485760,
        'logger': SilentLogger(),
    }

    if file_format == 'audio':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        ydl_opts.update({
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferredformat': 'mp4',
            }],
        })

    print("Analyzing playlist URL...")
    time.sleep(1)
    print("Extracting playlist metadata...")
    time.sleep(1)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)
            video_list = []
            failed_downloads = []

            if 'entries' not in info:
                print(f"Single {'video' if file_format == 'video' else 'audio'} detected.")
                video_title = info.get('title', 'Unknown Title')
                video_url = info.get('url') or info.get('webpage_url') or playlist_url
                video_file = download_single_item(video_url, video_title, directory, ydl_opts, file_format)
                if video_file:
                    video_list.append(video_file)
                else:
                    failed_downloads.append(video_title)
                return video_list, failed_downloads

            print(f"Found playlist: {info.get('title', 'Unknown Playlist')} "
                  f"with {len(info['entries'])} items")

            download_tasks = []
            for entry in info['entries']:
                if not entry:
                    print("Invalid entry in playlist, skipping...")
                    failed_downloads.append("Invalid Entry")
                    continue
                video_title = entry.get('title', 'Unknown Title')
                video_url = entry.get('url') or entry.get('webpage_url')
                if not video_url:
                    print(f"No valid URL for '{video_title}', skipping...")
                    failed_downloads.append(video_title)
                    continue
                download_tasks.append((video_url, video_title))

            total_tasks = len(download_tasks)
            print(f"Starting download of {total_tasks} items...")
            with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
                future_to_title = {
                    executor.submit(download_single_item, url, title, directory, ydl_opts, file_format): title
                    for url, title in download_tasks
                }
                for i, future in enumerate(as_completed(future_to_title), 1):
                    title = future_to_title[future]
                    try:
                        video_file = future.result()
                        if video_file:
                            video_list.append(video_file)
                        else:
                            failed_downloads.append(title)
                        print(f"Progress: {i}/{total_tasks} items completed")
                    except NetworkError as e:
                        raise
                    except Exception as e:
                        print(f"Failed: {title} (Unexpected error: {str(e)})")
                        failed_downloads.append(title)
                        print(f"Progress: {i}/{total_tasks} items completed")

            return video_list, failed_downloads

    except NetworkError as e:
        print(f"Critical network error: {str(e)}. Aborting playlist download.")
        return [], failed_downloads
    except Exception as e:
        print(f"Unexpected error processing playlist: {str(e)}. Aborting playlist download.")
        return [], failed_downloads

if __name__ == '__main__':
    check_ffmpeg()
    result = pyfiglet.figlet_format("YOUTUBE PLAYLIST DOWNLOADER")
    print(result)
    print("\033[1;34m          Created By a Skeeper\033[0m")
    print("\033[2;32m     do not suck on using the application\033[0m")
    print("\033[2;32m            skeeperloyaltie\033[0m")
    print("\033[1;32m   Mail: skeeperloyaltie@pm.me\033[0m")
    print()

    while True:
        file_format = input("Enter download format (audio/mp3 or video/mp4): ").lower()
        if file_format in ['audio', 'mp3', 'video', 'mp4']:
            file_format = 'audio' if file_format in ['audio', 'mp3'] else 'video'
            break
        print("Invalid input. Please enter 'audio', 'mp3', 'video', or 'mp4'.")

    download_directory = get_default_directory(file_format)
    print(f"Default download directory: {download_directory}")
    custom_dir = input("Enter custom directory (or press Enter to use default): ")
    if custom_dir:
        download_directory = custom_dir

    has_permission, error_msg = check_permissions(download_directory)
    if not has_permission:
        print(f"Error: {error_msg}")
        if os.path.exists(os.path.expanduser("~/storage")):
            print("Termux detected. Ensure 'termux-setup-storage' has been run and storage permissions are granted.")
            input("Press Enter to continue or Ctrl+C to abort...")
        else:
            print("Please ensure the directory is writable or choose a different location.")
        sys.exit(1)

    links = []
    while len(links) < 5:
        link = input("Enter a YouTube playlist URL (or press Enter to finish): ")
        if not link:
            break
        links.append(link)

    if links:
        print("\nYouTube Links entered:")
        for link in links:
            print(f"['{link}']")
        print()

    if links:
        for playlist_url in links:
            print(f"\nProcessing playlist: {playlist_url}")
            downloaded_files, failed_downloads = download_playlist(playlist_url, download_directory, file_format, max_concurrent=2)

            if downloaded_files:
                print("\nDownloaded files:")
                for file in downloaded_files:
                    print(f"- {file}")
            else:
                print("No files downloaded for this playlist.")

            if failed_downloads:
                print("\nFailed downloads:")
                for title in failed_downloads:
                    print(f"- {title}")

            time.sleep(2)

        print("\nWow - we did it - Thanks for helping!")
    else:
        print("No links provided. Exiting...")