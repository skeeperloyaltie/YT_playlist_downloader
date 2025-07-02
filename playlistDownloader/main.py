import yt_dlp as youtube_dl
import os
import time
import sys
import pyfiglet

class NetworkError(Exception):
    pass

def download_playlist(playlist_url, directory):
    # Create directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)
    os.chdir(directory)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'noplaylist': False,  # Always process as playlist
        'quiet': False,
        'no_warnings': True,
        'extract_flat': False,  # Fully extract playlist info
        'playlist_items': '1-1000',  # Limit to avoid infinite mixes
        'ignoreerrors': True,  # Skip errors for individual videos
    }

    print("Analyzing playlist URL...")
    time.sleep(1)
    print("Extracting playlist contents...")
    time.sleep(1)

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            # Get playlist info without downloading
            info = ydl.extract_info(playlist_url, download=False)
            video_list = []

            # Check if it's a single video or playlist
            if 'entries' not in info:
                print("Single video detected, treating as a single-item playlist.")
                video_title = info.get('title', 'Unknown Title')
                video_file = f'{video_title}.mp3'
                if os.path.isfile(video_file):
                    print(f'{video_file} already exists, skipping...')
                else:
                    try:
                        ydl.download([playlist_url])
                        video_list.append(video_file)
                    except youtube_dl.utils.DownloadError as e:
                        if "network" in str(e).lower() or "connection" in str(e).lower():
                            raise NetworkError(f"Network error: {str(e)}")
                        print(f"Error downloading single video '{video_title}': {str(e)}. Skipping...")
                return video_list

            # Playlist case
            print(f"Found playlist: {info.get('title', 'Unknown Playlist')} "
                  f"with {len(info['entries'])} songs")
            failed_downloads = []

            for entry in info['entries']:
                if not entry:
                    print("Encountered invalid entry in playlist, skipping...")
                    continue

                video_title = entry.get('title', 'Unknown Title')
                video_url = entry.get('url') or entry.get('webpage_url')
                video_file = f'{video_title}.mp3'

                if os.path.isfile(video_file):
                    print(f'{video_file} already exists, skipping...')
                    video_list.append(video_file)
                    continue

                try:
                    print(f"Downloading: {video_title}")
                    ydl.download([video_url])
                    video_list.append(video_file)
                except youtube_dl.utils.DownloadError as e:
                    if "network" in str(e).lower() or "connection" in str(e).lower():
                        raise NetworkError(f"Network error for '{video_title}': {str(e)}")
                    print(f"Error downloading '{video_title}': {str(e)}. Skipping...")
                    failed_downloads.append(video_title)
                except Exception as e:
                    print(f"Unexpected error for '{video_title}': {str(e)}. Skipping...")
                    failed_downloads.append(video_title)

            if failed_downloads:
                print("\nFailed to download the following songs:")
                for title in failed_downloads:
                    print(f"- {title}")
            print(f"\nSuccessfully downloaded {len(video_list)}/{len(info['entries'])} songs!")
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
    download_directory = os.path.expanduser("~/Music/")

    # Process each playlist
    if links:
        for playlist_url in links:
            print(f"\nProcessing playlist: {playlist_url}")
            downloaded_files = download_playlist(playlist_url, download_directory)
            
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
