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
        'noplaylist': False,
        'quiet': False,
        'no_warnings': True,
    }

    print("Decoding playlist...")
    time.sleep(1)
    print("This might take a few seconds!")
    time.sleep(1)

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            playlist = ydl.extract_info(playlist_url, download=True)
            video_list = []
            
            if 'entries' not in playlist:
                # Handle single video case
                video_title = playlist['title']
                video_file = f'{video_title}.mp3'
                video_list.append(video_file)
            else:
                # Handle playlist case
                for entry in playlist['entries']:
                    if entry:
                        video_title = entry['title']
                        video_file = f'{video_title}.mp3'
                        video_list.append(video_file)
                        if os.path.isfile(video_file):
                            print(f'{video_title}.mp3 already exists, skipping...')
                            continue

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
