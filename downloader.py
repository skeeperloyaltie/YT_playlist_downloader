import sys
import requests
from bs4 import BeautifulSoup
import pytube

# Function to extract video links
def extract_video_links(playlist_url):
    response = requests.get(playlist_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    links = []
    
    for link in soup.find_all('a', {'class': 'yt-simple-endpoint style-scope ytd-playlist-video-renderer'}):
        video_id = link['href'].split('=')[1]
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        links.append(video_url)
    
    return links

def download_videos(video_links):
    for link in video_links:
        try:
            yt = pytube.YouTube(link)
            stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
            stream.download(output_path='your_download_path')  # Specify your download path here
            print("Downloaded:", yt.title)
        except Exception as e:
            print("Error downloading:", link, e)

if __name__ == "__main__":
    playlist_url = "https://www.youtube.com/watch?v=T8guj_S9tgs&list=RD6u0DGIh3wLA&index=2&ab_channel=ZoeWeesVEVO"
    video_links = extract_video_links(playlist_url)
    print(video_links)
    download_videos(video_links)
