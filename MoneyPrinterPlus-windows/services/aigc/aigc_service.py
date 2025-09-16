# -*- coding: utf-8 -*-
"""
AIGC Service for MoneyPrinterPlus
Integrates TikTokRewriter functionality into the MMP web UI
"""

import os
import sys
import tempfile
import shutil
import threading
from pathlib import Path
from typing import Optional, Callable, Dict, Any
import subprocess
import time

# Add AIGC path to Python path
aigc_path = Path(__file__).parent.parent.parent.parent / "aigc"
if str(aigc_path) not in sys.path:
    sys.path.insert(0, str(aigc_path))

try:
    from rewriter_core import RewriterConfig, Rewriter
except ImportError:
    RewriterConfig = None
    Rewriter = None


class AIGCService:
    """
    AIGC Service wrapper for TikTokRewriter integration
    """

    def __init__(self):
        """Initialize the AIGC service."""
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if required dependencies are available."""
        if RewriterConfig is None or Rewriter is None:
            raise ImportError(
                "TikTokRewriter dependencies not found. "
                "Please ensure the AIGC directory is properly set up."
            )

        # Check if AIGC directory exists
        aigc_dir = Path(__file__).parent.parent.parent.parent / "aigc"
        if not aigc_dir.exists():
            raise FileNotFoundError(
                f"AIGC directory not found at {aigc_dir}. "
                "Please ensure TikTokRewriter is properly installed."
            )

    def process_files(
        self,
        caption_path: str,
        tts_path: Optional[str] = None,
        config: Dict[str, Any] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        Process caption and optional TTS files using TikTokRewriter.

        Args:
            caption_path: Path to caption file
            tts_path: Optional path to TTS file
            config: Configuration dictionary
            progress_callback: Callback for progress updates (progress, status)
            log_callback: Callback for log messages

        Returns:
            bool: True if processing was successful
        """
        try:
            # Update progress
            if progress_callback:
                progress_callback(0.1, "Initializing...")

            # Log start
            if log_callback:
                log_callback(f"Starting AIGC processing...")
                log_callback(f"Caption file: {caption_path}")
                if tts_path:
                    log_callback(f"TTS file: {tts_path}")
                else:
                    log_callback("Mode: Caption-only (no TTS)")

            # Create RewriterConfig
            rewriter_config = RewriterConfig(
                caption=Path(caption_path),
                tts=Path(tts_path) if tts_path else None,
                num=config.get('num_variants', 3),
                variants_per_request=config.get('variants_per_request', 1),
                model=config.get('model', 'deepseek-chat'),
                base_url=config.get('base_url', 'https://api.deepseek.com'),
                temperature=config.get('temperature', 0.8),
                max_tokens=config.get('max_tokens', 3072),
                retries=2,
                stream=config.get('stream', True),
                stream_style="compact",
                no_reasoning=config.get('no_reasoning', False),
                api_key=config.get('api_key'),
                no_tts=not config.get('use_tts', True)
            )

            if progress_callback:
                progress_callback(0.3, "Configuration loaded")

            # Create rewriter instance
            rewriter = Rewriter(rewriter_config)

            if progress_callback:
                progress_callback(0.5, "Starting rewrite process...")

            # Progress tracking for streaming
            progress_step = 0.5 / max(1, config.get('num_variants', 3))  # Distribute remaining progress
            current_progress = 0.5

            def stdout_callback(line: str):
                if log_callback:
                    log_callback(f"[STDOUT] {line.strip()}")
                # Update progress based on output
                nonlocal current_progress
                if "variant_" in line.lower():
                    current_progress += progress_step
                    if progress_callback:
                        progress_callback(min(current_progress, 0.9), f"Processing variant...")

            def stderr_callback(line: str):
                if log_callback:
                    log_callback(f"[STDERR] {line.strip()}")

            # Run the rewriter
            if log_callback:
                log_callback("Executing TikTokRewriter...")

            exit_code = rewriter.run(
                on_stdout=stdout_callback,
                on_stderr=stderr_callback
            )

            if progress_callback:
                progress_callback(1.0, "Processing completed")

            if log_callback:
                log_callback(f"TikTokRewriter finished with exit code: {exit_code}")

            return exit_code == 0

        except Exception as e:
            if log_callback:
                log_callback(f"Error during processing: {str(e)}")
            if progress_callback:
                progress_callback(1.0, f"Error: {str(e)}")
            return False

    def validate_files(self, caption_path: str, tts_path: Optional[str] = None) -> tuple[bool, str]:
        """
        Validate input files.

        Args:
            caption_path: Path to caption file
            tts_path: Optional path to TTS file

        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            # Check caption file
            if not Path(caption_path).exists():
                return False, "Caption file does not exist"

            if not Path(caption_path).is_file():
                return False, "Caption path is not a file"

            # Check TTS file if provided
            if tts_path:
                if not Path(tts_path).exists():
                    return False, "TTS file does not exist"

                if not Path(tts_path).is_file():
                    return False, "TTS path is not a file"

            # Check file sizes (reasonable limits)
            caption_size = Path(caption_path).stat().st_size
            if caption_size > 10 * 1024 * 1024:  # 10MB limit
                return False, "Caption file is too large (>10MB)"

            if tts_path:
                tts_size = Path(tts_path).stat().st_size
                if tts_size > 10 * 1024 * 1024:  # 10MB limit
                    return False, "TTS file is too large (>10MB)"

            return True, "Files are valid"

        except Exception as e:
            return False, f"File validation error: {str(e)}"

    def get_available_models(self) -> list[str]:
        """
        Get list of available AI models for rewriting.

        Returns:
            list: Available model names
        """
        return [
            'deepseek-chat',
            'deepseek-reasoner',
            'gpt-3.5-turbo',
            'gpt-4',
            'gpt-4-turbo',
            'claude-3-sonnet',
            'claude-3-haiku'
        ]

    def estimate_cost(self, config: Dict[str, Any], caption_length: int, tts_length: int = 0) -> Dict[str, Any]:
        """
        Estimate the cost of processing based on input sizes.

        Args:
            config: Configuration dictionary
            caption_length: Length of caption text in characters
            tts_length: Length of TTS text in characters

        Returns:
            dict: Cost estimation information
        """
        model = config.get('model', 'deepseek-chat')
        num_variants = config.get('num_variants', 3)

        # Rough token estimation (characters * 0.3 for English, 0.5 for Chinese/mixed)
        caption_tokens = int(caption_length * 0.4)  # Average for mixed content
        tts_tokens = int(tts_length * 0.4) if tts_length > 0 else 0

        # Total tokens per variant
        total_input_tokens = caption_tokens + tts_tokens
        estimated_output_tokens = int(total_input_tokens * 1.5)  # Estimate output size

        # Cost estimation (rough, will vary by provider)
        cost_per_1k_input = 0.001  # $0.001 per 1K input tokens
        cost_per_1k_output = 0.002  # $0.002 per 1K output tokens

        total_input_cost = (total_input_tokens * num_variants / 1000) * cost_per_1k_input
        total_output_cost = (estimated_output_tokens * num_variants / 1000) * cost_per_1k_output
        total_cost = total_input_cost + total_output_cost

        return {
            'model': model,
            'num_variants': num_variants,
            'estimated_input_tokens': total_input_tokens * num_variants,
            'estimated_output_tokens': estimated_output_tokens * num_variants,
            'estimated_cost_usd': round(total_cost, 4),
            'processing_time_estimate': f"{num_variants * 30}-{num_variants * 60}s"
        }


def test_aigc_service():
    """Test function for AIGC service."""
    print("Testing AIGC Service...")

    try:
        service = AIGCService()
        print("✅ AIGC Service initialized successfully")

        # Test model list
        models = service.get_available_models()
        print(f"✅ Available models: {models}")

        print("✅ All tests passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    test_aigc_service()
