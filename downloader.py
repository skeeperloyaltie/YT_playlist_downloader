from pytube import Playlist
import os 

def download_playlist(playlist_url, directory):
    # Create a Playlist object
    playlist = Playlist(playlist_url)

    # Create the directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Change to the specified directory
    os.chdir(directory)

    video_list = []

    for video in playlist.videos:
        try:
            video.streams.filter(only_audio=True, file_extension='mp4').first().download()
            video_list.append(video.title)
        except Exception as e:
            print(f"Error downloading {video.title}: {str(e)}")

    print('All songs in the playlist have been downloaded.')
    return video_list

if __name__ == '__main__':
    playlist_url = input('Enter the URL of the YouTube playlist: ')
    directory = input('Enter the directory to save the downloaded files: ')

    downloaded_videos = download_playlist(playlist_url, directory)

    print(f'The following videos have been downloaded and saved in {directory}:')
    for video_title in downloaded_videos:
        print(video_title)
