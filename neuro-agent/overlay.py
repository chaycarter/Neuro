"""
Neuro Agent - Desktop Overlay UI
Floating always-on-top panel for Carter Sciences / neuro.reccy.dev
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import scrolledtext
import threading
import queue
import asyncio
from datetime import datetime


# Neuro brand colours
BRAND_BG = "#0D0D0D"
BRAND_SURFACE = "#1A1A2E"
BRAND_ACCENT = "#7B2FBE"
BRAND_ACCENT_LIGHT = "#9D4EDD"
BRAND_TEXT = "#E8E8F0"
BRAND_MUTED = "#6B6B8A"
BRAND_SUCCESS = "#00C896"
BRAND_WARNING = "#FFB347"
BRAND_ERROR = "#FF4757"


class TaskLogWidget(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=BRAND_BG, **kwargs)
        self.log_text = ctk.CTkTextbox(
            self,
            fg_color=BRAND_SURFACE,
            text_color=BRAND_TEXT,
            font=("JetBrains Mono", 11),
            wrap="word",
            state="disabled",
        )
        self.log_text.pack(fill="both", expand=True, padx=4, pady=4)

    def append(self, message: str, level: str = "info"):
        colours = {
            "info": BRAND_TEXT,
            "success": BRAND_SUCCESS,
            "warning": BRAND_WARNING,
            "error": BRAND_ERROR,
            "agent": BRAND_ACCENT_LIGHT,
        }
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {message}\n"
        self.log_text.configure(state="normal")
        self.log_text.tag_config(level, foreground=colours.get(level, BRAND_TEXT))
        self.log_text.insert("end", line, level)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")


class StatusDot(ctk.CTkLabel):
    """Small animated status indicator."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="●", font=("Arial", 12), **kwargs)
        self._idle()

    def _idle(self):
        self.configure(text_color=BRAND_MUTED)

    def working(self):
        self.configure(text_color=BRAND_ACCENT_LIGHT)

    def success(self):
        self.configure(text_color=BRAND_SUCCESS)

    def error(self):
        self.configure(text_color=BRAND_ERROR)


class NeuroOverlay(ctk.CTk):
    def __init__(self, task_queue: queue.Queue, result_queue: queue.Queue):
        super().__init__()

        self.task_queue = task_queue
        self.result_queue = result_queue

        # Window setup
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title("Neuro Agent")
        self.geometry("420x620+20+60")
        self.configure(fg_color=BRAND_BG)
        self.attributes("-topmost", True)  # Always on top
        self.resizable(True, True)

        # Allow transparency drag (borderless feel)
        self.overrideredirect(False)

        self._build_ui()
        self._poll_results()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        # --- Header bar ---
        header = ctk.CTkFrame(self, fg_color=BRAND_SURFACE, corner_radius=0, height=48)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="⬡ NEURO",
            font=("Arial", 15, "bold"),
            text_color=BRAND_ACCENT_LIGHT,
        ).pack(side="left", padx=12, pady=10)

        ctk.CTkLabel(
            header,
            text="neuro.reccy.dev",
            font=("Arial", 10),
            text_color=BRAND_MUTED,
        ).pack(side="left", padx=0, pady=10)

        self.status_dot = StatusDot(header)
        self.status_dot.pack(side="right", padx=12)

        self.status_label = ctk.CTkLabel(
            header,
            text="Ready",
            font=("Arial", 10),
            text_color=BRAND_MUTED,
        )
        self.status_label.pack(side="right", padx=4)

        # --- Quick action pills ---
        pills_frame = ctk.CTkFrame(self, fg_color=BRAND_BG)
        pills_frame.pack(fill="x", padx=10, pady=(8, 0))

        quick_tasks = [
            ("Search Candidates", "search"),
            ("Send Messages", "message"),
            ("Connect", "connect"),
            ("Scrape Profile", "scrape"),
        ]
        for label, task_type in quick_tasks:
            btn = ctk.CTkButton(
                pills_frame,
                text=label,
                font=("Arial", 11),
                fg_color=BRAND_SURFACE,
                hover_color=BRAND_ACCENT,
                text_color=BRAND_TEXT,
                corner_radius=20,
                height=28,
                command=lambda t=task_type: self._quick_action(t),
            )
            btn.pack(side="left", padx=3, pady=4)

        # --- Task input ---
        input_frame = ctk.CTkFrame(self, fg_color=BRAND_SURFACE, corner_radius=10)
        input_frame.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(
            input_frame,
            text="Tell Neuro what to do",
            font=("Arial", 11),
            text_color=BRAND_MUTED,
        ).pack(anchor="w", padx=10, pady=(8, 2))

        self.task_input = ctk.CTkTextbox(
            input_frame,
            height=80,
            fg_color=BRAND_BG,
            text_color=BRAND_TEXT,
            font=("Arial", 12),
            wrap="word",
        )
        self.task_input.pack(fill="x", padx=8, pady=(0, 4))
        self.task_input.bind("<Return>", self._on_enter)

        btn_row = ctk.CTkFrame(input_frame, fg_color=BRAND_SURFACE)
        btn_row.pack(fill="x", padx=8, pady=(0, 8))

        self.run_btn = ctk.CTkButton(
            btn_row,
            text="▶  Run Task",
            font=("Arial", 12, "bold"),
            fg_color=BRAND_ACCENT,
            hover_color=BRAND_ACCENT_LIGHT,
            text_color="white",
            corner_radius=8,
            command=self._submit_task,
        )
        self.run_btn.pack(side="left", padx=4)

        self.stop_btn = ctk.CTkButton(
            btn_row,
            text="■  Stop",
            font=("Arial", 12),
            fg_color=BRAND_SURFACE,
            hover_color=BRAND_ERROR,
            text_color=BRAND_MUTED,
            border_color=BRAND_MUTED,
            border_width=1,
            corner_radius=8,
            command=self._stop_task,
        )
        self.stop_btn.pack(side="left", padx=4)

        # --- Task Log ---
        ctk.CTkLabel(
            self,
            text="Activity Log",
            font=("Arial", 11, "bold"),
            text_color=BRAND_MUTED,
        ).pack(anchor="w", padx=14, pady=(4, 0))

        self.log = TaskLogWidget(self)
        self.log.pack(fill="both", expand=True, padx=10, pady=(2, 10))

        self.log.append("Neuro Agent initialised.", "success")
        self.log.append("Connect your browser and give a task to begin.", "info")

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    def _on_enter(self, event):
        if not event.state & 0x1:  # Shift not held
            self._submit_task()
            return "break"

    def _submit_task(self):
        text = self.task_input.get("1.0", "end").strip()
        if not text:
            return
        self.task_input.delete("1.0", "end")
        self.log.append(f"Task: {text}", "info")
        self._set_running()
        self.task_queue.put({"type": "natural_language", "instruction": text})

    def _quick_action(self, task_type: str):
        prompts = {
            "search": "Search LinkedIn for neurotech candidates with 3+ years experience",
            "message": "Draft and send a personalised connection message to the last viewed LinkedIn profile",
            "connect": "Send a connection request to the last viewed LinkedIn profile",
            "scrape": "Extract the full profile details from the current LinkedIn tab",
        }
        instruction = prompts.get(task_type, task_type)
        self.task_input.delete("1.0", "end")
        self.task_input.insert("end", instruction)
        self._submit_task()

    def _stop_task(self):
        self.task_queue.put({"type": "stop"})
        self._set_idle()
        self.log.append("Task stopped by user.", "warning")

    def _set_running(self):
        self.run_btn.configure(state="disabled")
        self.status_dot.working()
        self.status_label.configure(text="Running...")

    def _set_idle(self):
        self.run_btn.configure(state="normal")
        self.status_dot.success()
        self.status_label.configure(text="Ready")

    # ------------------------------------------------------------------
    # Result polling (checks result_queue every 200ms)
    # ------------------------------------------------------------------
    def _poll_results(self):
        try:
            while True:
                result = self.result_queue.get_nowait()
                level = result.get("level", "info")
                message = result.get("message", "")
                self.log.append(message, level)
                if result.get("done"):
                    self._set_idle()
        except queue.Empty:
            pass
        self.after(200, self._poll_results)

    def post_result(self, message: str, level: str = "info", done: bool = False):
        self.result_queue.put({"message": message, "level": level, "done": done})
