# config.py

# ... (Window Settings, Colors, Fonts remain the same) ...
WINDOW_TITLE = "YouTube Downloader Ultimate"
WINDOW_SIZE = "600x800"

COLOR_BG_MAIN = "#f0f0f0"
COLOR_BTN_START = "#4CAF50"
COLOR_BTN_STOP = "#FF9800"
COLOR_BTN_CANCEL = "#F44336"
COLOR_TEXT_PRIMARY = "#333333"
COLOR_TEXT_SUCCESS = "green"
COLOR_TEXT_ERROR = "red"

FONT_MAIN = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_HEADER = ("Segoe UI", 12, "bold")
FONT_MONO = ("Consolas", 9)

# --- CHANGED: Default Quality ---
DEFAULT_QUALITY = "1080p (MP4 - Fast)" 

# --- Feature Options ---
AUDIO_FORMATS = ["MP3", "M4A", "WAV", "FLAC"]

# ... (POWER_ARGS remain the same) ...
POWER_ARGS = {
    "🚫 Remove Sponsors (SponsorBlock)": {
        "sponsorblock_remove": "sponsor,selfpromo,interaction,intro,outro,music_offtopic",
        "force_keyframes_at_cuts": True,
    },
    "🎬 Embed Chapters": {"addchapters": True},
    "🖼️ Save Thumbnail to Disk (.jpg)": {"writethumbnail": True},
    "📝 Save Description to Disk (.txt)": {"writedescription": True},
    "ℹ️ Save Metadata to Disk (.json)": {"writeinfojson": True},
    "🌍 Bypass Region Locks (Geo Bypass)": {"geo_bypass": True},
    "🐌 Limit Download Speed (5 MB/s)": {"ratelimit": "5M"},
    "🔡 Restrict Filenames (ASCII Only)": {"restrictfilenames": True},
    "⚠️ Ignore Errors (Skip Unavailable)": {"ignoreerrors": True},
    "🕒 Use Download Date (No Mod Time)": {"updatetime": False},
}