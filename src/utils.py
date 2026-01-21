import shutil
import re

def format_bytes(bytes_val):
    if bytes_val is None: return "0 B"
    if bytes_val < 1024: return f"{bytes_val} B"
    elif bytes_val < 1024**2: return f"{bytes_val/1024:.1f} KB"
    elif bytes_val < 1024**3: return f"{bytes_val/1024**2:.1f} MB"
    return f"{bytes_val/1024**3:.2f} GB"

def format_seconds(seconds):
    if seconds is None: return "--:--"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0: return f"{int(h)}:{int(m):02d}:{int(s):02d}"
    return f"{int(m):02d}:{int(s):02d}"

def parse_time_to_seconds(time_str):
    if not time_str or not time_str.strip(): return None
    try:
        parts = list(map(int, time_str.split(':')))
        if len(parts) == 1: return parts[0]
        elif len(parts) == 2: return parts[0] * 60 + parts[1]
        elif len(parts) == 3: return parts[0] * 3600 + parts[1] * 60 + parts[2]
    except: return None
    return None

def get_quality_opts(selection, audio_format="MP3", compatibility_mode=False):
    # 1. Audio Only
    if "Audio Only" in selection:
        codec_map = {"MP3": "mp3", "M4A": "m4a", "WAV": "wav", "FLAC": "flac"}
        codec = codec_map.get(audio_format, "mp3")
        return {
            'format': 'bestaudio/best',
            'keepvideo': False,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': codec,
                'preferredquality': '192',
            }],
        }

    # 2. 4K / Best (Explicit Catch)
    # The Regex below won't catch "4K" because it looks for digits like "2160p".
    if "4K" in selection or "Best" in selection:
        return {'format': 'bestvideo+bestaudio/best'}

    # 3. Compatibility Mode (Force H.264 if requested)
    if compatibility_mode:
        return {'format': 'bestvideo[vcodec^=avc]+bestaudio[acodec^=mp4a]/best[vcodec^=avc]'}

    # 4. Dynamic Resolution Handling (1080p, 720p, 480p...)
    # Looks for "1080p", "720p" in the string
    match = re.search(r'(\d{3,4})p', selection)
    if match:
        height = int(match.group(1))
        # If height > 1080, allow ANY container (MKV/WebM)
        if height > 1080:
            return {'format': f'bestvideo[height={height}]+bestaudio/best[height={height}]'}
        # If height <= 1080, prefer MP4 for compatibility
        else:
            return {'format': f'bestvideo[height={height}][ext=mp4]+bestaudio[ext=m4a]/best[height={height}][ext=mp4]/best[height={height}]'}

    # 5. Fallback Default
    return {'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'}

def is_ffmpeg_installed():
    """Checks if FFmpeg is available in the system path."""
    return shutil.which("ffmpeg") is not None