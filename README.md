# YouTube Playlist & Mix Downloader

[![CI](https://github.com/skeeperloyaltie/YT_playlist_downloader/actions/workflows/ci.yml/badge.svg)](https://github.com/skeeperloyaltie/YT_playlist_downloader/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Termux Ready](https://img.shields.io/badge/Termux-Supported-brightgreen.svg)](https://termux.dev/)

A fast, multithreaded YouTube playlist and dynamic mix downloader that extracts high-quality audio and saves tracks directly to your device's music library as MP3s.

Supports **Android (Termux)**, **Windows**, **macOS**, and **Linux**.

---

## ⚡ Quick Start: 1-Line Termux / Linux Install

In **Termux** (or any Linux terminal), simply paste and run:

```bash
curl -sSL https://raw.githubusercontent.com/skeeperloyaltie/YT_playlist_downloader/main/install.sh | bash
```

This installs Python, FFmpeg, configures shared storage, installs the package, and creates a global `ytdl` command.

---

## ✨ Features

- **YouTube Mixes (Dynamic Radio)**: Extracts dynamic YouTube mixes (e.g. `list=RD...` or `list=UL...`) by automatically preserving anchor video context.
- **Saved Playlists**: Full support for standard public, unlisted, and user-saved playlists (`list=PL...`, `list=OLAK...`).
- **Private Playlists (Liked Videos / Watch Later)**: Seamless cookie authentication (`list=LL`, `list=WL`) via `--browser chrome/edge/firefox` or `cookies.txt`, with graceful fallback to download the seed song if cookies are not provided.
- **Automatic Scoped Storage Routing (Termux/Android)**: Intercepts scoped media sandboxes (`Android/media/com.termux/`) and routes tracks directly into your phone's accessible shared `~/storage/shared/Music/` folder.
- **WebM to MP3 Transcoding & Auto-Recovery**: Automatically detects FFmpeg to transcode 160kbps Opus streams to 192kbps MP3s. Scans and converts existing `.webm` files and cleans up redundant duplicates.
- **Batch Converter (`--convert`)**: Quickly transcode all existing `.webm` files in your music library to `.mp3` with one command.
- **High-Speed Concurrent Downloads**: Multi-threaded downloads powered by `ThreadPoolExecutor`.
- **Deduplication & Resume**: Records downloaded tracks in `.download_archive.txt` so re-runs complete in seconds.
- **Reusable Python API**: Clean module structure with exports ready for integration into FastAPI, Flask, Django, or desktop/mobile apps.

---

## 📦 Installation & Setup

### Option 1: One-Line Script (Termux / Linux)
```bash
curl -sSL https://raw.githubusercontent.com/skeeperloyaltie/YT_playlist_downloader/main/install.sh | bash
```

### Option 2: Standard Pip Install
```bash
git clone https://github.com/skeeperloyaltie/YT_playlist_downloader.git
cd YT_playlist_downloader
pip install -r requirements.txt
pip install -e .
```

### FFmpeg Requirement (For MP3 Conversion)
YouTube serves audio natively in Opus/WebM and AAC/M4A. FFmpeg is required to convert streams to MP3:
- **Android / Termux**: `pkg install ffmpeg`
- **Windows**: `winget install Gyan.FFmpeg`
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

---

## 🚀 Usage

### 1. Interactive Mode
Run without arguments to enter links interactively:
```bash
ytdl
# or: python playlistDownloader/main.py
```

### 2. CLI Command Examples

```bash
# Download a dynamic YouTube Mix (Radio)
ytdl "https://www.youtube.com/watch?v=-8OsZxDZCgg&list=RD-8OsZxDZCgg&start_radio=1"

# Download a standard saved playlist
ytdl "https://www.youtube.com/playlist?list=PLrAlbmPo5Ymp30Kq122r4R6b_R4sD2qVz"

# Download Liked Videos (list=LL) using browser cookies
ytdl "https://www.youtube.com/watch?v=65A7_eNDcks&list=LL" --browser chrome

# Convert all existing .webm files in your music directory to .mp3
ytdl --convert

# Custom output directory and concurrency
ytdl "<URL>" --dir "~/Music/MyPlaylist" --concurrent 6 --mix-limit 100
```

### CLI Options

| Flag | Default | Description |
|---|---|---|
| `-d`, `--dir` | Auto (`~/storage/shared/Music` on Android, `~/Music/` on PC/Mac) | Directory where audio files are saved |
| `-c`, `--concurrent` | `4` | Number of concurrent downloads |
| `-b`, `--browser` | `None` | Browser to read YouTube login cookies from (`chrome`, `edge`, `firefox`, `brave`) |
| `--cookies` | `None` | Path to a `cookies.txt` file for private playlists (`list=LL`) |
| `-m`, `--mix-limit` | `50` | Maximum songs to extract for dynamic/infinite YouTube Mixes |
| `--convert` | `False` | Convert all existing `.webm` files in the directory to `.mp3` and exit |
| `--ffmpeg-location` | `None` | Custom path to the FFmpeg executable or binary directory |

---

## 🐍 Python Package / Library Usage

You can import this project directly as a Python library:

```python
import playlistDownloader as pld

# 1. Inspect environment & storage target
env = pld.detect_environment()
music_dir = pld.get_default_download_directory()

# 2. Convert existing WebM files to MP3
pld.convert_existing_webm(directory=music_dir)

# 3. Download playlist programmatically
downloaded = pld.download_playlist(
    playlist_url="https://www.youtube.com/watch?v=-8OsZxDZCgg&list=RD-8OsZxDZCgg",
    directory=music_dir,
    max_concurrent=4,
    max_mix_songs=50
)
print("Downloaded files:", downloaded)
```

---

## 🤝 Contributing

Contributions are welcome! Please check out [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on code standards, local setup, and testing.

To run the automated test suite locally:
```bash
python -m unittest discover tests/
```

---

## ☕ Support & Donations (M-Pesa)

If you find this tool helpful and want to support ongoing maintenance and feature development, consider sending a tip:

- **M-Pesa (Kenya & Global)**: `0716642889`
- **Name**: Godfrey Gudah (Skeeper Loyaltie)
- **Contact**: `skeeperloyaltie@pm.me`

---

## 📄 License
This project is licensed under the [MIT License](LICENSE).
