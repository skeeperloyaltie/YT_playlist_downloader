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
        'outtmpl': '%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'noplaylist':False,
        'retries':10,
        'buffer_size':1024*1024,
        'ignoreerrors':True,
        'max_downloads':1,
        'ratelimit':1024*1024,
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([playlist_url])
        except Exception as e:
            print(f'Error downloading {playlist_url}')
            print(e)
    print('All songs in the playlist have been downloaded.')

playlist_url = input("Enter playlist URL: ")
directory = input('Enter directory path: ')
download_playlist(playlist_url, directory)
