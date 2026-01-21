# 📺 Gameel YT Downloader

A robust, resume-capable YouTube downloader built with **Python** and **Tkinter**. This application provides a modern GUI wrapper for `yt-dlp` and `ffmpeg`, offering advanced features like 4K video merging, exact time clipping, and smart file collision detection.

![App Icon](assets/icon.ico)

## ✨ Key Features

* **⏯️ Smart Resume System**: Detects partial downloads (`.part`) and resumes exactly where they left off, even after the app is closed.
* **✂️ Time Clipping**: Download specific segments of a video (e.g., "01:15 to 02:30") without downloading the whole file.
* **🎥 High-Fidelity Quality**: Auto-merges video/audio streams to support **4K (2160p)** and **2K (1440p)** MKV/WebM files.
* **🛡️ Collision Protection**: Uses "Smart Glob" logic to prevent overwriting existing files while ignoring thumbnails.
* **⚙️ Dependency Check**: Automatically detects if `ffmpeg` is missing and alerts the user.

## 📂 Project Structure

This project follows a modular source structure:

```text
GameelYTDownloader/
├── src/           # Source Code
│   ├── main.py    # Entry point
│   ├── logic.py   # Download management & threading
│   ├── utils.py   # Formatting & helpers
│   └── config.py  # Constants
├── dist/          # Compiled Executable (in Releases)
└── assets/        # Icons and Images
```

## 🚀 Installation & Usage

### For Users (Run the App)

1. Go to the Releases page of this repository.
2. Download the `.zip` file.
3. Extract it and run `gameelytdownloader.exe`.

Note: FFmpeg is included in the download folder, so no extra installation is needed.

### For Developers (Run from Source)

If you want to modify the code or run it with Python:

1. Clone the repository:

```bash
git clone https://github.com/gameelaj/GameelYTDownloader.git
cd GameelYTDownloader
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the application (source lives in `src`):

```bash
python src/main.py
```

## 🛠️ Built With

* Python 3.10+
* Tkinter (Native GUI)
* yt-dlp (Core download engine)
* FFmpeg (Media merging and conversion)
* PyInstaller (Executable compilation)

## 📄 License

Distributed under the MIT License. See LICENSE for more information.