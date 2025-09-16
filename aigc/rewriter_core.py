# -*- coding: utf-8 -*-
"""
Core wrapper for the TikTok rewrites.
- Exposes RewriterConfig and Rewriter for GUI or other callers.
- Delegates to your proven CLI script `rewrite_tiktok_ds.py` via subprocess,
  so you keep one source of truth for the rewriting logic.
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional, Callable, List
import subprocess
import sys
import shlex
import os

__all__ = ["RewriterConfig", "Rewriter"]

@dataclass
class RewriterConfig:
    # Required IO
    caption: Path                          # Caption is always required
    tts: Optional[Path] = None            # TTS is optional for caption-only mode
    
    # Generation
    num: int = 3                          # total variants across all calls
    variants_per_request: int = 1         # how many variants to request per API call
    model: str = "deepseek-chat"          # or "deepseek-reasoner"
    base_url: str = "https://api.deepseek.com"
    temperature: float = 0.8              # harmless for reasoner
    max_tokens: int = 3072
    retries: int = 2

    # Streaming
    stream: bool = False
    stream_style: Literal["compact", "raw"] = "compact"
    no_reasoning: bool = False            # hide reasoning_content if True
    stream_log: Optional[Path] = None     # optional file to log the raw stream

    # Auth
    api_key: Optional[str] = None         # if None, use env DEEPSEEK_API_KEY
    
    # Mode
    no_tts: bool = False                  # If True, only process captions (caption-only mode)

    # Python/Script
    python_exe: Optional[Path] = None     # default: current interpreter
    script_path: Optional[Path] = None    # default: alongside this file (rewrite_tiktok_ds.py)

class Rewriter:
    """
    Thin wrapper that calls the CLI script `rewrite_tiktok_ds.py`.

    Usage:
        # With TTS:
        cfg = RewriterConfig(tts=Path("a.txt"), caption=Path("b.txt"), num=4)
        code = Rewriter(cfg).run(print, print)
        
        # Caption-only mode:
        cfg = RewriterConfig(caption=Path("b.txt"), num=4, no_tts=True)
        code = Rewriter(cfg).run(print, print)
    """

    def __init__(self, cfg: RewriterConfig):
        self.cfg = cfg
        self._proc: Optional[subprocess.Popen] = None

    def _resolve_script(self) -> Path:
        if self.cfg.script_path is not None:
            return Path(self.cfg.script_path).resolve()
        here = Path(__file__).parent.resolve()
        candidate = here / "rewrite_tiktok_ds.py"
        if candidate.exists():
            return candidate
        cwd_candidate = Path.cwd() / "rewrite_tiktok_ds.py"
        if cwd_candidate.exists():
            return cwd_candidate.resolve()
        raise FileNotFoundError(
            "Cannot find rewrite_tiktok_ds.py. "
            "Place it alongside rewriter_core.py or set RewriterConfig.script_path."
        )

    def _python_exe(self) -> Path:
        if self.cfg.python_exe is not None:
            return Path(self.cfg.python_exe).resolve()
        return Path(sys.executable).resolve()

    def _build_cmd(self) -> List[str]:
        script = self._resolve_script()
        c: List[str] = [
            str(self._python_exe()),
            str(script),
            "--caption", str(Path(self.cfg.caption).resolve()),
            "--num", str(int(self.cfg.num)),
            "--variants-per-request", str(int(self.cfg.variants_per_request)),
            "--model", self.cfg.model,
            "--base_url", self.cfg.base_url,
            "--max_tokens", str(int(self.cfg.max_tokens)),
            "--retries", str(int(self.cfg.retries)),
            "--stream-style", self.cfg.stream_style,
            "--temperature", str(self.cfg.temperature),
        ]
        
        # Add TTS only if provided and not in no-tts mode
        if self.cfg.tts and not self.cfg.no_tts:
            c.extend(["--tts", str(Path(self.cfg.tts).resolve())])
        elif self.cfg.no_tts:
            c.append("--no-tts")
        
        if self.cfg.stream:
            c.append("--stream")
            if self.cfg.no_reasoning:
                c.append("--no-reasoning")
        if self.cfg.stream_log:
            c.extend(["--stream-log", str(Path(self.cfg.stream_log).resolve())])
        return c

    def _build_env(self) -> dict:
        env = os.environ.copy()
        if self.cfg.api_key:
            env["DEEPSEEK_API_KEY"] = self.cfg.api_key
        return env

    def run(
        self,
        on_stdout: Optional[Callable[[str], None]] = None,
        on_stderr: Optional[Callable[[str], None]] = None,
        cwd: Optional[Path] = None,
    ) -> int:
        """Run the CLI script. If callbacks are provided, stream lines to them. Returns the exit code."""
        cmd = self._build_cmd()
        env = self._build_env()
        workdir = str(cwd or Path.cwd())

        if on_stdout:
            on_stdout("Running: " + " ".join(shlex.quote(x) for x in cmd) + "\n")

        self._proc = subprocess.Popen(
            cmd,
            cwd=workdir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        assert self._proc.stdout and self._proc.stderr
        for line in self._proc.stdout:
            if on_stdout:
                on_stdout(line)
        err_accum = []
        for line in self._proc.stderr:
            err_accum.append(line)
            if on_stderr:
                on_stderr(line)

        code = self._proc.wait()
        self._proc = None

        if code != 0 and not err_accum and on_stderr:
            on_stderr(f"[Rewriter] Process exited with code {code}\n")
        return code

    def stop(self) -> None:
        """Best-effort stop (not wired to GUI stop button here)."""
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
            except Exception:
                pass
            try:
                self._proc.kill()
            except Exception:
                pass
            self._proc = None
