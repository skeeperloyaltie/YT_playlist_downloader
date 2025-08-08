import yt_dlp as youtube_dl
import os
import time
import sys
import pyfiglet
from concurrent.futures import ThreadPoolExecutor, as_completed

class NetworkError(Exception):
    pass

class SilentLogger:
    """Custom logger to suppress verbose yt-dlp output."""
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass

def download_single_item(video_url, video_title, directory, ydl_opts, file_format):
    """Download a single item (audio or video) and return its filename or None if failed."""
    os.chdir(directory)
    file_ext = 'mp3' if file_format == 'audio' else 'mp4'
    video_file = f'{video_title}.{file_ext}'

    if os.path.isfile(video_file):
        print(f'{video_file} already exists, skipping...')
        return video_file

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            print(f"Downloading: {video_title} as {file_ext.upper()}...")
            ydl.download([video_url])
            # Verify file exists and is non-zero
            file_path = os.path.join(directory, video_file)
            if os.path.isfile(file_path) and os.path.getsize(file_path) > 0:
                print(f"Completed: {video_file}")
                return video_file
            else:
                print(f"Failed: {video_title} (file missing or empty)")
                return None
    except youtube_dl.utils.DownloadError as e:
        if "network" in str(e).lower() or "connection" in str(e).lower():
            raise NetworkError(f"Network error for '{video_title}': {str(e)}")
        print(f"Failed: {video_title} ({str(e)})")
        return None
    except Exception as e:
        print(f"Failed: {video_title} (Unexpected error: {str(e)})")
        return None

def download_playlist(playlist_url, directory, file_format='audio', max_concurrent=4):
    # Create directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Configure yt-dlp options based on format
    ydl_opts = {
        'outtmpl': '%(title)s.%(ext)s',
        'noplaylist': False,
        'quiet': True,  # Suppress verbose output
        'no_warnings': True,
        'extract_flat': False,
        'playlist_items': '1-3000',
        'ignoreerrors': True,
        'retries': 10,
        'fragment_retries': 10,
        'concurrent_fragments': 4,
        'http_chunk_size': 10485760,
        'logger': SilentLogger(),  # Use custom logger
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
    else:  # video
        ydl_opts.update({
            'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        })

    print("Analyzing playlist URL...")
    time.sleep(1)
    print("Extracting playlist metadata...")
    time.sleep(1)

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)
            video_list = []
            failed_downloads = []

            # Handle single video case
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

            # Playlist case
            print(f"Found playlist: {info.get('title', 'Unknown Playlist')} "
                  f"with {len(info['entries'])} items")

            # Prepare tasks for concurrent download
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

            # Download items concurrently with progress
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
    # Display banner
    result = pyfiglet.figlet_format("YOUTUBE PLAYLIST DOWNLOADER")
    print(result)
    print("\033[1;34m          Created By a Skeeper\033[0m")
    print("\033[2;32m     do not suck on using the application\033[0m")
    print("\033[2;32m            skeeperloyaltie\033[0m")
    print("\033[1;32m   Mail: skeeperloyaltie@pm.me\033[0m")
    print()

    # Check Termux storage setup
    termux_storage = os.path.expanduser("~/storage/shared")
    if not os.path.exists(termux_storage):
        print("Termux storage not found. Please run 'termux-setup-storage' to grant access.")
        print("Exiting...")
        sys.exit(1)

    # Get download format from user
    while True:
        file_format = input("Enter download format (audio/mp3 or video/mp4): ").lower()
        if file_format in ['audio', 'mp3', 'video', 'mp4']:
            file_format = 'audio' if file_format in ['audio', 'mp3'] else 'video'
            break
        print("Invalid input. Please enter 'audio', 'mp3', 'video', or 'mp4'.")

    # Set download directory for Termux
    download_directory = os.path.expanduser("~/storage/shared/Music") if file_format == 'audio' else os.path.expanduser("~/storage/shared/Videos")

    # Get playlist links from user
    links = []
    while len(links) < 5:
        link = input("Enter a YouTube playlist URL (or press Enter to finish): ")
        if not link:
            break
        links.append(link)

    # Display entered links
    if links:
        print("\nYouTube Links entered:")
        for link in links:
            print(f"['{link}']")
        print()

    # Process each playlist
    if links:
        for playlist_url in links:
            print(f"\nProcessing playlist: {playlist_url}")
            downloaded_files, failed_downloads = download_playlist(playlist_url, download_directory, file_format, max_concurrent=4)

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

            time.sleep(2)  # Brief pause between playlists

        print("\nWow - we did it - Thanks for helping!")
    else:
        print("No links provided. Exiting...")
