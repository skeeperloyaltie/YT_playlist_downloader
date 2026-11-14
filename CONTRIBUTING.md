# Contributing to YouTube Playlist & Mix Downloader

Thank you for your interest in contributing to **YouTube Playlist & Mix Downloader**! We welcome all contributions, whether it's reporting bugs, improving documentation, adding new features, or optimizing performance across Android (Termux), Windows, macOS, and Linux.

---

## Code of Conduct
Please be respectful and constructive in all discussions, issues, and pull requests.

---

## How to Contribute

### 1. Reporting Bugs
- Check the [Issues](../../issues) tab to see if the bug has already been reported.
- If not, open a new issue using the **Bug Report** template.
- Include:
  - Your Operating System & Environment (e.g., Windows 11, Termux on Android 14, Ubuntu 24.04).
  - Python version (`python3 --version`).
  - `yt-dlp` version (`python3 -c "import yt_dlp; print(yt_dlp.__version__)"`).
  - Terminal output and exact error traceback.
  - An example URL that reproduces the issue (if not private).

### 2. Suggesting Enhancements
- Open an issue using the **Feature Request** template.
- Clearly describe the problem you want to solve and your proposed solution.

### 3. Pull Requests (PRs)
1. **Fork** the repository and clone your fork:
   ```bash
   git clone https://github.com/<your-username>/YT_playlist_downloader.git
   cd YT_playlist_downloader
   ```
2. **Create a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. **Install dependencies and test tools**:
   ```bash
   pip install -r requirements.txt
   pip install pytest flake8 build
   ```
4. **Create a feature branch**:
   ```bash
   git checkout -b feature/my-cool-feature
   ```
5. **Run tests**:
   Ensure all automated unit tests pass before submitting your PR:
   ```bash
   python -m unittest discover tests/
   ```
6. **Commit & Push**:
   Write clear, descriptive commit messages:
   ```bash
   git commit -m "feat: add support for custom bitrate selection"
   git push origin feature/my-cool-feature
   ```
7. **Open a Pull Request**:
   Submit your PR targeting the `main` branch. Fill out the PR template with context on what changed.

---

## Coding Standards
- Target Python 3.9+ compatibility.
- Ensure cross-platform compatibility (Windows, macOS, Linux, and Android/Termux).
- Avoid hardcoding OS-specific file paths (`/` vs `\`). Always use `os.path.join()` or `pathlib`.
- Keep thread-safety in mind: worker functions running under `ThreadPoolExecutor` must not mutate global process directories or shared state without locks.

---

## Financial Support & Tips
If this project helped you or your workflow, support ongoing development via M-Pesa:
- **M-Pesa**: `0716642889`
