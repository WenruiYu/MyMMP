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
from pathlib import Path
from typing import Optional, Tuple

from config.config import my_config, save_config, load_session_state_from_yaml
from pages.common import common_ui
from tools.tr_utils import tr


class AIGCRewriterPage:
    """Optimized AIGC Rewriter Page Class"""
    
    def __init__(self):
        self.setup_page()
        self.load_config()
    
    def setup_page(self):
        """Initialize page configuration and session state."""
        load_session_state_from_yaml('04_aigc_first_visit')
        common_ui()
        
        # Initialize session state
        if 'aigc_running' not in st.session_state:
            st.session_state['aigc_running'] = False
        
        # Page header
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
        
        # Check service availability
        try:
            from services.aigc.aigc_service import AIGCService
            self.aigc_service = AIGCService
        except ImportError:
            st.error(tr("AIGC service is not available"))
            st.stop()
    
    def load_config(self):
        """Load AIGC configuration with defaults."""
        aigc_config = my_config.get('aigc', {})
        defaults = {
            'aigc_api_key': '',
            'aigc_model': 'deepseek-chat',
            'aigc_base_url': 'https://api.deepseek.com',
            'aigc_max_tokens': 3072,
            'aigc_temperature': 0.8,
            'aigc_stream': True,
            'aigc_no_reasoning': False,
            'aigc_num_variants': 3,
            'aigc_variants_per_request': 1,
            'aigc_use_tts': True
        }
        
        for key, default in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = aigc_config.get(key.replace('aigc_', ''), default)
    
    def save_config(self):
        """Save current configuration."""
        if 'aigc' not in my_config:
            my_config['aigc'] = {}
        
        config_mapping = {
            'aigc_api_key': 'api_key',
            'aigc_model': 'model', 
            'aigc_base_url': 'base_url',
            'aigc_max_tokens': 'max_tokens',
            'aigc_temperature': 'temperature',
            'aigc_stream': 'stream',
            'aigc_no_reasoning': 'no_reasoning'
        }
        
        for session_key, config_key in config_mapping.items():
            if session_key in st.session_state:
                my_config['aigc'][config_key] = st.session_state[session_key]
        
        save_config()
    
    @staticmethod
    def clean_file_path(raw_path: str) -> Tuple[str, str]:
        """Clean file path by removing quotes and basic validation."""
        if not raw_path or not raw_path.strip():
            return "", ""
        
        cleaned = raw_path.strip()
        message = ""
        
        # Remove quotes
        if (cleaned.startswith('"') and cleaned.endswith('"')) or \
           (cleaned.startswith("'") and cleaned.endswith("'")):
            cleaned = cleaned[1:-1]
            message = tr("Path cleaned: quotes removed")
        
        # Basic validation
        invalid_chars = ['<', '>', '|', '*', '?']
        if any(char in cleaned for char in invalid_chars):
            return "", tr("Path contains invalid characters")
        
        return cleaned, message
    
    @staticmethod
    def validate_file_path(path: str) -> Tuple[bool, str]:
        """Validate file path exists and is readable."""
        if not path:
            return False, tr("Please provide a valid file path")
        
        path_obj = Path(path)
        if not path_obj.exists():
            return False, tr("File not found")
        if not path_obj.is_file():
            return False, tr("Invalid file path")
        
        try:
            with open(path_obj, 'r', encoding='utf-8') as f:
                f.read(1)
        except (PermissionError, UnicodeDecodeError):
            return False, tr("File cannot be read or is not a text file")
        
        return True, ""
    
    @staticmethod
    def browse_file(title: str) -> str:
        """Open file browser dialog."""
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        file_path = filedialog.askopenfilename(
            title=title,
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        root.destroy()
        return file_path or ''
    
    def create_file_input(self, label: str, session_key: str, browse_key: str, help_text: str, required: bool = True) -> Optional[str]:
        """Create file input with browse functionality."""
        st.markdown(f"**{tr(label)}**")
        
        # Handle browser selection
        browser_key = f'{session_key}_browser'
        if browser_key in st.session_state and st.session_state[browser_key]:
            default_value = st.session_state[browser_key]
            st.session_state[browser_key] = ''
        else:
            default_value = st.session_state.get(session_key, '')
        
        # File path input
        path_raw = st.text_input(
            "",
            value=default_value,
            key=session_key,
            placeholder=tr("Enter file path or click Browse"),
            help=help_text,
            label_visibility="collapsed"
        )
        
        # Browse button
        if st.button(tr(f"Browse {label.split()[0]} File"), key=browse_key, type="secondary"):
            file_path = self.browse_file(f"Select {label}")
            if file_path:
                st.session_state[browser_key] = file_path
                st.rerun()
        
        # Clean and validate
        clean_path, clean_msg = self.clean_file_path(path_raw)
        if clean_msg:
            st.info(clean_msg)
        
        return clean_path if clean_path else None
    
    def render_inputs(self):
        """Render input section."""
        st.markdown(f"### {tr('Input Files')}")
        
        # TTS toggle
        use_tts = st.checkbox(
            tr("Include TTS Rewriting"),
            value=st.session_state.get('aigc_use_tts', True),
            key='aigc_use_tts',
            help=tr("Uncheck for caption-only mode (no TTS generation)")
        )
        
        # File inputs
        tts_path = None
        if use_tts:
            tts_path = self.create_file_input(
                "TTS Text File (.txt)",
                'aigc_tts_path',
                'tts_browse_btn',
                tr("Paste: C:\\Users\\plove\\Downloads\\test\\tts.txt")
            )
        else:
            st.info(tr("Caption-only mode: TTS disabled"))
        
        caption_path = self.create_file_input(
            "Caption File (.txt)",
            'aigc_caption_path', 
            'cap_browse_btn',
            tr("Paste: C:\\Users\\plove\\Downloads\\test\\caption.txt")
        )
        
        return use_tts, tts_path, caption_path
    
    def render_settings(self):
        """Render generation settings."""
        st.markdown(f"### {tr('Generation Settings')}")
        col1, col2 = st.columns(2)
        
        with col1:
            num_variants = st.number_input(
                tr("Number of Variants"), 1, 50, 
                st.session_state.get('aigc_num_variants', 3),
                key='aigc_num_variants'
            )
            variants_per_request = st.number_input(
                tr("Variants per Request"), 1, 5,
                st.session_state.get('aigc_variants_per_request', 1),
                key='aigc_variants_per_request'
            )
        
        with col2:
            temperature = st.slider(
                tr("Temperature"), 0.0, 2.0,
                st.session_state.get('aigc_temperature', 0.8),
                0.1, key='aigc_temperature'
            )
            max_tokens = st.slider(
                tr("Max Tokens"), 256, 4096,
                st.session_state.get('aigc_max_tokens', 3072),
                256, key='aigc_max_tokens'
            )
        
        return num_variants, variants_per_request, temperature, max_tokens
    
    def render_model_config(self):
        """Render model configuration."""
        st.markdown(f"### {tr('Model Configuration')}")
        
        with st.expander(tr("API Settings"), expanded=True):
            api_key = st.text_input(
                tr("API Key"),
                value=st.session_state.get('aigc_api_key', ''),
                type="password",
                key='aigc_api_key',
                on_change=self.save_config
            )
            
            model_options = ['deepseek-chat', 'deepseek-reasoner', 'gpt-3.5-turbo', 'gpt-4']
            model = st.selectbox(
                tr("Model"), model_options,
                index=model_options.index(st.session_state.get('aigc_model', 'deepseek-chat')),
                key='aigc_model', on_change=self.save_config
            )
            
            base_url = st.text_input(
                tr("Base URL"),
                value=st.session_state.get('aigc_base_url', 'https://api.deepseek.com'),
                key='aigc_base_url', on_change=self.save_config
            )
        
        with st.expander(tr("Streaming Options")):
            stream_enabled = st.checkbox(
                tr("Enable Streaming"),
                value=st.session_state.get('aigc_stream', True),
                key='aigc_stream', on_change=self.save_config
            )
            no_reasoning = st.checkbox(
                tr("Hide Reasoning"),
                value=st.session_state.get('aigc_no_reasoning', False),
                key='aigc_no_reasoning', on_change=self.save_config,
                help=tr("Hide AI reasoning process in output")
            )
        
        return api_key, model, base_url, stream_enabled, no_reasoning
    
    def validate_inputs(self, use_tts: bool, tts_path: Optional[str], caption_path: Optional[str], api_key: str) -> Tuple[bool, str]:
        """Validate all inputs."""
        if not caption_path:
            return False, tr("Please provide caption file path")
        
        caption_valid, caption_error = self.validate_file_path(caption_path)
        if not caption_valid:
            return False, caption_error
        
        if use_tts:
            if not tts_path:
                return False, tr("Please provide TTS file path")
            tts_valid, tts_error = self.validate_file_path(tts_path)
            if not tts_valid:
                return False, tts_error
        
        if not api_key:
            return False, tr("Please configure API key")
        
        return True, tr("Ready to process")
    
    def update_log(self, log_area, message):
        """Update processing log."""
        if 'aigc_log_messages' not in st.session_state:
            st.session_state['aigc_log_messages'] = []
        
        st.session_state['aigc_log_messages'].append(str(message))
        
        # Keep last 50 messages
        if len(st.session_state['aigc_log_messages']) > 50:
            st.session_state['aigc_log_messages'] = st.session_state['aigc_log_messages'][-50:]
        
        log_content = "\n".join(st.session_state['aigc_log_messages'])
        log_area.code(log_content, language=None)
    
    @staticmethod
    def update_progress(progress_bar, status_text, progress, status):
        """Update progress display."""
        progress_bar.progress(progress)
        status_text.text(status)
    
    def display_results(self, use_tts: bool):
        """Display generated files."""
        st.markdown(f"### {tr('Generated Files')}")
        
        caption_path = st.session_state.get('aigc_caption_file_path', '')
        tts_path = st.session_state.get('aigc_tts_file_path', '')
        
        def show_files(file_type: str, pattern: str, icon: str, file_path: str, show_dir: bool = True):
            if not file_path:
                return
            
            file_dir = Path(file_path).parent
            files = list(file_dir.glob(pattern))
            
            if files:
                st.markdown(f"**{tr(f'{file_type} Variants:')}** ({len(files)} {tr('files generated')})")
                if show_dir:
                    st.info(f"**{tr('Files saved to:')}** `{file_dir}`")
                
                for f in sorted(files):
                    st.text(f"{icon} {f.name} - {f.stat().st_size} bytes")
        
        # Show results
        show_files("Caption", "variant_*_caption.txt", "📄", caption_path)
        
        if use_tts and tts_path:
            caption_dir = Path(caption_path).parent if caption_path else None
            tts_dir = Path(tts_path).parent
            show_separate = tts_dir != caption_dir
            show_files("TTS", "variant_*_tts.txt", "🎤", tts_path, show_separate)
    
    def process_files(self, config: dict, caption_path: str, tts_path: Optional[str]):
        """Process files with AIGC service."""
        progress_placeholder = st.empty()
        log_placeholder = st.empty()
        
        with progress_placeholder.container():
            st.markdown(f"### {tr('Processing Progress')}")
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        with log_placeholder.container():
            st.markdown(f"### {tr('Processing Log')}")
            log_area = st.empty()
        
        try:
            aigc_service = self.aigc_service()
            
            success = aigc_service.process_files(
                caption_path=caption_path,
                tts_path=tts_path,
                config=config,
                progress_callback=lambda p, s: self.update_progress(progress_bar, status_text, p, s),
                log_callback=lambda msg: self.update_log(log_area, msg)
            )
            
            if success:
                st.success(tr("Rewriting completed successfully!"))
                self.display_results(config['use_tts'])
            else:
                st.error(tr("Rewriting failed. Please check the logs above."))
                
        except Exception as e:
            st.error(tr("Error during processing:") + f" {str(e)}")
            st.exception(e)
        
        finally:
            st.session_state['aigc_running'] = False
    
    def run(self):
        """Main application logic."""
        # Main layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            use_tts, tts_path, caption_path = self.render_inputs()
            num_variants, variants_per_request, temperature, max_tokens = self.render_settings()
        
        with col2:
            api_key, model, base_url, stream_enabled, no_reasoning = self.render_model_config()
        
        # Processing section
        col_process, _ = st.columns([1, 2])
        
        with col_process:
            can_process, validation_msg = self.validate_inputs(use_tts, tts_path, caption_path, api_key)
            
            st.markdown(f"### {tr('Processing')}")
            st.info(validation_msg)
            
            if st.button(
                tr("Start Rewriting"),
                disabled=not can_process or st.session_state.get('aigc_running', False),
                type="primary",
                use_container_width=True
            ):
                st.session_state['aigc_running'] = True
                st.session_state['aigc_log_messages'] = []
                st.session_state['aigc_caption_file_path'] = caption_path
                st.session_state['aigc_tts_file_path'] = tts_path
                st.rerun()
        
        # Processing area
        if st.session_state.get('aigc_running', False):
            st.markdown("---")
            
            config = {
                'api_key': api_key, 'model': model, 'base_url': base_url,
                'max_tokens': max_tokens, 'temperature': temperature,
                'stream': stream_enabled, 'no_reasoning': no_reasoning,
                'num_variants': num_variants, 'variants_per_request': variants_per_request,
                'use_tts': use_tts
            }
            
            self.process_files(
                config, 
                st.session_state.get('aigc_caption_file_path'),
                st.session_state.get('aigc_tts_file_path')
            )
        
        # Footer
        st.markdown("---")
        st.markdown(f"*{tr('Tip: For best results, ensure your caption files contain clear, well-structured content with hashtags at the end.')}*")


# Initialize and run the application
if __name__ == "__main__" or True:  # Always run in Streamlit context
    app = AIGCRewriterPage()
    app.run()
