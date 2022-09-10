# Download each song in a playlist from youtube and save it to a folder
from lib2to3.pytree import convert
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
                        
# use youtube_dl to convert the videos to mp3
def convert_to_mp3(folder_name):
    # get the list of mp3 files in the folder
    mp3_files = os.listdir(folder_name)
    # use youtube_dl to convert the mp3 files to mp3
    sys.setrecursionlimit(1500)
    for mp3_file in mp3_files:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': folder_name + '/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([mp3_file])
    
# main function
def main():
    # get the playlist url from the user
    p = """\t   ########################################################### 
           ###########################################################
           ##              YOUTUBE PLAYLIST DOWNLOADER              ##
           ##                                                       ##
           ##          Made with Love by Skeeper Loyaltie           ##
           ##                                                       ##
           ##                    bugs dont bite                     ##
           ##                                                       ##
           ##                      Contribute                       ##
           ###########################################################
           ###########################################################
        
        Menu: 
         Welcome to Youtube Playlist Downloader
        1. Download Mp3: 
        2. Download Mp4: 
        3. Exit:
        
    
        """
    print(p)
    choice = int(input("\t Enter an option: "))
    if choice == 1:
        playlist_url = input("Enter the playlist url: ")
        
        # determine if the playlist url is a playlist or a single video
        if playlist_url.find("list=") != -1:
            video_urls = get_playlist_videos(playlist_url)
            folder_name = input("Enter the folder name: ")
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
                download_videos(video_urls, folder_name)
            else:
                print('Directory null.')
            
            print("Download complete")
            
            # convert the mp4 to mp3
            # convert_to_mp3(folder_name)       
        
        elif playlist_url.find("watch?") != -1:
            # get the folder name from the user
            folder_name = input("Enter the folder name: ")
            # download the video to a folder
            download_songs(playlist_url, folder_name)
            print("Download complete")
            
            # convert_to_mp3(folder_name)
            
            
        else:
            print("Invalid playlist url")
            sys.exit()
        
if __name__ == "__main__":
    main()