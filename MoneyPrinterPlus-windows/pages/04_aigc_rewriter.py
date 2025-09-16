#  Copyright © [2024] Wenrui Yu
#
#  All rights reserved. This software and associated documentation files (the "Software") are provided for personal and educational use only. Commercial use of the Software is strictly prohibited unless explicit permission is obtained from the author.
#
#  Permission is hereby granted to any person to use, copy, and modify the Software for non-commercial purposes, provided that the following conditions are met:
#
#  1. The original copyright notice and this permission notice must be included in all copies or substantial portions of the Software.
#  2. Modifications, if any, must retain the original copyright information and must not imply that the modified version is an official version of the Software.
#  3. Any distribution of the Software or its modifications must retain the original copyright notice and include this permission notice.
#
#  For commercial use, including but not limited to selling, distributing, or using the Software as part of any commercial product or service, you must obtain explicit authorization from the author.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHOR OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#  Author: Wenrui Yu
#  email: flydean@163.com
#  Website: [www.flydean.com](https://github.com/WenruiYu)
#  GitHub: [https://github.com/ddean2009/MoneyPrinterPlus](https://github.com/ddean2009/MoneyPrinterPlus)
#
#  All rights reserved.
#

import streamlit as st
import os
import threading
import queue
from pathlib import Path
from typing import Optional
import tempfile
import time

from config.config import my_config, save_config, languages, load_session_state_from_yaml, save_session_state_to_yaml
from pages.common import common_ui
from tools.tr_utils import tr
from tools.utils import random_with_system_time

def clean_file_path(raw_path: str) -> tuple[str, str]:
    """
    Clean a file path by removing surrounding quotes and normalizing.
    Returns (cleaned_path, message)
    """
    if not raw_path or not raw_path.strip():
        return "", ""

    cleaned_path = raw_path.strip()

    # Remove surrounding quotes (both single and double)
    if (cleaned_path.startswith('"') and cleaned_path.endswith('"')) or \
       (cleaned_path.startswith("'") and cleaned_path.endswith("'")):
        cleaned_path = cleaned_path[1:-1]
        message = tr("Path cleaned: quotes removed")
    else:
        message = ""

    # Basic validation - check for obviously invalid characters
    invalid_chars = ['<', '>', '|', '*', '?']
    if any(char in cleaned_path for char in invalid_chars):
        return "", tr("Path contains invalid characters")

    return cleaned_path, message

def validate_manual_path(path: str) -> tuple[bool, str]:
    """
    Validate a manual file path.
    Returns (is_valid, error_message)
    """
    if not path:
        return False, tr("Please provide a valid file path or upload a file")

    path_obj = Path(path)

    # Check if path exists
    if not path_obj.exists():
        return False, tr("File not found")

    # Check if it's a file (not directory)
    if not path_obj.is_file():
        return False, tr("Invalid file path")

    # Check if file is readable
    try:
        with open(path_obj, 'r', encoding='utf-8') as f:
            f.read(1)  # Just try to read first character
    except (PermissionError, UnicodeDecodeError):
        return False, tr("File cannot be read or is not a text file")

    return True, ""

# Import AIGC services (we'll create these)
try:
    from services.aigc.aigc_service import AIGCService
except ImportError:
    st.error("AIGC service not found. Please ensure AIGC functionality is properly installed.")
    AIGCService = None

# Load session state
load_session_state_from_yaml('04_aigc_first_visit')

# Initialize common UI
common_ui()

# Page configuration
st.markdown(f"""
    <div style="text-align: center; padding: 1rem 0; margin-bottom: 2rem; border-bottom: 2px solid #e0e0e0;">
        <h1 style="color: #1f77b4; font-weight: 600; font-size: 2.5rem; margin: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
            {tr('AI Content Rewriter')}
        </h1>
        <p style="color: #666; font-size: 1.2rem; margin: 0.5rem 0 0 0; font-weight: 300;">
            {tr('智能内容改写工具')}
        </p>
    </div>
""", unsafe_allow_html=True)

# Check if AIGC service is available
if AIGCService is None:
    st.error(tr("AIGC service is not available"))
    st.stop()

# Initialize session state for AIGC
if 'aigc_running' not in st.session_state:
    st.session_state['aigc_running'] = False
if 'aigc_msg_queue' not in st.session_state:
    st.session_state['aigc_msg_queue'] = queue.Queue()

def save_aigc_config():
    """Save AIGC-related configuration."""
    if 'aigc' not in my_config:
        my_config['aigc'] = {}

    my_config['aigc']['api_key'] = st.session_state.get('aigc_api_key', '')
    my_config['aigc']['model'] = st.session_state.get('aigc_model', 'deepseek-chat')
    my_config['aigc']['base_url'] = st.session_state.get('aigc_base_url', 'https://api.deepseek.com')
    my_config['aigc']['max_tokens'] = st.session_state.get('aigc_max_tokens', 3072)
    my_config['aigc']['temperature'] = st.session_state.get('aigc_temperature', 0.8)
    my_config['aigc']['stream'] = st.session_state.get('aigc_stream', True)
    my_config['aigc']['no_reasoning'] = st.session_state.get('aigc_no_reasoning', False)
    save_config()

def load_aigc_config():
    """Load AIGC configuration into session state."""
    aigc_config = my_config.get('aigc', {})

    if 'aigc_api_key' not in st.session_state:
        st.session_state['aigc_api_key'] = aigc_config.get('api_key', '')
    if 'aigc_model' not in st.session_state:
        st.session_state['aigc_model'] = aigc_config.get('model', 'deepseek-chat')
    if 'aigc_base_url' not in st.session_state:
        st.session_state['aigc_base_url'] = aigc_config.get('base_url', 'https://api.deepseek.com')
    if 'aigc_max_tokens' not in st.session_state:
        st.session_state['aigc_max_tokens'] = aigc_config.get('max_tokens', 3072)
    if 'aigc_temperature' not in st.session_state:
        st.session_state['aigc_temperature'] = aigc_config.get('temperature', 0.8)
    if 'aigc_stream' not in st.session_state:
        st.session_state['aigc_stream'] = aigc_config.get('stream', True)
    if 'aigc_no_reasoning' not in st.session_state:
        st.session_state['aigc_no_reasoning'] = aigc_config.get('no_reasoning', False)

# Load configuration
load_aigc_config()

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown(f"### {tr('Input Files')}")

    # Mode selection
    use_tts = st.checkbox(
        tr("Include TTS Rewriting"),
        value=st.session_state.get('aigc_use_tts', True),
        key='aigc_use_tts',
        help=tr("Uncheck for caption-only mode (no TTS generation)")
    )

    # Initialize variables
    tts_file = None
    tts_path = None
    tts_path_raw = ""
    caption_file = None
    caption_path = None
    caption_path_raw = ""
    # Get input method preferences from session state
    tts_input_method = st.session_state.get('tts_input_method', tr("Upload file"))
    cap_input_method = st.session_state.get('cap_input_method', tr("Upload file"))

    # File inputs
    col_tts, col_cap = st.columns(2)

    # TTS File Input
    with col_tts:
        if use_tts:
            st.markdown(f"**{tr('TTS Text File (.txt)')}**")
            tts_input_method = st.radio(
                "",
                [tr("Upload file"), tr("Manual path")],
                key='tts_input_method',
                horizontal=True,
                label_visibility="collapsed",
                index=0 if tts_input_method == tr("Upload file") else 1
            )

            if tts_input_method == tr("Upload file"):
                tts_file = st.file_uploader(
                    "",
                    type=['txt'],
                    key='aigc_tts_file',
                    help=tr("Upload TTS text file for voice generation"),
                    label_visibility="collapsed"
                )
                tts_path = None
                tts_path_raw = ""
            else:
                tts_path_raw = st.text_input(
                    "",
                    key='aigc_tts_path',
                    placeholder=tr("Enter file path manually (drag & drop or paste)"),
                    help=tr("Or upload file above"),
                    label_visibility="collapsed"
                )
                tts_path, tts_clean_msg = clean_file_path(tts_path_raw)
                if tts_clean_msg:
                    st.info(tts_clean_msg)
                tts_file = None
        else:
            st.info(tr("Caption-only mode: TTS disabled"))
            tts_file = None
            tts_path = None
            tts_path_raw = ""

    # Caption File Input
    with col_cap:
        st.markdown(f"**{tr('Caption File (.txt)')}**")
        cap_input_method = st.radio(
            "",
            [tr("Upload file"), tr("Manual path")],
            key='cap_input_method',
            horizontal=True,
            label_visibility="collapsed",
            index=0 if cap_input_method == tr("Upload file") else 1
        )

        if cap_input_method == tr("Upload file"):
            caption_file = st.file_uploader(
                "",
                type=['txt'],
                key='aigc_caption_file',
                help=tr("Upload caption file for rewriting"),
                label_visibility="collapsed"
            )
            caption_path = None
            caption_path_raw = ""
        else:
            caption_path_raw = st.text_input(
                "",
                key='aigc_caption_path',
                placeholder=tr("Enter file path manually (drag & drop or paste)"),
                help=tr("Or upload file above"),
                label_visibility="collapsed"
            )
            caption_path, cap_clean_msg = clean_file_path(caption_path_raw)
            if cap_clean_msg:
                st.info(cap_clean_msg)
            caption_file = None

    # Generation settings
    st.markdown(f"### {tr('Generation Settings')}")

    col_settings1, col_settings2 = st.columns(2)

    with col_settings1:
        num_variants = st.number_input(
            tr("Number of Variants"),
            min_value=1,
            max_value=10,
            value=st.session_state.get('aigc_num_variants', 3),
            key='aigc_num_variants'
        )

        variants_per_request = st.number_input(
            tr("Variants per Request"),
            min_value=1,
            max_value=5,
            value=st.session_state.get('aigc_variants_per_request', 1),
            key='aigc_variants_per_request'
        )

    with col_settings2:
        temperature = st.slider(
            tr("Temperature"),
            min_value=0.0,
            max_value=2.0,
            value=st.session_state.get('aigc_temperature', 0.8),
            step=0.1,
            key='aigc_temperature'
        )

        max_tokens = st.slider(
            tr("Max Tokens"),
            min_value=256,
            max_value=4096,
            value=st.session_state.get('aigc_max_tokens', 3072),
            step=256,
            key='aigc_max_tokens'
        )

with col2:
    st.markdown(f"### {tr('Model Configuration')}")

    # API Configuration
    with st.expander(tr("API Settings"), expanded=True):
        api_key = st.text_input(
            tr("API Key"),
            value=st.session_state.get('aigc_api_key', ''),
            type="password",
            key='aigc_api_key',
            on_change=save_aigc_config
        )

        model_options = ['deepseek-chat', 'deepseek-reasoner', 'gpt-3.5-turbo', 'gpt-4']
        model = st.selectbox(
            tr("Model"),
            options=model_options,
            index=model_options.index(st.session_state.get('aigc_model', 'deepseek-chat')),
            key='aigc_model',
            on_change=save_aigc_config
        )

        base_url = st.text_input(
            tr("Base URL"),
            value=st.session_state.get('aigc_base_url', 'https://api.deepseek.com'),
            key='aigc_base_url',
            on_change=save_aigc_config
        )

    # Streaming options
    with st.expander(tr("Streaming Options")):
        stream_enabled = st.checkbox(
            tr("Enable Streaming"),
            value=st.session_state.get('aigc_stream', True),
            key='aigc_stream',
            on_change=save_aigc_config
        )

        no_reasoning = st.checkbox(
            tr("Hide Reasoning"),
            value=st.session_state.get('aigc_no_reasoning', False),
            key='aigc_no_reasoning',
            on_change=save_aigc_config,
            help=tr("Hide AI reasoning process in output")
        )

# Process button and status
col_process, col_status = st.columns([1, 2])

with col_process:
    # Validation
    can_process = False
    validation_msg = ""

    # Validate caption file/path
    caption_valid = False
    caption_error = ""

    if cap_input_method == tr("Upload file"):
        if caption_file:
            caption_valid = True
        else:
            caption_error = tr("Please upload a caption file")
    else:  # Manual path
        if caption_path:
            caption_valid, caption_error = validate_manual_path(caption_path)
        else:
            caption_error = tr("Please provide a valid file path or upload a file")

    # Validate TTS file/path
    tts_valid = True
    tts_error = ""

    if use_tts:
        if tts_input_method == tr("Upload file"):
            if tts_file:
                tts_valid = True
            else:
                tts_error = tr("Please upload a TTS file or disable TTS mode")
                tts_valid = False
        else:  # Manual path
            if tts_path:
                tts_valid, tts_error = validate_manual_path(tts_path)
            else:
                tts_error = tr("Please provide a valid file path or upload a file")
                tts_valid = False

    # Check for conflicting inputs (both file upload and manual path)
    if cap_input_method == tr("Upload file") and caption_path_raw:
        caption_error = tr("Please choose either manual path or file upload, not both")
        caption_valid = False
    if use_tts and tts_input_method == tr("Upload file") and tts_path_raw:
        tts_error = tr("Please choose either manual path or file upload, not both")
        tts_valid = False

    # Final validation
    if not caption_valid:
        validation_msg = caption_error
    elif not tts_valid:
        validation_msg = tts_error
    elif not api_key:
        validation_msg = tr("Please configure API key")
    else:
        can_process = True
        validation_msg = tr("Ready to process")

    st.markdown(f"### {tr('Processing')}")
    st.info(validation_msg)

    # Process button
    if st.button(
        tr("Start Rewriting"),
        disabled=not can_process or st.session_state.get('aigc_running', False),
        type="primary",
        use_container_width=True
    ):
        st.session_state['aigc_running'] = True

        # Save temporary files
        temp_dir = Path(tempfile.mkdtemp())

        # Handle caption file
        if cap_input_method == tr("Upload file"):
            # Save uploaded caption file
            caption_path = temp_dir / "caption.txt"
            caption_content = caption_file.getvalue().decode('utf-8')
            caption_path.write_text(caption_content, encoding='utf-8')
        else:
            # Use manual caption path
            caption_path = Path(caption_path)

        # Handle TTS file if provided
        tts_path = None
        if use_tts:
            if tts_input_method == tr("Upload file"):
                # Save uploaded TTS file
                tts_path = temp_dir / "tts.txt"
                tts_content = tts_file.getvalue().decode('utf-8')
                tts_path.write_text(tts_content, encoding='utf-8')
            else:
                # Use manual TTS path
                tts_path = Path(tts_path)

        # Store paths in session state
        st.session_state['aigc_temp_dir'] = str(temp_dir)
        st.session_state['aigc_caption_path'] = str(caption_path)
        st.session_state['aigc_tts_path'] = str(tts_path) if tts_path else None

        st.rerun()

# Processing area
if st.session_state.get('aigc_running', False):
    st.markdown("---")

    # Progress area
    progress_placeholder = st.empty()
    log_placeholder = st.empty()

    with progress_placeholder.container():
        st.markdown(f"### {tr('Processing Progress')}")
        progress_bar = st.progress(0)
        status_text = st.empty()

    with log_placeholder.container():
        st.markdown(f"### {tr('Processing Log')}")
        log_area = st.empty()

    # Initialize AIGC service
    try:
        aigc_service = AIGCService()

        # Configure service
        config = {
            'api_key': api_key,
            'model': model,
            'base_url': base_url,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'stream': stream_enabled,
            'no_reasoning': no_reasoning,
            'num_variants': num_variants,
            'variants_per_request': variants_per_request,
            'use_tts': use_tts
        }

        # Get file paths
        caption_path = st.session_state.get('aigc_caption_path')
        tts_path = st.session_state.get('aigc_tts_path')

        # Process files
        success = aigc_service.process_files(
            caption_path=caption_path,
            tts_path=tts_path,
            config=config,
            progress_callback=lambda p, s: update_progress(progress_bar, status_text, p, s),
            log_callback=lambda msg: update_log(log_area, msg)
        )

        if success:
            st.success(tr("Rewriting completed successfully!"))

            # Show results
            st.markdown(f"### {tr('Generated Files')}")

            temp_dir = Path(st.session_state.get('aigc_temp_dir', ''))

            # List generated caption files
            caption_files = list(temp_dir.glob("variant_*_caption.txt"))
            if caption_files:
                st.markdown(f"**{tr('Caption Variants:')}**")
                for f in sorted(caption_files):
                    with open(f, 'r', encoding='utf-8') as file:
                        content = file.read()
                    st.text_area(
                        f.name,
                        value=content,
                        height=100,
                        key=f"caption_{f.name}"
                    )

            # List generated TTS files if TTS was enabled
            if use_tts:
                tts_files = list(temp_dir.glob("variant_*_tts.txt"))
                if tts_files:
                    st.markdown(f"**{tr('TTS Variants:')}**")
                    for f in sorted(tts_files):
                        with open(f, 'r', encoding='utf-8') as file:
                            content = file.read()
                        st.text_area(
                            f.name,
                            value=content,
                            height=100,
                            key=f"tts_{f.name}"
                        )

            # Download section
            st.markdown(f"### {tr('Download Results')}")
            col_zip, col_cleanup = st.columns(2)

            with col_zip:
                if st.button(tr("Download All as ZIP"), type="primary"):
                    import zipfile
                    import io

                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for file_path in temp_dir.glob("variant_*.txt"):
                            zip_file.write(file_path, file_path.name)

                    zip_buffer.seek(0)
                    st.download_button(
                        label=tr("Download ZIP"),
                        data=zip_buffer,
                        file_name=f"aigc_rewrite_{random_with_system_time()}.zip",
                        mime="application/zip"
                    )

            with col_cleanup:
                if st.button(tr("Clean Up Files")):
                    import shutil
                    if temp_dir.exists():
                        shutil.rmtree(temp_dir)
                    st.success(tr("Temporary files cleaned up!"))
                    st.rerun()

        else:
            st.error(tr("Rewriting failed. Please check the logs above."))

    except Exception as e:
        st.error(tr("Error during processing:") + f" {str(e)}")
        st.exception(e)

    # Reset running state
    st.session_state['aigc_running'] = False

def update_progress(progress_bar, status_text, progress, status):
    """Update progress bar and status text."""
    progress_bar.progress(progress)
    status_text.text(status)

def update_log(log_area, message):
    """Update log area with new message."""
    current_log = log_area.text if hasattr(log_area, 'text') else ""
    new_log = current_log + "\n" + message
    log_area.text_area(tr("Processing Log"), value=new_log, height=200)

# Footer
st.markdown("---")
st.markdown(f"*{tr('Tip: For best results, ensure your caption files contain clear, well-structured content with hashtags at the end.')}*")

