#!/usr/bin/env bash
# ==============================================================================
# YouTube Playlist & Mix Downloader - Automated Termux & Linux Installer
# Author: Skeeper Loyaltie (skeeperloyaltie@pm.me)
# Support / M-Pesa: 0716642889
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "=========================================================="
echo "      YouTube Playlist & Mix Downloader Installer         "
echo "               Created By Skeeper Loyaltie                "
echo "=========================================================="
echo -e "${NC}"

# 1. Detect Environment (Termux vs Linux/macOS)
IS_TERMUX=false
if [ -n "$TERMUX_VERSION" ] || [[ "$PREFIX" == *"com.termux"* ]] || [ -d "/data/data/com.termux" ]; then
    IS_TERMUX=true
fi

if [ "$IS_TERMUX" = true ]; then
    echo -e "${GREEN}[*] Termux environment detected (Android).${NC}"
    echo -e "[*] Updating package repositories and installing dependencies..."
    pkg update -y
    pkg install -y python ffmpeg git

    # Setup shared storage if not already configured
    if [ ! -d "$HOME/storage" ]; then
        echo -e "${YELLOW}[!] Setting up shared storage access...${NC}"
        echo -e "    Please tap 'ALLOW' on the Android permission prompt."
        termux-setup-storage || true
        sleep 2
    fi
else
    echo -e "${GREEN}[*] Standard Linux / Unix environment detected.${NC}"
    if ! command -v python3 &>/dev/null; then
        echo -e "${RED}[!] python3 is required. Please install Python 3 and rerun.${NC}"
        exit 1
    fi
    if ! command -v ffmpeg &>/dev/null; then
        echo -e "${YELLOW}[!] Warning: ffmpeg was not found in PATH.${NC}"
        echo -e "    Please install ffmpeg (e.g. 'sudo apt install ffmpeg' or 'brew install ffmpeg') to enable MP3 conversion."
    fi
fi

# 2. Install / Upgrade Python packages
echo -e "${GREEN}[*] Installing required Python packages (yt-dlp, pyfiglet, setuptools)...${NC}"
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install --upgrade yt-dlp pyfiglet

# 3. Clone or Install Repository
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
if [ -f "$SCRIPT_DIR/setup.py" ]; then
    echo -e "${GREEN}[*] Installing package from local directory: $SCRIPT_DIR${NC}"
    python3 -m pip install --upgrade "$SCRIPT_DIR"
else
    echo -e "${GREEN}[*] Fetching and installing latest package from GitHub...${NC}"
    python3 -m pip install --upgrade git+https://github.com/skeeperloyaltie/YT_playlist_downloader.git
fi

# 4. Create convenient 'ytdl' executable shortcut
BIN_DEST=""
if [ "$IS_TERMUX" = true ]; then
    BIN_DEST="$PREFIX/bin/ytdl"
elif [ -d "$HOME/.local/bin" ] || mkdir -p "$HOME/.local/bin"; then
    BIN_DEST="$HOME/.local/bin/ytdl"
fi

if [ -n "$BIN_DEST" ]; then
    cat << 'EOF' > "$BIN_DEST"
#!/usr/bin/env bash
python3 -m playlistDownloader.main "$@"
EOF
    chmod +x "$BIN_DEST"
    echo -e "${GREEN}[✓] Command shortcut created at:${NC} $BIN_DEST"
fi

echo -e "\n${GREEN}=========================================================="
echo " [✓] Installation Successfully Completed!                "
echo "==========================================================${NC}"
echo -e "You can now run the downloader anywhere by typing:"
echo -e "  ${YELLOW}ytdl${NC}                   (Interactive mode)"
echo -e "  ${YELLOW}ytdl \"<URL>\"${NC}           (Direct playlist or mix URL)"
echo -e "  ${YELLOW}ytdl --convert${NC}         (Convert all existing .webm files to .mp3)"
echo -e ""
echo -e "${BLUE}Support the Project (M-Pesa):${NC}"
echo -e "  Send Tip / Support: ${YELLOW}0716642889${NC}"
echo -e "==========================================================\n"
