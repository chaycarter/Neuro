"""
W — Chay Carter's Personal Assistant
Desktop overlay UI: always-on-top floating panel
Carter Sciences / neuro.reccy.dev
"""

import customtkinter as ctk
import tkinter as tk
import queue
from datetime import datetime


# Colour palette — clean dark with neuro purple accent
BG         = "#0A0A0F"
SURFACE    = "#13131F"
SURFACE2   = "#1C1C2E"
ACCENT     = "#7B2FBE"
ACCENT_LT  = "#9D4EDD"
ACCENT_DIM = "#4A1A7A"
TEXT       = "#E8E8F0"
MUTED      = "#5A5A7A"
SUCCESS    = "#00C896"
WARNING    = "#FFB347"
ERROR      = "#FF4757"
CYAN       = "#00D4FF"


class LogWidget(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=BG, **kwargs)
        self.box = ctk.CTkTextbox(
            self, fg_color=SURFACE, text_color=TEXT,
            font=("Courier New", 11), wrap="word", state="disabled",
        )
        self.box.pack(fill="both", expand=True, padx=2, pady=2)

    def append(self, message: str, level: str = "info"):
        colour_map = {
            "info":    TEXT,
            "success": SUCCESS,
            "warning": WARNING,
            "error":   ERROR,
            "agent":   CYAN,
        }
        ts = datetime.now().strftime("%H:%M:%S")
        prefix = {"agent": "W  ", "success": "✓  ", "warning": "!  ", "error": "✗  "}.get(level, "   ")
        line = f"{ts}  {prefix}{message}\n"
        self.box.configure(state="normal")
        self.box.tag_config(level, foreground=colour_map.get(level, TEXT))
        self.box.insert("end", line, level)
        self.box.see("end")
        self.box.configure(state="disabled")

    def clear(self):
        self.box.configure(state="normal")
        self.box.delete("1.0", "end")
        self.box.configure(state="disabled")


class WOverlay(ctk.CTk):
    def __init__(self, task_queue: queue.Queue, result_queue: queue.Queue):
        super().__init__()

        self.task_queue = task_queue
        self.result_queue = result_queue

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title("W")
        self.geometry("440x680+16+50")
        self.configure(fg_color=BG)
        self.attributes("-topmost", True)
        self.resizable(True, True)

        self._build()
        self._poll()

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------
    def _build(self):
        # ── Header ──────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        ctk.CTkLabel(
            hdr, text="W", font=("Arial", 22, "bold"), text_color=ACCENT_LT,
        ).pack(side="left", padx=14, pady=8)

        ctk.CTkLabel(
            hdr, text="Chay's Assistant  ·  Carter Sciences",
            font=("Arial", 10), text_color=MUTED,
        ).pack(side="left")

        # Status indicator
        self._status_dot = ctk.CTkLabel(hdr, text="●", font=("Arial", 13), text_color=MUTED)
        self._status_dot.pack(side="right", padx=12)
        self._status_lbl = ctk.CTkLabel(hdr, text="Ready", font=("Arial", 10), text_color=MUTED)
        self._status_lbl.pack(side="right", padx=2)

        # ── Tab bar ──────────────────────────────────────────────────────
        tabs_frame = ctk.CTkFrame(self, fg_color=SURFACE2, corner_radius=0, height=36)
        tabs_frame.pack(fill="x")
        tabs_frame.pack_propagate(False)

        self._active_tab = tk.StringVar(value="task")
        tab_defs = [("Task", "task"), ("Research", "research"), ("Content", "content"), ("Network", "network"), ("Intel", "intel")]
        self._tab_frames = {}

        for label, key in tab_defs:
            btn = ctk.CTkButton(
                tabs_frame, text=label, font=("Arial", 11),
                fg_color="transparent", hover_color=ACCENT_DIM,
                text_color=MUTED, corner_radius=0, height=36, width=100,
                command=lambda k=key: self._switch_tab(k),
            )
            btn.pack(side="left")
            self._tab_frames[key] = btn

        # ── Content area ─────────────────────────────────────────────────
        self._content = ctk.CTkFrame(self, fg_color=BG)
        self._content.pack(fill="both", expand=True)

        self._pages = {
            "task":     self._build_task_page,
            "research": self._build_research_page,
            "content":  self._build_content_page,
            "network":  self._build_network_page,
            "intel":    self._build_intel_page,
        }
        self._rendered = {}
        self._current_tab = None
        self._switch_tab("task")

    # ------------------------------------------------------------------
    # Tab switching
    # ------------------------------------------------------------------
    def _switch_tab(self, key: str):
        # Hide current
        if self._current_tab and self._current_tab in self._rendered:
            self._rendered[self._current_tab].pack_forget()
        # Dim all tab buttons
        for k, btn in self._tab_frames.items():
            btn.configure(text_color=MUTED, fg_color="transparent")
        # Highlight active
        self._tab_frames[key].configure(text_color=ACCENT_LT, fg_color=ACCENT_DIM)

        # Render if first visit
        if key not in self._rendered:
            frame = ctk.CTkFrame(self._content, fg_color=BG)
            self._pages[key](frame)
            self._rendered[key] = frame

        self._rendered[key].pack(fill="both", expand=True)
        self._current_tab = key

    # ------------------------------------------------------------------
    # Task page
    # ------------------------------------------------------------------
    def _build_task_page(self, parent):
        # Quick action pills — 2 rows
        row1_items = [("Research News", "research_run"), ("Draft Newsletter", "newsletter")]
        row2_items = [("Audit Connections", "audit"), ("Connect Targets", "connect_targets"), ("Find Seniors", "find_seniors")]

        for row_items in (row1_items, row2_items):
            row = ctk.CTkFrame(parent, fg_color=BG)
            row.pack(fill="x", padx=10, pady=(8, 0))
            for label, key in row_items:
                ctk.CTkButton(
                    row, text=label, font=("Arial", 11),
                    fg_color=SURFACE2, hover_color=ACCENT,
                    text_color=TEXT, corner_radius=20, height=28,
                    command=lambda k=key: self._quick(k),
                ).pack(side="left", padx=3, pady=2)

        # Input
        input_frame = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=10)
        input_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            input_frame, text="Tell W what to do",
            font=("Arial", 11), text_color=MUTED,
        ).pack(anchor="w", padx=10, pady=(8, 2))

        self.task_input = ctk.CTkTextbox(
            input_frame, height=72, fg_color=BG,
            text_color=TEXT, font=("Arial", 12), wrap="word",
        )
        self.task_input.pack(fill="x", padx=8, pady=(0, 4))
        self.task_input.bind("<Return>", self._on_enter)

        btn_row = ctk.CTkFrame(input_frame, fg_color=SURFACE)
        btn_row.pack(fill="x", padx=8, pady=(0, 8))

        self.run_btn = ctk.CTkButton(
            btn_row, text="▶  Run", font=("Arial", 12, "bold"),
            fg_color=ACCENT, hover_color=ACCENT_LT, text_color="white",
            corner_radius=8, command=self._submit,
        )
        self.run_btn.pack(side="left", padx=4)

        ctk.CTkButton(
            btn_row, text="■  Stop", font=("Arial", 11),
            fg_color=SURFACE, hover_color=ERROR, text_color=MUTED,
            border_color=MUTED, border_width=1, corner_radius=8,
            command=self._stop,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_row, text="Clear", font=("Arial", 11),
            fg_color=SURFACE, hover_color=SURFACE2, text_color=MUTED,
            corner_radius=8, command=self._clear_log,
        ).pack(side="right", padx=4)

        # Log
        ctk.CTkLabel(
            parent, text="Activity", font=("Arial", 10, "bold"), text_color=MUTED,
        ).pack(anchor="w", padx=14, pady=(4, 0))

        self.log = LogWidget(parent)
        self.log.pack(fill="both", expand=True, padx=10, pady=(2, 10))
        self.log.append("W online. Ready for instructions.", "success")

    # ------------------------------------------------------------------
    # Research page
    # ------------------------------------------------------------------
    def _build_research_page(self, parent):
        ctk.CTkLabel(
            parent, text="Neuro Research", font=("Arial", 13, "bold"), text_color=ACCENT_LT,
        ).pack(anchor="w", padx=14, pady=(14, 2))

        ctk.CTkLabel(
            parent,
            text="Pull the latest papers, news, and company updates\nfrom arXiv, Nature, IEEE, MIT Tech Review, and more.",
            font=("Arial", 11), text_color=MUTED, justify="left",
        ).pack(anchor="w", padx=14, pady=(0, 10))

        # Days selector
        sel_row = ctk.CTkFrame(parent, fg_color=BG)
        sel_row.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(sel_row, text="Look back:", font=("Arial", 11), text_color=MUTED).pack(side="left", padx=6)
        self._days_var = tk.StringVar(value="7")
        for days in ("3", "7", "14"):
            ctk.CTkRadioButton(
                sel_row, text=f"{days}d", variable=self._days_var, value=days,
                font=("Arial", 11), text_color=TEXT,
                fg_color=ACCENT, hover_color=ACCENT_LT,
            ).pack(side="left", padx=6)

        ctk.CTkButton(
            parent, text="▶  Run Research Sweep",
            font=("Arial", 12, "bold"), fg_color=ACCENT, hover_color=ACCENT_LT,
            text_color="white", corner_radius=8, height=36,
            command=lambda: self._quick("research_run"),
        ).pack(padx=14, pady=8, fill="x")

        ctk.CTkButton(
            parent, text="Save Newsletter Draft",
            font=("Arial", 11), fg_color=SURFACE2, hover_color=ACCENT_DIM,
            text_color=TEXT, corner_radius=8, height=32,
            command=lambda: self._quick("newsletter"),
        ).pack(padx=14, pady=4, fill="x")

        ctk.CTkLabel(
            parent, text="Sources monitored:",
            font=("Arial", 10, "bold"), text_color=MUTED,
        ).pack(anchor="w", padx=14, pady=(12, 2))

        sources = [
            "arXiv (cs.NE · q-bio.NC · eess.SP)",
            "Nature Neuroscience · Nature Biotechnology",
            "IEEE Spectrum · MIT Technology Review",
        ]
        for s in sources:
            ctk.CTkLabel(parent, text=f"  · {s}", font=("Arial", 10), text_color=MUTED).pack(anchor="w", padx=14)

    # ------------------------------------------------------------------
    # Network page
    # ------------------------------------------------------------------
    def _build_network_page(self, parent):
        ctk.CTkLabel(
            parent, text="Network Management", font=("Arial", 13, "bold"), text_color=ACCENT_LT,
        ).pack(anchor="w", padx=14, pady=(14, 2))

        ctk.CTkLabel(
            parent,
            text="Audit your connections, find senior targets,\nand manage the master spreadsheet.",
            font=("Arial", 11), text_color=MUTED, justify="left",
        ).pack(anchor="w", padx=14, pady=(0, 10))

        actions = [
            ("Audit connections (score all)", "audit"),
            ("Connect with sheet targets", "connect_targets"),
            ("Find senior followers to connect", "find_seniors"),
            ("Read master spreadsheet summary", "sheet_summary"),
        ]
        for label, key in actions:
            ctk.CTkButton(
                parent, text=label,
                font=("Arial", 11), fg_color=SURFACE2, hover_color=ACCENT,
                text_color=TEXT, corner_radius=8, height=34,
                command=lambda k=key: self._quick(k),
            ).pack(padx=14, pady=4, fill="x")

        ctk.CTkLabel(
            parent, text="Scoring logic:",
            font=("Arial", 10, "bold"), text_color=MUTED,
        ).pack(anchor="w", padx=14, pady=(12, 2))

        criteria = [
            "Prioritise:  founder/C/VP/Director + neurotech company",
            "Keep:        neurotech role or company",
            "Review:      unclear relevance",
            "Remove:      spam / unrelated industry",
        ]
        for c in criteria:
            ctk.CTkLabel(parent, text=f"  {c}", font=("Courier New", 10), text_color=MUTED).pack(anchor="w", padx=14)

    # ------------------------------------------------------------------
    # Content page
    # ------------------------------------------------------------------
    def _build_content_page(self, parent):
        ctk.CTkLabel(
            parent, text="Content Studio", font=("Arial", 13, "bold"), text_color=ACCENT_LT,
        ).pack(anchor="w", padx=14, pady=(14, 2))

        ctk.CTkLabel(
            parent,
            text="Draft content in Chay's voice for Carter Sciences\nand Reccy Neuro across all channels.",
            font=("Arial", 11), text_color=MUTED, justify="left",
        ).pack(anchor="w", padx=14, pady=(0, 10))

        sections = [
            ("LinkedIn", [
                ("Weekly wrap-up post", "li_wrap"),
                ("Reccy Neuro role post", "li_role_post"),
            ]),
            ("Long-form", [
                ("Substack article", "substack_draft"),
                ("Interview article intro", "interview_intro"),
                ("Newsletter edition", "newsletter_ed"),
            ]),
        ]
        for section_title, items in sections:
            ctk.CTkLabel(
                parent, text=section_title,
                font=("Arial", 10, "bold"), text_color=MUTED,
            ).pack(anchor="w", padx=14, pady=(10, 2))
            for label, key in items:
                ctk.CTkButton(
                    parent, text=label,
                    font=("Arial", 11), fg_color=SURFACE2, hover_color=ACCENT,
                    text_color=TEXT, corner_radius=8, height=32,
                    command=lambda k=key: self._quick(k),
                ).pack(padx=14, pady=3, fill="x")

        ctk.CTkLabel(
            parent, text="All drafts saved to data/content_drafts/",
            font=("Arial", 10), text_color=MUTED,
        ).pack(anchor="w", padx=14, pady=(12, 0))

    # ------------------------------------------------------------------
    # Intel page
    # ------------------------------------------------------------------
    def _build_intel_page(self, parent):
        ctk.CTkLabel(
            parent, text="Market Intelligence", font=("Arial", 13, "bold"), text_color=ACCENT_LT,
        ).pack(anchor="w", padx=14, pady=(14, 2))

        ctk.CTkLabel(
            parent,
            text="Reccy Neuro lens: intelligence first.\nFunding, hiring signals, vertical scans.",
            font=("Arial", 11), text_color=MUTED, justify="left",
        ).pack(anchor="w", padx=14, pady=(0, 10))

        intel_actions = [
            ("Weekly neurotech briefing", "weekly_briefing"),
            ("Funding scan (>$5M, last 30 days)", "intel_funding"),
            ("Hiring signals across neurotech", "intel_hiring"),
        ]
        for label, key in intel_actions:
            ctk.CTkButton(
                parent, text=label,
                font=("Arial", 11), fg_color=SURFACE2, hover_color=ACCENT,
                text_color=TEXT, corner_radius=8, height=34,
                command=lambda k=key: self._quick(k),
            ).pack(padx=14, pady=4, fill="x")

        ctk.CTkLabel(
            parent, text="Custom query",
            font=("Arial", 10, "bold"), text_color=MUTED,
        ).pack(anchor="w", padx=14, pady=(12, 2))

        company_row = ctk.CTkFrame(parent, fg_color=BG)
        company_row.pack(fill="x", padx=14, pady=4)

        self._intel_input = ctk.CTkEntry(
            company_row, placeholder_text="Company or vertical name...",
            font=("Arial", 11), fg_color=SURFACE2, text_color=TEXT,
            border_color=MUTED, border_width=1,
        )
        self._intel_input.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            company_row, text="Deep-dive",
            font=("Arial", 11), fg_color=ACCENT, hover_color=ACCENT_LT,
            text_color="white", corner_radius=8, width=90,
            command=self._intel_company,
        ).pack(side="right")

        ctk.CTkLabel(
            parent, text="Verticals tracked:",
            font=("Arial", 10, "bold"), text_color=MUTED,
        ).pack(anchor="w", padx=14, pady=(12, 2))

        verticals = ["Neuromodulation (DBS, SCS, VNS, TMS, tDCS, FUS)",
                     "BCI (implantable, non-invasive, endovascular)",
                     "Neuroimaging (MRI AI, fNIRS, EEG diagnostics)",
                     "Digital Therapeutics / Mental Health",
                     "Wearables & Neurofeedback",
                     "Bioelectronics / Drug-device combos"]
        for v in verticals:
            ctk.CTkLabel(parent, text=f"  · {v}", font=("Arial", 10), text_color=MUTED).pack(anchor="w", padx=14)

    def _intel_company(self):
        company = self._intel_input.get().strip() if hasattr(self, "_intel_input") else ""
        if not company:
            return
        instruction = f"Give me a company deep-dive on: {company}. Use the Reccy Neuro intelligence framework."
        self.task_input.delete("1.0", "end")
        self.task_input.insert("end", instruction)
        self._switch_tab("task")
        self._submit()

    # ------------------------------------------------------------------
    # Quick actions
    # ------------------------------------------------------------------
    def _quick(self, key: str):
        days = getattr(self, "_days_var", None)
        d = days.get() if days else "7"
        prompts = {
            # Research
            "research_run":         f"Run a neurotech research sweep for the last {d} days. Fetch papers and news from all sources.",
            "newsletter":           "Save the latest newsletter draft to file.",
            # Content
            "li_wrap":              "Draft my weekly LinkedIn wrap-up post for Carter Sciences. Ask me what happened this week if you need context.",
            "li_role_post":         "Draft a LinkedIn role post for the Reccy Neuro feed. Ask me which role to highlight.",
            "substack_draft":       "Draft a Substack article for The Neurotech Newsletter. Ask me for the topic and angle.",
            "interview_intro":      "Draft an interview intro for a Carter Sciences article. Ask me who the subject is.",
            "newsletter_ed":        "Draft the bi-weekly newsletter edition. Ask me for the key highlights.",
            # Network
            "audit":                "Audit my LinkedIn connections. Score each one for neurotech relevance and flag who to remove or prioritise.",
            "connect_targets":      "Read the master spreadsheet for target connections with status 'target'. Go through each one and send a personalised connection request.",
            "find_seniors":         "Analyse my LinkedIn followers. Identify senior people (C-level, VP, Director, Founder) at neurotech companies that I should connect with.",
            "sheet_summary":        "Read the master connections spreadsheet and give me a summary of the current status breakdown.",
            # Intel
            "weekly_briefing":      "Give me my weekly neurotech briefing. 5-7 notable things ordered by relevance to Carter Sciences and Reccy Neuro.",
            "intel_funding":        "Scan for neurotech funding rounds above $5M from the last 30 days.",
            "intel_hiring":         "Give me hiring signals across neurotech right now. Who is scaling?",
        }
        instruction = prompts.get(key, key)
        self.task_input.delete("1.0", "end")
        self.task_input.insert("end", instruction)
        self._switch_tab("task")
        self._submit()

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------
    def _on_enter(self, event):
        if not (event.state & 0x1):
            self._submit()
            return "break"

    def _submit(self):
        text = self.task_input.get("1.0", "end").strip()
        if not text:
            return
        self.task_input.delete("1.0", "end")
        self.log.append(f"Task: {text}", "info")
        self._set_running()
        self.task_queue.put({"type": "natural_language", "instruction": text})

    def _stop(self):
        self.task_queue.put({"type": "stop"})
        self._set_idle()
        self.log.append("Stopped.", "warning")

    def _clear_log(self):
        self.log.clear()

    def _set_running(self):
        self.run_btn.configure(state="disabled")
        self._status_dot.configure(text_color=ACCENT_LT)
        self._status_lbl.configure(text="Running...")

    def _set_idle(self):
        self.run_btn.configure(state="normal")
        self._status_dot.configure(text_color=SUCCESS)
        self._status_lbl.configure(text="Ready")

    # ------------------------------------------------------------------
    # Result polling
    # ------------------------------------------------------------------
    def _poll(self):
        try:
            while True:
                r = self.result_queue.get_nowait()
                self.log.append(r.get("message", ""), r.get("level", "info"))
                if r.get("done"):
                    self._set_idle()
        except queue.Empty:
            pass
        self.after(150, self._poll)
