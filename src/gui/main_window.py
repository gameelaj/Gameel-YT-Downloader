import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import requests
from PIL import Image, ImageTk
from io import BytesIO
import threading

# Imports from root
import config
import utils
from logic import DownloadManager

# Import from our new module
from gui.components import TimeClipper

class YTDLPGui:
    def __init__(self, root):
        self.root = root
        self.logic = DownloadManager()
        
        self.current_image = None 
        self.active_custom_args = [] 
        
        # State Tracking
        self.resume_args = None
        self.is_paused = False

        self.root.title(config.WINDOW_TITLE)
        self.root.geometry("600x800")
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # --- FEATURE 1: FFmpeg Check on Startup ---
        self._check_ffmpeg()
        
        self._build_ui()

    def _check_ffmpeg(self):
        """Warns the user if FFmpeg is missing."""
        if not utils.is_ffmpeg_installed():
            messagebox.showwarning(
                "FFmpeg Missing", 
                "Critical Dependency Missing: FFmpeg.\n\n"
                "Without FFmpeg:\n"
                "- High-Res (1080p+) videos cannot be merged.\n"
                "- Audio conversion (MP3) will fail.\n"
                "- Time clipping will not work.\n\n"
                "Please install FFmpeg or place ffmpeg.exe in this folder."
            )

    def _build_ui(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Section 1: Inputs ---
        input_frame = ttk.LabelFrame(main_frame, text="Video Details", padding="10")
        input_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(input_frame, text="Video URL:", font=config.FONT_BOLD).pack(anchor=tk.W)
        
        url_box = ttk.Frame(input_frame)
        url_box.pack(fill=tk.X, pady=(5, 10))
        
        self.url_entry = ttk.Entry(url_box, width=50, font=config.FONT_MAIN)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Button(url_box, text="Paste", command=self.paste_from_clipboard, bg="#e1f5fe", relief="flat", padx=10).pack(side=tk.LEFT, padx=(5, 0))
        tk.Button(url_box, text="Check", command=self.load_preview, bg="#ddd", relief="flat", padx=10).pack(side=tk.LEFT, padx=(5, 0))

        self.preview_frame = tk.Frame(input_frame, bg="#f0f0f0", height=150)
        self.preview_frame.pack(fill=tk.X, pady=5)
        self.preview_frame.pack_propagate(False)
        self.lbl_thumbnail = tk.Label(self.preview_frame, text="No Preview", bg="#f0f0f0", fg="#888")
        self.lbl_thumbnail.pack(expand=True)
        self.lbl_title = tk.Label(input_frame, text="", font=config.FONT_BOLD, fg="#333", wraplength=500)
        self.lbl_title.pack(pady=(5,0))

        ttk.Label(input_frame, text="Custom Name (Optional):", font=config.FONT_BOLD).pack(anchor=tk.W, pady=(10,0))
        self.name_entry = ttk.Entry(input_frame, width=70, font=config.FONT_MAIN)
        self.name_entry.pack(fill=tk.X, pady=5)

        # --- Section 2: Settings ---
        settings_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 5))
        settings_frame.columnconfigure(1, weight=1)

        ttk.Label(settings_frame, text="Save to:", font=config.FONT_BOLD).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.save_path = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Desktop"))
        ttk.Entry(settings_frame, textvariable=self.save_path).grid(row=0, column=1, sticky="ew", padx=10)
        
        # --- FEATURE 2: Open Folder Button ---
        btn_browse_box = tk.Frame(settings_frame)
        btn_browse_box.grid(row=0, column=2, padx=5)
        
        ttk.Button(btn_browse_box, text="Browse...", command=self.browse_location).pack(side=tk.LEFT)
        # Small folder icon button
        tk.Button(btn_browse_box, text="Open", command=self.open_save_folder, relief="flat", bg="#eee", padx=5).pack(side=tk.LEFT, padx=(5,0))
        # --------------------------------------

        ttk.Label(settings_frame, text="Quality:", font=config.FONT_BOLD).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.quality_var = tk.StringVar(value=config.DEFAULT_QUALITY)
        
        options = ["1080p (MP4 - Fast)", "4K / Best (MKV/WebM)", "720p Limit", "Audio Only"]
        self.quality_menu = ttk.OptionMenu(settings_frame, self.quality_var, options[0], *options, command=self.on_quality_change)
        self.quality_menu.grid(row=1, column=1, sticky="ew", padx=10)

        # --- Advanced Options Toggle ---
        self.show_advanced = tk.BooleanVar(value=False)
        self.btn_adv = ttk.Checkbutton(main_frame, text="Show Advanced Options", variable=self.show_advanced, command=self.toggle_advanced)
        self.btn_adv.pack(anchor=tk.W, pady=(0, 5))

        # --- Advanced Frame ---
        self.adv_frame = ttk.LabelFrame(main_frame, text="Advanced Controls", padding="10")
        self.adv_frame.columnconfigure(1, weight=1)
        self.adv_frame.columnconfigure(3, weight=1)

        # Row 0: Compatibility & Audio
        self.compat_mode = tk.BooleanVar(value=False)
        self.chk_compat = ttk.Checkbutton(self.adv_frame, text="Force Compatibility (H.264)", variable=self.compat_mode)
        self.chk_compat.grid(row=0, column=0, columnspan=2, sticky=tk.W)

        ttk.Label(self.adv_frame, text="Audio Format:").grid(row=0, column=2, sticky=tk.E)
        self.audio_fmt_var = tk.StringVar(value="MP3")
        self.audio_menu = ttk.OptionMenu(self.adv_frame, self.audio_fmt_var, config.AUDIO_FORMATS[0], *config.AUDIO_FORMATS)
        self.audio_menu.grid(row=0, column=3, sticky="ew", padx=5)
        self.audio_menu.configure(state="disabled")

        # --- COMPONENT: Time Clipper ---
        self.clipper = TimeClipper(self.adv_frame, on_change_callback=self.on_clip_change)
        self.clipper.grid(row=1, column=0, columnspan=4, sticky="ew", pady=5)

        # Row 2: Checkboxes
        self.embed_subs = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.adv_frame, text="Embed Subtitles (En)", variable=self.embed_subs).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        self.embed_meta = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.adv_frame, text="Embed Metadata", variable=self.embed_meta).grid(row=2, column=2, columnspan=2, sticky=tk.W, pady=5)
        
        # Row 3: Bitrate & Args
        ttk.Label(self.adv_frame, text="MP3 Bitrate:").grid(row=3, column=0, sticky=tk.W)
        self.bitrate_var = tk.StringVar(value="192")
        bit_opts = ["128", "192", "320"]
        ttk.OptionMenu(self.adv_frame, self.bitrate_var, bit_opts[1], *bit_opts).grid(row=3, column=1, sticky="w", padx=5)

        ttk.Label(self.adv_frame, text="Add Arg:").grid(row=3, column=2, sticky=tk.E)
        self.arg_selection = tk.StringVar()
        arg_keys = list(config.POWER_ARGS.keys())
        self.arg_dropdown = ttk.OptionMenu(self.adv_frame, self.arg_selection, arg_keys[0], *arg_keys)
        self.arg_dropdown.grid(row=3, column=3, sticky="ew", padx=5)
        
        # Row 4: Buttons/Lists
        tk.Button(self.adv_frame, text="+ Add Argument", command=self.add_argument, bg="#ddd", relief="flat", font=("Segoe UI", 8)).grid(row=4, column=3, sticky="ew", padx=5, pady=(5, 0))

        self.arg_listbox = tk.Listbox(self.adv_frame, height=3, font=("Consolas", 8), bg="#f9f9f9", selectmode=tk.SINGLE)
        self.arg_listbox.grid(row=5, column=0, columnspan=4, sticky="ew", pady=5)
        self.arg_listbox.bind('<Double-Button-1>', self.remove_argument)
        
        # --- Progress & Controls ---
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.pack(fill=tk.X, pady=(0, 15))
        self.status_label = ttk.Label(self.progress_frame, text="Ready", font=config.FONT_MONO, foreground="#555")
        self.status_label.pack(anchor=tk.W, pady=(0, 5))
        self.progress = ttk.Progressbar(self.progress_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress.pack(fill=tk.X)

        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        # START BUTTON
        self.btn_start = tk.Button(btn_frame, text="START DOWNLOAD", command=self.start, bg=config.COLOR_BTN_START, fg="white", font=config.FONT_BOLD, relief="flat", pady=8, cursor="hand2")
        self.btn_start.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # PAUSE / RESUME BUTTON
        self.btn_pause = tk.Button(btn_frame, text="PAUSE", command=self.toggle_pause, bg="orange", fg="white", font=config.FONT_MAIN, relief="flat", pady=8, state=tk.DISABLED, width=15)
        self.btn_pause.pack(side=tk.LEFT, padx=5)

        # SAVE PARTIAL BUTTON
        self.btn_save_partial = tk.Button(btn_frame, text="SAVE PARTIAL", command=self.save_partial, bg="#607d8b", fg="white", font=config.FONT_MAIN, relief="flat", pady=8, state=tk.DISABLED, width=15)
        self.btn_save_partial.pack(side=tk.LEFT, padx=5)
        
        # CANCEL / DELETE BUTTON
        self.btn_cancel = tk.Button(btn_frame, text="DELETE", command=self.cancel, bg=config.COLOR_BTN_CANCEL, fg="white", font=config.FONT_MAIN, relief="flat", pady=8, state=tk.DISABLED, width=15)
        self.btn_cancel.pack(side=tk.LEFT, padx=(5, 0))

    # --- FEATURE 2 Helper: Open Folder ---
    def open_save_folder(self):
        path = self.save_path.get()
        if os.path.isdir(path):
            os.startfile(path)
        else:
            messagebox.showerror("Error", "Invalid Directory")
    # -------------------------------------

    def toggle_pause(self):
        if not self.is_paused:
            self.is_paused = True
            # Check for None safety
            if self.logic.active_file_prefix and self.resume_args is not None:
                self.resume_args['custom_name'] = self.logic.active_file_prefix

            self.logic.stop_and_save()
            self._set_button_state("paused")
            self.status_label.config(text="Paused. Press Resume to continue.", foreground="orange")
            
        else:
            if not self.resume_args:
                messagebox.showerror("Error", "Resume data lost. Please restart.")
                return

            self.is_paused = False
            self.logic.restore_partials()
            self._set_button_state("downloading")
            self.status_label.config(text="Resuming...", foreground="blue")
            
            # Resume with is_resume=True
            self.logic.start_download(**self.resume_args, is_resume=True)

    def save_partial(self):
        if self.is_paused:
            self.is_paused = False
            self.resume_args = None
            self._set_button_state("idle")
            self.status_label.config(text="Partial saved.", foreground="orange")
            return
        if not self.logic.is_downloading:
            return
        self.is_paused = False
        self.resume_args = None
        self.btn_pause.config(state=tk.DISABLED)
        self.btn_save_partial.config(state=tk.DISABLED)
        self.btn_cancel.config(state=tk.DISABLED)
        self.status_label.config(text="Stopping and saving partial...", foreground="orange")
        self.logic.stop_and_save()

    def _set_button_state(self, state):
        if state == "downloading":
            self.btn_start.config(state=tk.DISABLED, bg="#cccccc")
            self.btn_pause.config(state=tk.NORMAL, text="PAUSE", bg="orange")
            self.btn_save_partial.config(state=tk.NORMAL)
            self.btn_cancel.config(state=tk.NORMAL, text="DELETE")
        elif state == "paused":
            self.btn_start.config(state=tk.DISABLED, bg="#cccccc")
            self.btn_pause.config(state=tk.NORMAL, text="RESUME", bg="green")
            self.btn_save_partial.config(state=tk.NORMAL)
            self.btn_cancel.config(state=tk.NORMAL, text="DELETE")
        elif state == "idle":
            self.btn_start.config(state=tk.NORMAL, bg=config.COLOR_BTN_START)
            self.btn_pause.config(state=tk.DISABLED, text="PAUSE", bg="orange")
            self.btn_save_partial.config(state=tk.DISABLED)
            self.btn_cancel.config(state=tk.DISABLED)

    def on_clip_change(self):
        if "Audio Only" in self.quality_var.get():
            self.chk_compat.configure(state="disabled")
            return
        is_high_res = any(x in self.quality_var.get() for x in ["4K", "2K", "2160p", "1440p"])
        if is_high_res:
            self.chk_compat.configure(state="disabled")
            self.compat_mode.set(False)
            return
        if self.clipper.is_clipping_active():
            if str(self.chk_compat['state']) != 'disabled': 
                self.chk_compat.configure(state="disabled")
                self.compat_mode.set(False)
        else:
            self.chk_compat.configure(state="normal")

    def on_quality_change(self, selection):
        if "Audio Only" in selection:
            self.audio_menu.configure(state="normal")
            self.chk_compat.configure(state="disabled")
        else:
            self.audio_menu.configure(state="disabled")
            self.on_clip_change()

    def set_quality(self, value):
        self.quality_var.set(value)
        self.on_quality_change(value)

    def update_quality_menu(self, resolutions):
        menu = self.quality_menu["menu"]
        menu.delete(0, "end") 
        new_options = []
        for r in resolutions:
            if r == 2160: label = "2160p (4K)"
            elif r == 1440: label = "1440p (2K)"
            elif r == 1080: label = "1080p"
            elif r == 720: label = "720p"
            elif r == 480: label = "480p"
            else: label = f"{r}p"
            new_options.append(label)
        new_options.append("Audio Only")

        for opt in new_options:
            menu.add_command(label=opt, command=lambda value=opt: self.set_quality(value))
        
        if "1080p" in new_options: self.quality_var.set("1080p")
        else: self.quality_var.set(new_options[0])
        self.on_quality_change(self.quality_var.get())

    def add_argument(self):
        selection = self.arg_selection.get()
        if selection and selection not in self.active_custom_args:
            self.active_custom_args.append(selection)
            self.arg_listbox.insert(tk.END, selection)

    def remove_argument(self, event):
        selection = self.arg_listbox.curselection()
        if selection:
            index = selection[0]
            value = self.arg_listbox.get(index)
            self.active_custom_args.remove(value)
            self.arg_listbox.delete(index)

    def browse_location(self):
        d = filedialog.askdirectory()
        if d: self.save_path.set(d)

    def toggle_advanced(self):
        if self.show_advanced.get():
            self.adv_frame.pack(after=self.btn_adv, fill=tk.X, pady=(0, 15))
        else:
            self.adv_frame.pack_forget()

    def paste_from_clipboard(self):
        try:
            content = self.root.clipboard_get().strip()
            if "\n" in content or len(content) > 250: return
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, content)
            self.status_label.config(text="Pasted! Loading preview...", foreground="green")
            self.load_preview()
        except: pass

    def load_preview(self):
        url = self.url_entry.get()
        if not url: return
        self.lbl_thumbnail.config(text="Fetching info...", image="") 
        self.lbl_title.config(text="")
        threading.Thread(target=self._fetch_and_display, args=(url,), daemon=True).start()

    def _fetch_and_display(self, url):
        info = self.logic.fetch_video_info(url)
        if not info:
            self.root.after(0, lambda: self.lbl_thumbnail.config(text="Could not load preview"))
            return
        try:
            response = requests.get(info['thumbnail_url'])
            pil_image = Image.open(BytesIO(response.content))
            base_width = 250
            w_percent = (base_width / float(pil_image.size[0]))
            h_size = int((float(pil_image.size[1]) * float(w_percent)))
            pil_image = pil_image.resize((base_width, h_size), Image.Resampling.LANCZOS)
            tk_image = ImageTk.PhotoImage(pil_image)

            def update_ui():
                self.lbl_thumbnail.config(image=tk_image, text="")
                self.current_image = tk_image 
                self.lbl_title.config(text=info['title'])
                if info.get('duration'):
                    self.clipper.set_duration(info['duration'])
                if info.get('resolutions'):
                    self.update_quality_menu(info['resolutions'])
            
            self.root.after(0, update_ui)
        except Exception as e:
            print(f"Image load error: {e}")

    def start(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return
            
        self._set_button_state("downloading")
        self.is_paused = False
        
        custom_arg_dicts = [config.POWER_ARGS[name] for name in self.active_custom_args]
        start_time, end_time = self.clipper.get_times()
        quality_sel = self.quality_var.get()
        is_high_res = any(x in quality_sel for x in ["4K", "2K", "2160p", "1440p"])
        
        if "Audio Only" in quality_sel: final_container = "mp3" 
        elif is_high_res: final_container = "mkv"
        else: final_container = "mp4"

        advanced_opts = {
            'container': final_container,
            'audio_format': self.audio_fmt_var.get(),
            'compatibility_mode': self.compat_mode.get(),
            'audio_bitrate': self.bitrate_var.get(),
            'embed_subs': self.embed_subs.get(),
            'embed_meta': self.embed_meta.get(),
            'custom_args': custom_arg_dicts,
            'time_start': start_time,
            'time_end': end_time,
            'total_duration': self.clipper.video_duration
        }
        
        self.resume_args = {
            'url': url,
            'path': self.save_path.get(),
            'quality': self.quality_var.get(),
            'custom_name': self.name_entry.get().strip(),
            'advanced_opts': advanced_opts,
            'progress_callback': self.update_progress,
            'status_callback': self.update_status,
            'finish_callback': self.on_finish,
            'error_callback': self.on_error
        }
        
        self.logic.start_download(**self.resume_args, is_resume=False)

    def cancel(self): 
        if self.is_paused:
            msg = self.logic.manual_cleanup()
            self.is_paused = False
            self.resume_args = None
            self._set_button_state("idle")
            self.progress['value'] = 0
            self.status_label.config(text="Ready", foreground="#555")
            messagebox.showinfo("Cancelled", "Download cancelled and files deleted.")
        else:
            self.is_paused = False 
            self.resume_args = None
            self.logic.cancel()

    def update_progress(self, downloaded, total, speed, eta):
        if total and total > 0: p = (downloaded / total) * 100
        else: p = 0
        p_text = f"{p:.1f}%" if total > 0 else "..."
        total_str = utils.format_bytes(total) if total else "?"
        stats = f"{p_text} | {utils.format_bytes(downloaded)} of {total_str} | {utils.format_bytes(speed)}/s | ETA: {utils.format_seconds(eta)}"
        self.root.after(0, lambda: self._apply_progress(p, stats))

    def _apply_progress(self, p, stats):
        self.progress['value'] = p
        self.status_label.config(text=stats, foreground=config.COLOR_TEXT_PRIMARY)

    def update_status(self, msg, color):
        self.root.after(0, lambda: self.status_label.config(text=msg, foreground=color))

    def on_finish(self, success: bool):
        def _finish_ui_updates():
            if self.is_paused: return 

            self._set_button_state("idle")
            self.progress['value'] = 100 if success else 0
            
            if success:
                self.status_label.config(text="Download Complete!", foreground=config.COLOR_TEXT_SUCCESS)
                
                # --- AUTO OPEN FOLDER OPTION? ---
                # Uncomment next line if you want it to open automatically
                # self.open_save_folder()
                
                messagebox.showinfo("Success", "Download Finished.")
                self.name_entry.delete(0, tk.END)
                self.clipper.reset() 
            else:
                status_text = self.status_label.cget("text")
                if "Cancelled" in status_text:
                     messagebox.showinfo("Cancelled", "Download cancelled and files deleted.")
                     self.status_label.config(text="Ready", foreground="#555")

        self.root.after(0, _finish_ui_updates)

    def on_error(self, err_msg):
        def _error_ui_updates():
            self.is_paused = False
            self._set_button_state("idle")
            self.status_label.config(text="Error occurred", foreground=config.COLOR_TEXT_ERROR)
            messagebox.showerror("Error", err_msg)
        self.root.after(0, _error_ui_updates)
