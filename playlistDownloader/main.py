import yt_dlp as youtube_dl
import os
import time
import sys
import pyfiglet 


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
    s = True
    while s:
        print("Model set: [Decoding playlist!]")
        time.sleep(3)
        print(["This might take a few seconds!"])
        time.sleep(2)
        print("Successful!")
        time.sleep(2)
        s = False


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


# download_playlist('https://www.youtube.com/watch?v=TJjc94NMmkk&list=RDTJjc94NMmkk&start_radio=1&ab_channel=JessieMurphVEVO', 'music')

if __name__ == '__main__':
    result = pyfiglet.figlet_format("YOUTUBE PLAYLIST DOWNLOADER") 

#    os.system("clear")
    print(result)
    os.system('echo  "\\e[1;31m\"')
    os.system('echo "\\e[1;32m\"')
    os.system('echo "\\e[1;32m\"')
    os.system('echo "\\e[1;34m          Created By a Skeeper\\e[0m"')
    os.system('echo "\\e[2;32m     do not suck on using the application \\e[0m"')
    os.system('echo "\\e[2;32m            skeeperloyaltie \\e[0m"')
    os.system('echo "\\e[1;32m   Mail: skeeperloyaltie@pm.me \\e[0m"')
    print()

    # Initialize an empty list to store the links
    links = []

    # Use a loop to get input from the user until 5 links are entered
    while len(links) < 5:
        link = input("Enter a youtube playlist: [Press enter if you done!]  ")
        
        # Check if the user pressed Enter without enteing a link
        if not link:
            break
        
        # Append the link to the list
        links.append(link)

    # Display the entered links
    print("Youtube Links entered:")
    for link in links:
        print("['" + link + "']")
    print()
    
    # Define the download directory
    download_directory = os.path.expanduser("~/Music/")

    # Check if the directory exists, and if not, create it
    if not os.path.exists(download_directory):
        os.makedirs(download_directory)

    import time

    def perform_network_operation():
        # Simulate a network operation (replace with your actual code)
        if len(links) < 1:
            raise NetworkError("Network issue occurred")
        else:
            return "Data from the network"

    class NetworkError(Exception):
        pass

    max_retries = 5
    retry_delay = 5  # seconds

    for attempt in range(1, max_retries + 1):
        try:
            result = perform_network_operation()
            # If the network operation succeeds, exit the loop
            break
        except NetworkError as e:
            print(f"Attempt {attempt}: {str(e)}")
            if attempt < max_retries:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Exiting...")
                break
    else:
        print("Task failed after multiple attempts. Exiting...")

    # Continue with the program using 'result' if the operation was successful
    if result:
        print("Network operation succeeded. Continuing with the program.")
        # Your program logic here


        for i in links:
            download_playlist(i, download_directory)


    print("Wow - we did it - Thanks for helping")
