# Download each song in a playlist from youtube and save it to a folder
import os 
import sys
from pytube import Playlist
import youtube_dl

# get all the videos in a playlist and store the url's in a list
def get_playlist_videos(playlist_url):
    playlist = Playlist(playlist_url)
    video_urls = playlist.video_urls
    # print the number of videos in the playlist
    print("Number of videos in the playlist: " + str(len(video_urls)))
    return video_urls

def download_songs(song_url, folder_name):
    if not os.path.exists(folder_name):
            os.makedirs(folder_name)
            
    ydl_opts = {
            'format': 'best',
            'outtmpl': folder_name + '/%(title)s.%(ext)s'
        }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([song_url])
        
            
# using youtube_dl download all the videos in  the list to a folder
def download_videos(video_urls, folder_name):
    if not os.path.exists(folder_name):
            os.makedirs(folder_name)
    for url in video_urls:
        ydl_opts = {
            'format': 'best',
            'outtmpl': folder_name + '/%(title)s.%(ext)s'
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
                        
# # use youtube_dl to convert the videos to mp3
# def convert_to_mp3(folder_name):
#     # use youtube_dl to convert the videos to mp3
#     convert_to_mp3(folder_name)
#     # get the list of mp3 files in the folder
#     mp3_files = os.listdir(folder_name)
#     # use youtube_dl to convert the mp3 files to mp3
            
#     for mp3_file in mp3_files:
#         try:
#             ydl_opts = {
#                 'format': 'bestaudio/best',
#                 'outtmpl': folder_name + '/%(title)s.%(ext)s',
#                 'postprocessors': [{
#                     'key': 'FFmpegExtractAudio',
#                     'preferredcodec': 'mp3',
#                     'preferredquality': '192',
#                 }],
#             }
#             with youtube_dl.YoutubeDL(ydl_opts) as ydl:
#                 ydl.download([mp3_file])
#         except Exception as e:
#             print(e)
# main function
def main():
    # get the playlist url from the user
    playlist_url = input("Enter the playlist url: ")
        
    # determine if the playlist url is a playlist or a single video
    if playlist_url.find("list=") != -1:
        video_urls = get_playlist_videos(playlist_url)
        
        folder_name = input("Enter the folder name: ")
        # get the list of videos in the playlist
        # video_urls = get_playlist_videos(playlist_url)
        # download the videos to a folder 
        # 
        download_videos(video_urls, folder_name)
        print("Download complete")
        
        
      
       
    elif playlist_url.find("watch?") != -1:
         # get the folder name from the user
          # get the folder name from the user
        folder_name = input("Enter the folder name: ")
        # download the video to a folder
        download_songs(playlist_url, folder_name)
        print("Download complete")
        
        
    else:
        print("Invalid playlist url")
        sys.exit()
        
if __name__ == "__main__":
    main()