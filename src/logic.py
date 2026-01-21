import yt_dlp
from yt_dlp.utils import download_range_func
import threading
import os
import time
import glob
from utils import get_quality_opts, parse_time_to_seconds

class DownloadManager:
    def __init__(self):
        self.abort_action = None
        self.is_downloading = False
        self.active_file_prefix = None
        self.active_dir = None

    def fetch_video_info(self, url):
        opts = {'quiet': True, 'skip_download': True, 'noplaylist': True}
        try:
            with yt_dlp.YoutubeDL(params=opts) as ydl: # type: ignore
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats') or []
                resolutions = set()
                for f in formats:
                    if f.get('vcodec') != 'none' and f.get('height'):
                        resolutions.add(f['height'])
                sorted_res = sorted(list(resolutions), reverse=True)
                return {
                    'title': info.get('title', 'Unknown Title'),
                    'thumbnail_url': info.get('thumbnail', None),
                    'duration': info.get('duration', 0),
                    'resolutions': sorted_res
                }
        except Exception as e:
            print(f"Metadata fetch error: {e}")
            return None

    def start_download(self, url, path, quality, custom_name, advanced_opts,
                       progress_callback, status_callback, finish_callback, error_callback, is_resume=False):
        self.abort_action = None
        self.is_downloading = True

        t = threading.Thread(target=self._run_process, 
                             args=(url, path, quality, custom_name, advanced_opts,
                                   progress_callback, status_callback, finish_callback, error_callback, is_resume))
        t.start()

    def cancel(self): self.abort_action = 'cancel'
    def stop_and_save(self): self.abort_action = 'stop_save'
    
    def manual_cleanup(self):
        self.abort_action = 'cancel'
        return self._handle_cleanup_and_exit()

    def restore_partials(self):
        if not self.active_dir or not self.active_file_prefix: return
        search_pattern = os.path.join(self.active_dir, f"{self.active_file_prefix}*")
        found_files = glob.glob(search_pattern)
        for f in found_files:
            # Skip metadata/thumbs, only touch video parts
            if f.lower().endswith(('.part', '.ytdl', '.info.json', '.webp', '.jpg', '.png', '.description')): continue
            
            part_name = f + ".part"
            if not os.path.exists(part_name):
                try: os.rename(f, part_name)
                except: pass

    def _get_unique_filename(self, path, base_name, ext, is_resume=False):
        """
        Determines final filename.
        Resume: Returns base_name (No checks, trusts the saved name).
        Start:  Loops (1, 2, 3...) using SMART GLOB to find empty slots.
                It considers a slot 'taken' if ANY video file exists,
                but ignores .webp/.json files.
        """
        if is_resume: return base_name

        def is_taken(candidate_name):
            # 1. PARANOID GLOB SEARCH
            # Find ANY file that starts with "candidate_name."
            pattern = os.path.join(path, f"{candidate_name}.*")
            matches = glob.glob(pattern)
            
            # 2. FILTER RESULTS
            for f in matches:
                # If we find a file, check its extension
                lower_f = f.lower()
                
                # IGNORE these extensions (Metadata/Thumbs are NOT collisions)
                if lower_f.endswith(('.webp', '.jpg', '.png', '.description', '.info.json', '.txt')):
                    continue
                
                # If it's NOT in the ignore list, it's a Video/Part/Temp file.
                # This counts as a collision!
                return True
            
            return False

        # --- LOOP LOGIC ---
        # 1. Try Base Name
        if not is_taken(base_name): return base_name

        # 2. Loop until we find a "Safe" slot
        counter = 1
        while True:
            new_name = f"{base_name} ({counter})"
            if not is_taken(new_name): return new_name
            counter += 1

    def _run_process(self, url, path, quality, custom_name, advanced_opts,
                     progress_callback, status_callback, finish_callback, error_callback, is_resume):
        
        def hook(d):
            if self.abort_action: raise Exception("ABORT_SIGNAL")
            if d['status'] == 'downloading':
                progress_callback(d.get('downloaded_bytes', 0), d.get('total_bytes') or d.get('total_bytes_estimate') or 0, d.get('speed', 0), d.get('eta', 0))
            elif d['status'] == 'finished':
                status_callback("Download 100%. Processing & Converting...", "blue")

        try:
            target_ext = advanced_opts.get('container', 'mp4')
            if "Audio Only" in quality: target_ext = "mp3"

            if custom_name:
                final_name = self._get_unique_filename(path, custom_name, target_ext, is_resume)
            else:
                status_callback("Fetching title...", "black")
                info = self.fetch_video_info(url)
                if info:
                    safe_title = info['title'].replace('/', '_').replace('\\', '_').replace(':', '-')
                    final_name = self._get_unique_filename(path, safe_title, target_ext, is_resume)
                else:
                    final_name = "%(title)s"
            
            self.active_dir = path
            self.active_file_prefix = final_name 

            opts = {
                'outtmpl': f'{path}/{final_name}.%(ext)s',
                'noplaylist': True,
                'progress_hooks': [hook],
                'addmetadata': advanced_opts.get('embed_meta', False),
                'writethumbnail': advanced_opts.get('embed_meta', False),
            }

            s_sec = parse_time_to_seconds(advanced_opts.get('time_start'))
            e_sec = parse_time_to_seconds(advanced_opts.get('time_end'))
            total_dur = advanced_opts.get('total_duration', 0)
            is_start_zero = (s_sec is None or s_sec < 1)
            is_end_full = (e_sec is None or (total_dur > 0 and e_sec >= total_dur - 1))
            is_clipping = not (is_start_zero and is_end_full) and (s_sec is not None or e_sec is not None)

            if is_clipping:
                opts['download_ranges'] = download_range_func([], [(s_sec, e_sec)]) # type: ignore
                opts['force_keyframes_at_cuts'] = False 

            if "Audio Only" not in quality:
                opts['merge_output_format'] = target_ext

            if 'custom_args' in advanced_opts:
                for arg_dict in advanced_opts['custom_args']: opts.update(arg_dict)
            if advanced_opts.get('embed_subs', False):
                opts.update({'writesubtitles': True, 'subtitleslangs': ['en.*'], 'embedsubtitles': True})

            quality_settings = get_quality_opts(
                selection=quality, 
                audio_format=advanced_opts.get('audio_format', 'MP3'),
                compatibility_mode=advanced_opts.get('compatibility_mode', False)
            )
            opts.update(quality_settings)

            for pp in opts.get('postprocessors', []):
                if pp['key'] == 'FFmpegExtractAudio':
                    pp['preferredquality'] = advanced_opts.get('audio_bitrate', '192')

            status_callback("Starting Download...", "black")
            with yt_dlp.YoutubeDL(params=opts) as ydl: # type: ignore
                ydl.download([url])
            
            finish_callback(success=True)
            
        except Exception as e:
            if self.abort_action is not None or "ABORT_SIGNAL" in str(e):
                msg = self._handle_cleanup_and_exit()
                status_callback(msg, "orange" if self.abort_action == 'stop_save' else "red")
                finish_callback(success=False)
            else:
                error_callback(str(e))
        finally:
            self.is_downloading = False

    def _handle_cleanup_and_exit(self):
        if not self.active_dir or not self.active_file_prefix: return "Cancelled."
        time.sleep(0.5) 
        search_pattern = os.path.join(self.active_dir, f"{self.active_file_prefix}*")
        action_msg = "Cancelled."
        if self.abort_action == 'stop_save': action_msg = "Stopped. Saved partials."
        
        for attempt in range(6): 
            found_files = glob.glob(search_pattern)
            files_locked = False
            for f in found_files:
                try:
                    # CANCEL: Delete EVERYTHING (Video + Thumbs)
                    if self.abort_action == 'cancel':
                        if os.path.exists(f): os.remove(f)
                    
                    # STOP & SAVE: Protect Video, Delete ONLY junk
                    elif self.abort_action == 'stop_save':
                        if f.endswith('.part'):
                            new_name = f.replace('.part', '')
                            if os.path.exists(new_name): os.remove(new_name)
                            os.rename(f, new_name)
                        
                        # PROTECT these (Ignored extensions)
                        elif f.lower().endswith(('.webp', '.jpg', '.png', '.description', '.info.json')):
                            pass 
                        
                        # DELETE pure junk
                        elif f.endswith('.ytdl'):
                            os.remove(f) 
                except PermissionError: files_locked = True
                except Exception: pass
            if not files_locked: break
            time.sleep(0.5)
        return action_msg