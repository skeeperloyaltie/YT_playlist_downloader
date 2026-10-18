# YouTube Playlist & Mix Downloader

A fast, multithreaded YouTube playlist and dynamic mix downloader that extracts audio and saves tracks directly to your music folder.

---

## Features

- **YouTube Mixes (Dynamic Radio)**: Fully extracts dynamically generated YouTube mixes (such as `list=RD...` or `list=UL...`) by automatically preserving anchor track context.
- **Saved Playlists**: Full support for standard public, unlisted, and user-saved playlists (`list=PL...`, `list=OLAK...`).
- **Private Playlists (Liked Videos / Watch Later)**: Seamless cookie integration (`list=LL`, `list=WL`) using browser cookies (`--browser chrome/edge/firefox`) or `cookies.txt`, with graceful fallback to download the seed song if cookies are not provided.
- **High Speed Concurrent Downloads**: Multi-threaded audio downloads with `ThreadPoolExecutor`.
- **Duplicate Prevention & Resumption**: Checks for existing files and records downloaded songs in `.download_archive.txt` so re-runs complete in seconds.
- **Cross-Platform & Windows Safe**: Filenames with invalid filesystem characters (`:`, `?`, `*`, `\`, `/`, `"`, `<`, `>`, `|`) are safely sanitized.
- **FFmpeg Detection**: Automatically uses FFmpeg to produce 192kbps MP3s when available, or gracefully downloads native high-quality audio (`.m4a`/`.webm`) when FFmpeg is not installed.

---

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **(Recommended) Install FFmpeg for MP3 conversion:**
   - **Windows**: `winget install Gyan.FFmpeg`
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg`

---

## Usage

### Interactive Mode
Run the script without arguments to enter URLs interactively:
```bash
python playlistDownloader/main.py
```

### CLI Mode
Pass URLs directly as command-line arguments:

```bash
# Download a YouTube Mix (unsaved dynamic radio)
python playlistDownloader/main.py "https://www.youtube.com/watch?v=-8OsZxDZCgg&list=RD-8OsZxDZCgg&start_radio=1"

# Download a standard saved playlist
python playlistDownloader/main.py "https://www.youtube.com/playlist?list=PLrAlbmPo5Ymp30Kq122r4R6b_R4sD2qVz"

# Download Liked Videos (list=LL) using browser cookies
python playlistDownloader/main.py "https://www.youtube.com/watch?v=65A7_eNDcks&list=LL" --browser chrome

# Custom destination and concurrency
python playlistDownloader/main.py "<URL>" --dir "D:/Music" --concurrent 6 --mix-limit 100
```

### Options

| Flag | Default | Description |
|---|---|---|
| `-d`, `--dir` | `~/Music/` | Directory where audio files are saved |
| `-c`, `--concurrent` | `4` | Number of concurrent downloads |
| `-b`, `--browser` | `None` | Browser to read YouTube login cookies from (`chrome`, `edge`, `firefox`, `brave`) |
| `--cookies` | `None` | Path to a `cookies.txt` file |
| `-m`, `--mix-limit` | `50` | Maximum songs to extract for dynamic/infinite YouTube Mixes |