import yt_dlp as youtube_dl
import os
import time
import sys
import pyfiglet
from concurrent.futures import ThreadPoolExecutor, as_completed

class NetworkError(Exception):
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
            print(f"Downloading: {video_title} as {file_ext.upper()}")
            ydl.download([video_url])
        return video_file
    except youtube_dl.utils.DownloadError as e:
        if "network" in str(e).lower() or "connection" in str(e).lower():
            raise NetworkError(f"Network error for '{video_title}': {str(e)}")
        print(f"Error downloading '{video_title}': {str(e)}. Skipping...")
        return None
    except Exception as e:
        print(f"Unexpected error for '{video_title}': {str(e)}. Skipping...")
        return None

def download_playlist(playlist_url, directory, file_format='audio', max_concurrent=4):
    # Create directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Configure yt-dlp options based on format
    ydl_opts = {
        'outtmpl': '%(title)s.%(ext)s',
        'noplaylist': False,  # Always process as playlist
        'quiet': False,
        'no_warnings': True,
        'extract_flat': False,  # Fully extract playlist info
        'playlist_items': '1-3000',  # Support up to 3000 items
        'ignoreerrors': True,  # Skip errors for individual videos
        'retries': 10,  # Retry on transient network issues
        'fragment_retries': 10,
        'concurrent_fragments': 4,  # Download multiple fragments in parallel
        'http_chunk_size': 10485760,  # 10MB chunks for faster downloads
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
            'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',  # Prioritize 1080p MP4
            'merge_output_format': 'mp4',  # Ensure output is MP4
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',  # Ensure video is in MP4 format
            }],
        })

    print("Analyzing playlist URL...")
    time.sleep(1)
    print("Extracting playlist metadata...")
    time.sleep(1)

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            # Extract metadata once
            info = ydl.extract_info(playlist_url, download=False)
            video_list = []
            failed_downloads = []

            # Handle single video case
            if 'entries' not in info:
                print(f"Single {'video' if file_format == 'video' else 'audio'} detected, treating as a single-item playlist.")
                video_title = info.get('title', 'Unknown Title')
                video_url = info.get('url') or info.get('webpage_url') or playlist_url
                video_file = download_single_item(video_url, video_title, directory, ydl_opts, file_format)
                if video_file:
                    video_list.append(video_file)
                else:
                    failed_downloads.append(video_title)
                return video_list

            # Playlist case
            print(f"Found playlist: {info.get('title', 'Unknown Playlist')} "
                  f"with {len(info['entries'])} items")

            # Prepare tasks for concurrent download
            download_tasks = []
            for entry in info['entries']:
                if not entry:
                    print("Encountered invalid entry in playlist, skipping...")
                    failed_downloads.append("Invalid Entry")
                    continue

                video_title = entry.get('title', 'Unknown Title')
                video_url = entry.get('url') or entry.get('webpage_url')

                if not video_url:
                    print(f"No valid URL for '{video_title}', skipping...")
                    failed_downloads.append(video_title)
                    continue

                download_tasks.append((video_url, video_title))

            # Download items concurrently
            with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
                future_to_title = {
                    executor.submit(download_single_item, url, title, directory, ydl_opts, file_format): title
                    for url, title in download_tasks
                }
                for future in as_completed(future_to_title):
                    title = future_to_title[future]
                    try:
                        video_file = future.result()
                        if video_file:
                            video_list.append(video_file)
                    except NetworkError as e:
                        raise  # Re-raise network errors to abort playlist
                    except Exception as e:
                        print(f"Unexpected error for '{title}': {str(e)}. Skipping...")
                        failed_downloads.append(title)

            if failed_downloads:
                print("\nFailed to download the following items:")
                for title in failed_downloads:
                    print(f"- {title}")
            print(f"\nSuccessfully downloaded {len(video_list)}/{len(info['entries'])} items!")
            return video_list

    except NetworkError as e:
        print(f"Critical network error: {str(e)}. Aborting playlist download.")
        return []
    except Exception as e:
        print(f"Unexpected error processing playlist: {str(e)}. Aborting playlist download.")
        return []

if __name__ == '__main__':
    # Display banner
    result = pyfiglet.figlet_format("YOUTUBE PLAYLIST DOWNLOADER")
    print(result)
    print("\033[1;34m          Created By a Skeeper\033[0m")
    print("\033[2;32m     do not suck on using the application\033[0m")
    print("\033[2;32m            skeeperloyaltie\033[0m")
    print("\033[1;32m   Mail: skeeperloyaltie@pm.me\033[0m")
    print()

    # Get download format from user
    while True:
        file_format = input("Enter download format (audio/mp3 or video/mp4): ").lower()
        if file_format in ['audio', 'mp3', 'video', 'mp4']:
            file_format = 'audio' if file_format in ['audio', 'mp3'] else 'video'
            break
        print("Invalid input. Please enter 'audio', 'mp3', 'video', or 'mp4'.")

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

    # Set download directory
    download_directory = os.path.expanduser("~/Music/") if file_format == 'audio' else os.path.expanduser("~/Videos/")

    # Process each playlist
    if links:
        for playlist_url in links:
            print(f"\nProcessing playlist: {playlist_url}")
            downloaded_files = download_playlist(playlist_url, download_directory, file_format, max_concurrent=4)
            
            if downloaded_files:
                print("\nDownloaded files:")
                for file in downloaded_files:
                    print(f"- {file}")
            else:
                print("No files downloaded for this playlist.")
            
            time.sleep(2)  # Brief pause between playlists

        print("\nWow - we did it - Thanks for helping!")
    else:
        print("No links provided. Exiting...")
