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
        'playlist_items': '1-1000',  # Limit to avoid infinite mixes, adjust as needed
    }

    print("Analyzing playlist URL...")
    time.sleep(1)
    print("Extracting playlist contents...")
    time.sleep(1)

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            # First, get playlist info without downloading
            info = ydl.extract_info(playlist_url, download=False)
            video_list = []

            # Handle different cases
            if 'entries' not in info:
                # Single video case
                video_title = info['title']
                video_file = f'{video_title}.mp3'
                if not os.path.isfile(video_file):
                    ydl.download([playlist_url])
                video_list.append(video_file)
            else:
                # Playlist/Mix case
                print(f"Found playlist: {info.get('title', 'Unknown Playlist')} "
                      f"with {len(info['entries'])} songs")
                
                for entry in info['entries']:
                    if entry:
                        video_title = entry.get('title', 'Unknown Title')
                        video_file = f'{video_title}.mp3'
                        if os.path.isfile(video_file):
                            print(f'{video_title}.mp3 already exists, skipping...')
                            continue
                        video_list.append(video_file)
                
                # Download the entire playlist at once
                ydl.download([playlist_url])

            print('All songs in the playlist have been downloaded successfully!')
            return video_list

    except youtube_dl.utils.DownloadError as e:
        print(f"Download error: {str(e)}")
        return []
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
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
                print("Failed to download playlist")
            
            time.sleep(2)  # Brief pause between playlists

        print("\nWow - we did it - Thanks for helping!")
    else:
        print("No links provided. Exiting...")
