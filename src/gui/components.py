# gui/components.py
import tkinter as tk
from tkinter import ttk
import utils

class TimeClipper(ttk.LabelFrame):
    # --- CHANGED: Add callback parameter ---
    def __init__(self, parent, on_change_callback=None, text="Time Clip"):
        super().__init__(parent, text=text, padding="10")
        self.video_duration = 0
        self.on_change = on_change_callback # Save the function
        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(1, weight=1)

        # Start Controls
        ttk.Label(self, text="Start:").grid(row=0, column=0, padx=5)
        self.entry_start = ttk.Entry(self, width=8)
        self.entry_start.grid(row=0, column=1, sticky="w")
        
        # Bind events
        self.entry_start.bind('<Return>', lambda e: self._sync_slider('start'))
        self.entry_start.bind('<FocusOut>', lambda e: self._sync_slider('start'))
        
        self.scale_start = ttk.Scale(self, from_=0, to=100, command=lambda v: self._sync_text(v, 'start'))
        self.scale_start.grid(row=0, column=2, sticky="ew", padx=10)

        # End Controls
        ttk.Label(self, text="End:").grid(row=1, column=0, padx=5)
        self.entry_end = ttk.Entry(self, width=8)
        self.entry_end.grid(row=1, column=1, sticky="w")
        
        # Bind events
        self.entry_end.bind('<Return>', lambda e: self._sync_slider('end'))
        self.entry_end.bind('<FocusOut>', lambda e: self._sync_slider('end'))

        self.scale_end = ttk.Scale(self, from_=0, to=100, command=lambda v: self._sync_text(v, 'end'))
        self.scale_end.grid(row=1, column=2, sticky="ew", padx=10)

    def set_duration(self, duration_seconds):
        self.video_duration = duration_seconds
        if duration_seconds > 0:
            self.scale_start.configure(to=duration_seconds)
            self.scale_end.configure(to=duration_seconds)
            self.reset()
        else:
            self.entry_start.delete(0, tk.END)
            self.entry_end.delete(0, tk.END)

    def reset(self):
        self.scale_start.set(0)
        self.scale_end.set(self.video_duration)
        self._sync_text(0, 'start')
        self._sync_text(self.video_duration, 'end')

    def get_times(self):
        return self.entry_start.get().strip(), self.entry_end.get().strip()
    
    # --- Helper to check if we are currently clipping ---
    def is_clipping_active(self):
        if self.video_duration == 0: return False
        
        s_txt, e_txt = self.get_times()
        s_sec = utils.parse_time_to_seconds(s_txt) or 0
        e_sec = utils.parse_time_to_seconds(e_txt) or 0
        
        # If Start > 0 OR End < Duration, we are clipping
        # (Tolerance of 1 second for float imprecision)
        start_active = s_sec > 1 
        end_active = e_sec < (self.video_duration - 1)
        
        return start_active or end_active

    # --- Internal Sync Logic ---
    def _sync_text(self, val, which):
        seconds = float(val)
        time_str = utils.format_seconds(int(seconds))
        target_entry = self.entry_start if which == 'start' else self.entry_end
        
        if target_entry.get() != time_str:
            target_entry.delete(0, tk.END)
            target_entry.insert(0, time_str)
            
        # --- TRIGGER THE CALLBACK ---
        if self.on_change: self.on_change()

    def _sync_slider(self, which):
        if self.video_duration == 0: return
        target_entry = self.entry_start if which == 'start' else self.entry_end
        target_scale = self.scale_start if which == 'start' else self.scale_end
        
        try:
            text = target_entry.get()
            sec = utils.parse_time_to_seconds(text)
            if sec is not None:
                target_scale.set(sec)
                # --- TRIGGER THE CALLBACK ---
                if self.on_change: self.on_change()
        except: pass