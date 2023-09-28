import yt_dlp as youtube_dl
import os
import time
import sys

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
    print(ydl_opts)

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        playlist = ydl.extract_info(playlist_url, download=True)
        video_list = []
        for entry in playlist['entries']:
            video_url = entry['url']
            video_title = entry['title']
            video_file = f'{directory}/{video_title}.mp3'
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

# l = ['https://www.youtube.com/watch?v=ALZHF5UqnU4&list=RDEM_2gyprKLdRLT0QaX-7S2lg&start_radio=1&rv=ZAfAud_M_mg', 'https://www.youtube.com/watch?v=ZAfAud_M_mg&list=RDZAfAud_M_mg&start_radio=1&rv=ZAfAud_M_mg&t=0&ab_channel=HalseyVEVO']
# for i in l:
#     download_playlist(i, 'music')


download_playlist('https://www.youtube.com/watch?v=TJjc94NMmkk&list=RDTJjc94NMmkk&start_radio=1&ab_channel=JessieMurphVEVO', 'music')

# if __name__ == '__main__':
#     if len(sys.argv) != 3:
#         print("Usage: python playlist_downloader.py <url> <directory>")
#         sys.exit(1)

#     url = sys.argv[1]
#     directory = sys.argv[2]

#     downloaded_videos = download_playlist(url, directory)
#     print(f'The following videos have been downloaded and saved in {directory}:')
#     print(downloaded_videos)
