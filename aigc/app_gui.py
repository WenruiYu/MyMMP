# -*- coding: utf-8 -*-
"""
Simple Tkinter GUI for TikTokRewriter.
- Lets you pick TTS file, Caption file, counts, model, streaming, etc.
- Streams the CLI output in real time into the log window.
- Writes TTS outputs to the TTS folder; Caption outputs to the Caption folder (handled by CLI).
"""

from __future__ import annotations
import os
import threading
import queue
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional

from rewriter_core import RewriterConfig, Rewriter

APP_TITLE = "TikTokRewriter"
DEFAULT_MODEL_CHOICES = ["deepseek-chat", "deepseek-reasoner"]

class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("900x640")

        self.proc_thread: Optional[threading.Thread] = None
        self.msg_q: "queue.Queue[tuple[str,str]]" = queue.Queue()
        self.running = False

        self._build_widgets()
        self._poll_queue()

    # -------- UI --------

    def _build_widgets(self) -> None:
        pad = {"padx": 8, "pady": 6}

        # Mode Selection
        mode_frame = ttk.LabelFrame(self, text="Mode")
        mode_frame.pack(fill="x", **pad)
        
        self.use_tts_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(mode_frame, text="Include TTS Rewriting (uncheck for caption-only mode)", 
                       variable=self.use_tts_var, command=self._toggle_tts_input).pack(anchor="w", padx=5, pady=5)

        # Inputs
        top = ttk.LabelFrame(self, text="Inputs")
        top.pack(fill="x", **pad)

        self.tts_var = tk.StringVar()
        self.tts_label = ttk.Label(top, text="TTS file:")
        self.tts_label.grid(row=0, column=0, sticky="w")
        self.tts_entry = ttk.Entry(top, textvariable=self.tts_var, width=80)
        self.tts_entry.grid(row=0, column=1, sticky="we")
        self.tts_button = ttk.Button(top, text="Browse...", command=self._browse_tts)
        self.tts_button.grid(row=0, column=2, sticky="e")

        self.cap_var = tk.StringVar()
        ttk.Label(top, text="Caption file:").grid(row=1, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.cap_var, width=80).grid(row=1, column=1, sticky="we")
        ttk.Button(top, text="Browse...", command=self._browse_caption).grid(row=1, column=2, sticky="e")

        top.columnconfigure(1, weight=1)

        # Options
        opt = ttk.LabelFrame(self, text="Options")
        opt.pack(fill="x", **pad)

        self.num_var = tk.IntVar(value=4)
        self.vpr_var = tk.IntVar(value=1)
        ttk.Label(opt, text="Total variants (-n):").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(opt, from_=1, to=999, textvariable=self.num_var, width=8).grid(row=0, column=1, sticky="w")
        ttk.Label(opt, text="Variants per request:").grid(row=0, column=2, sticky="w")
        ttk.Spinbox(opt, from_=1, to=20, textvariable=self.vpr_var, width=8).grid(row=0, column=3, sticky="w")

        self.model_var = tk.StringVar(value=DEFAULT_MODEL_CHOICES[0])
        ttk.Label(opt, text="Model:").grid(row=1, column=0, sticky="w")
        ttk.Combobox(opt, textvariable=self.model_var, values=DEFAULT_MODEL_CHOICES, width=22).grid(row=1, column=1, sticky="w")

        self.stream_var = tk.BooleanVar(value=True)
        self.no_reasoning_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt, text="Stream", variable=self.stream_var).grid(row=1, column=2, sticky="w")
        ttk.Checkbutton(opt, text="Hide reasoning", variable=self.no_reasoning_var).grid(row=1, column=3, sticky="w")

        self.style_var = tk.StringVar(value="compact")
        ttk.Label(opt, text="Stream style:").grid(row=2, column=0, sticky="w")
        ttk.Combobox(opt, textvariable=self.style_var, values=["compact", "raw"], width=10).grid(row=2, column=1, sticky="w")

        self.max_tokens_var = tk.IntVar(value=3072)
        self.retries_var = tk.IntVar(value=2)
        ttk.Label(opt, text="max_tokens:").grid(row=2, column=2, sticky="w")
        ttk.Spinbox(opt, from_=256, to=8192, increment=256, textvariable=self.max_tokens_var, width=8).grid(row=2, column=3, sticky="w")
        ttk.Label(opt, text="retries:").grid(row=3, column=2, sticky="w")
        ttk.Spinbox(opt, from_=0, to=10, textvariable=self.retries_var, width=8).grid(row=3, column=3, sticky="w")

        self.temp_var = tk.DoubleVar(value=0.8)
        ttk.Label(opt, text="temperature:").grid(row=3, column=0, sticky="w")
        ttk.Spinbox(opt, from_=0.0, to=2.0, increment=0.1, textvariable=self.temp_var, width=8).grid(row=3, column=1, sticky="w")

        self.key_var = tk.StringVar(value=os.environ.get("DEEPSEEK_API_KEY", ""))
        ttk.Label(opt, text="DEEPSEEK_API_KEY (optional override):").grid(row=4, column=0, sticky="w")
        ttk.Entry(opt, textvariable=self.key_var, width=28, show="•").grid(row=4, column=1, sticky="w")

        opt.columnconfigure(1, weight=1)

        # Stream log
        logf = ttk.LabelFrame(self, text="Stream log (optional)")
        logf.pack(fill="x", **pad)
        self.stream_log_var = tk.StringVar()
        ttk.Entry(logf, textvariable=self.stream_log_var, width=80).grid(row=0, column=0, sticky="we")
        ttk.Button(logf, text="Save As...", command=self._browse_stream_log).grid(row=0, column=1, sticky="e")
        logf.columnconfigure(0, weight=1)

        # Controls
        ctrl = ttk.Frame(self)
        ctrl.pack(fill="x", **pad)
        ttk.Button(ctrl, text="Start", command=self._start).pack(side="left")
        ttk.Button(ctrl, text="Stop", command=self._stop).pack(side="left")
        ttk.Button(ctrl, text="Clear Log", command=self._clear_log).pack(side="left")

        # Log box
        log = ttk.LabelFrame(self, text="Run Log")
        log.pack(fill="both", expand=True, **pad)

        self.text = tk.Text(log, wrap="word", height=20)
        self.text.pack(fill="both", expand=True, side="left")
        self.scroll = ttk.Scrollbar(log, command=self.text.yview)
        self.scroll.pack(side="right", fill="y")
        self.text.configure(yscrollcommand=self.scroll.set)
        self.text.tag_configure("err", foreground="#c00")
        self._log_banner()

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status_var, anchor="w").pack(fill="x")

    # -------- helpers --------

    def _log_banner(self) -> None:
        self.text.insert("end", f"{APP_TITLE} — ready.\n")
        self.text.see("end")

    def _append_log(self, s: str, tag: Optional[str] = None) -> None:
        if tag:
            self.text.insert("end", s, tag)
        else:
            self.text.insert("end", s)
        self.text.see("end")

    def _clear_log(self) -> None:
        self.text.delete("1.0", "end")
        self._log_banner()

    def _browse_tts(self) -> None:
        p = filedialog.askopenfilename(
            title="Select TTS .txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if p:
            self.tts_var.set(p)

    def _browse_caption(self) -> None:
        p = filedialog.askopenfilename(
            title="Select Caption .txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if p:
            self.cap_var.set(p)

    def _browse_stream_log(self) -> None:
        p = filedialog.asksaveasfilename(
            title="Save stream log as",
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if p:
            self.stream_log_var.set(p)
    
    def _toggle_tts_input(self) -> None:
        """Enable/disable TTS input fields based on mode selection."""
        if self.use_tts_var.get():
            self.tts_label.config(state="normal")
            self.tts_entry.config(state="normal")
            self.tts_button.config(state="normal")
        else:
            self.tts_label.config(state="disabled")
            self.tts_entry.config(state="readonly")
            self.tts_button.config(state="disabled")
            self.tts_var.set("")  # Clear TTS path when disabled

    # -------- run/stop --------

    def _start(self) -> None:
        if self.running:
            messagebox.showinfo(APP_TITLE, "Already running.")
            return

        use_tts = self.use_tts_var.get()
        tts = self.tts_var.get().strip() if use_tts else None
        cap = self.cap_var.get().strip()
        
        # Validate inputs
        if not cap:
            messagebox.showerror(APP_TITLE, "Please select a Caption file.")
            return
        if use_tts and not tts:
            messagebox.showerror(APP_TITLE, "Please select a TTS file or uncheck 'Include TTS Rewriting'.")
            return
        if not Path(cap).exists():
            messagebox.showerror(APP_TITLE, "Caption file does not exist.")
            return
        if use_tts and tts and not Path(tts).exists():
            messagebox.showerror(APP_TITLE, "TTS file does not exist.")
            return

        cfg = RewriterConfig(
            tts=Path(tts) if tts else None,
            caption=Path(cap),
            num=int(self.num_var.get()),
            variants_per_request=int(self.vpr_var.get()),
            model=self.model_var.get(),
            stream=bool(self.stream_var.get()),
            no_reasoning=bool(self.no_reasoning_var.get()),
            stream_style=self.style_var.get(),
            max_tokens=int(self.max_tokens_var.get()),
            retries=int(self.retries_var.get()),
            temperature=float(self.temp_var.get()),
            api_key=self.key_var.get().strip() or None,
            stream_log=Path(self.stream_log_var.get()).resolve() if self.stream_log_var.get().strip() else None,
            no_tts=not use_tts,  # Add flag for caption-only mode
        )

        self._clear_log()
        self.status_var.set("Running…")
        self.running = True

        def _stdout_cb(line: str) -> None:
            self.msg_q.put(("out", line))

        def _stderr_cb(line: str) -> None:
            self.msg_q.put(("err", line))

        def _runner():
            try:
                code = Rewriter(cfg).run(on_stdout=_stdout_cb, on_stderr=_stderr_cb)
                self.msg_q.put(("out", f"\n[Done] Exit code: {code}\n"))
            except Exception as e:
                self.msg_q.put(("err", f"\n[Error] {e}\n"))
            finally:
                self.msg_q.put(("status", "Ready"))
                self.msg_q.put(("stopflag", ""))

        self.proc_thread = threading.Thread(target=_runner, daemon=True)
        self.proc_thread.start()

    def _stop(self) -> None:
        messagebox.showinfo(APP_TITLE, "Stop requested. If it doesn't stop soon, close the spawned process from the logs.")

    def _poll_queue(self) -> None:
        try:
            while True:
                ch, text = self.msg_q.get_nowait()
                if ch == "out":
                    self._append_log(text)
                elif ch == "err":
                    self._append_log(text, tag="err")
                elif ch == "status":
                    self.status_var.set(text)
                elif ch == "stopflag":
                    self.running = False
        except queue.Empty:
            pass
        self.after(50, self._poll_queue)

if __name__ == "__main__":
    app = App()
    app.mainloop()
