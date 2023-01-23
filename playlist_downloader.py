import youtube_dl
import os
import time

def download_playlist(playlist_url, directory):
    # create directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)
    os.chdir(directory)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': directory + '/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        playlist = ydl.extract_info(playlist_url, download=False)
        video_list = []
        for entry in playlist['entries']:
            video_url = entry['url']
            video_title = entry['title']
            video_file = f'{directory}/{video_title}.mp3'
            # video_file = f'{video_title}.mp3'
            video_list.append(video_file)
            if os.path.isfile(video_file):
                print(f'{video_file} already exists, skipping...')
                continue
            try:
                ydl.download([video_url])
                time.sleep(5)
            except youtube_dl.utils.DownloadError as e:
                if e.exc_info[1].code == 403:
                    print(f'HTTP Error 403: Forbidden, retrying in 10 seconds...')
                    time.sleep(10)
                    ydl.download([video_url])
                else:
                    raise e
            except Exception as e:
                print(f'Error downloading {video_url}. Retrying...')
                time.sleep(10)
                ydl.download([video_url])
    print('All songs in the playlist have been downloaded.')
    return video_list

playlist_url = input("Enter playlist URL: ")
directory = input('Enter directory path: ')
downloaded_videos = download_playlist(playlist_url, directory)
print(f'The following videos have been downloaded and saved in {directory}:')
print(downloaded_videos)
