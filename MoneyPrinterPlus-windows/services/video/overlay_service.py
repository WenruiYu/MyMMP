#  Copyright © [2024] 程序那些事
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
#  Author: 程序那些事
#  email: flydean@163.com
#  Website: [www.flydean.com](http://www.flydean.com)
#  GitHub: [https://github.com/ddean2009/MoneyPrinterPlus](https://github.com/ddean2009/MoneyPrinterPlus)
#
#  All rights reserved.
#
#

import os
import random
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

import streamlit as st

from tools.file_utils import generate_temp_filename
from tools.utils import run_ffmpeg_command


class VideoOverlayService:
    """Service for applying image overlays to videos"""
    
    def __init__(self):
        self.enable_overlay = st.session_state.get("enable_video_overlay", False)
        self.overlay_mode = st.session_state.get("overlay_mode", "single")
        self.overlay_opacity = st.session_state.get("overlay_opacity", 1.0)
        self.overlay_image_path = st.session_state.get("overlay_image_path", None)
        self.overlay_folder_path = st.session_state.get("overlay_folder_path", None)
        
        # Cache for overlay images from folder
        self._overlay_images_cache = None
    
    def is_enabled(self) -> bool:
        """Check if overlay feature is enabled"""
        return self.enable_overlay
    
    def get_overlay_images_from_folder(self, folder_path: str) -> List[str]:
        """Get list of overlay images from folder"""
        if self._overlay_images_cache is not None:
            return self._overlay_images_cache
        
        overlay_images = []
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            # Support PNG and SVG files
            for ext in ['*.png', '*.PNG', '*.svg', '*.SVG']:
                overlay_images.extend(Path(folder_path).glob(ext))
            
            overlay_images = [str(img) for img in overlay_images]
            self._overlay_images_cache = overlay_images
        
        return overlay_images
    
    def get_overlay_for_video(self, video_index: int = 0) -> Optional[str]:
        """Get overlay image for a specific video"""
        if not self.enable_overlay:
            return None
        
        if self.overlay_mode == "single":
            # Single image mode
            if self.overlay_image_path and os.path.exists(self.overlay_image_path):
                return self.overlay_image_path
            else:
                print(f"Warning: Overlay image not found: {self.overlay_image_path}")
                return None
        else:
            # Folder mode - random selection
            if not self.overlay_folder_path:
                return None
            
            overlay_images = self.get_overlay_images_from_folder(self.overlay_folder_path)
            if overlay_images:
                # Use video index as seed for consistent random selection per video
                random.seed(video_index)
                selected = random.choice(overlay_images)
                # Reset random seed
                random.seed()
                return selected
            else:
                print(f"Warning: No overlay images found in folder: {self.overlay_folder_path}")
                return None
    
    def apply_overlay_to_video(self, video_path: str, output_path: str, video_index: int = 0) -> bool:
        """
        Apply overlay image to video using FFmpeg
        
        Args:
            video_path: Path to input video
            output_path: Path to output video
            video_index: Index of the video (used for random selection in folder mode)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enable_overlay:
            # If overlay is not enabled, just copy the video
            import shutil
            shutil.copy(video_path, output_path)
            return True
        
        overlay_image = self.get_overlay_for_video(video_index)
        if not overlay_image:
            # No overlay available, copy the video
            import shutil
            shutil.copy(video_path, output_path)
            return True
        
        try:
            # Get video dimensions first (needed for SVG conversion)
            probe_cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height',
                '-of', 'json',
                video_path
            ]
            import subprocess
            import json
            result = subprocess.run(probe_cmd, capture_output=True, text=True)
            probe_data = json.loads(result.stdout)
            video_width = probe_data['streams'][0]['width']
            video_height = probe_data['streams'][0]['height']
            
            # Check if overlay is SVG (needs conversion to PNG first)
            if overlay_image.lower().endswith('.svg'):
                # Convert SVG to PNG with transparency at video resolution
                temp_png = generate_temp_filename(overlay_image, ".png")
                svg_to_png_cmd = [
                    'ffmpeg',
                    '-i', overlay_image,
                    '-vf', f'scale={video_width}:{video_height},format=rgba',
                    '-y', temp_png
                ]
                run_ffmpeg_command(svg_to_png_cmd)
                overlay_image = temp_png
            
            # Build FFmpeg command for overlay
            # First scale the overlay to match video dimensions, then apply
            # scale2ref scales the overlay (input 1) to match the video (input 0) dimensions
            # Using lanczos scaling for better quality when scaling up or down
            if self.overlay_opacity < 1.0:
                # Scale overlay to video size, adjust opacity, then apply
                filter_complex = (
                    f"[1:v][0:v]scale2ref=iw:ih:flags=lanczos[overlay][video];"
                    f"[overlay]format=rgba,colorchannelmixer=aa={self.overlay_opacity}[ov];"
                    f"[video][ov]overlay=0:0:format=auto:alpha=premultiplied"
                )
            else:
                # Scale overlay to video size, then apply
                filter_complex = (
                    f"[1:v][0:v]scale2ref=iw:ih:flags=lanczos[overlay][video];"
                    f"[video][overlay]overlay=0:0:format=auto:alpha=premultiplied"
                )
            
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', video_path,       # Input video
                '-i', overlay_image,    # Overlay image
                '-filter_complex', filter_complex,
                '-c:v', 'libx264',      # Re-encode video
                '-preset', 'fast',      # Fast encoding
                '-crf', '23',           # Quality setting
                '-an',                  # Remove audio
                '-y', output_path       # Output file
            ]
            
            print(f"Applying overlay {os.path.basename(overlay_image)} to {os.path.basename(video_path)}")
            run_ffmpeg_command(ffmpeg_cmd)
            
            # Clean up temporary PNG if we converted from SVG
            if overlay_image != self.get_overlay_for_video(video_index) and os.path.exists(overlay_image):
                os.remove(overlay_image)
            
            return True
            
        except Exception as e:
            print(f"Error applying overlay: {str(e)}")
            # On error, copy the original video
            import shutil
            shutil.copy(video_path, output_path)
            return False
    
    def validate_overlay_settings(self) -> Tuple[bool, Optional[str]]:
        """
        Validate overlay settings
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.enable_overlay:
            return True, None
        
        if self.overlay_mode == "single":
            if not self.overlay_image_path:
                return False, "请设置叠加层图片路径 (Please set overlay image path)"
            if not os.path.exists(self.overlay_image_path):
                return False, f"叠加层图片不存在: {self.overlay_image_path} (Overlay image not found)"
            if not self.overlay_image_path.lower().endswith(('.png', '.svg')):
                return False, "叠加层图片必须是 PNG 或 SVG 格式 (Overlay must be PNG or SVG format)"
        else:
            if not self.overlay_folder_path:
                return False, "请设置叠加层图片文件夹路径 (Please set overlay images folder path)"
            if not os.path.exists(self.overlay_folder_path):
                return False, f"叠加层图片文件夹不存在: {self.overlay_folder_path} (Overlay folder not found)"
            if not os.path.isdir(self.overlay_folder_path):
                return False, f"路径不是文件夹: {self.overlay_folder_path} (Path is not a folder)"
            
            # Check if folder contains valid images
            overlay_images = self.get_overlay_images_from_folder(self.overlay_folder_path)
            if not overlay_images:
                return False, f"文件夹中没有找到 PNG 或 SVG 图片: {self.overlay_folder_path} (No PNG or SVG images found in folder)"
        
        return True, None
