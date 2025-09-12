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

import json
import os
import platform
from typing import Optional

from config.config import my_config
from services.alinls.speech_process import AliRecognitionService
from services.audio.faster_whisper_recognition_service import FasterWhisperRecognitionService
from services.audio.tencent_recognition_service import TencentRecognitionService
from services.captioning.common_captioning_service import Captioning
import subprocess

from tools.file_utils import generate_temp_filename
import streamlit as st

from tools.utils import get_session_option

# 获取当前脚本的绝对路径
script_path = os.path.abspath(__file__)

# print("当前脚本的绝对路径是:", script_path)

# 脚本所在的目录
script_dir = os.path.dirname(script_path)

font_dir = os.path.join(script_dir, '../../fonts')
font_dir = os.path.abspath(font_dir)

# windows路径需要特殊处理
if platform.system() == "Windows":
    font_dir = font_dir.replace("\\", "\\\\\\\\")
    font_dir = font_dir.replace(":", "\\\\:")


def generate_caption_from_tts_text():
    """Generate subtitles directly from TTS text"""
    import os
    from tools.utils import get_session_option
    from services.video.video_service import get_audio_duration
    
    print("Generating subtitles from TTS text...")
    
    # Check if this is a mix video (multiple scenes)
    is_mix_video = st.session_state.get('is_mix_video', False)
    
    if is_mix_video:
        # For mix videos, combine all scene texts
        tts_text = st.session_state.get('combined_tts_text', '')
        if not tts_text:
            # Try to get from individual scene texts
            scene_texts = []
            i = 1
            while True:
                scene_text_key = f"video_scene_text_{i}"
                if scene_text_key in st.session_state:
                    scene_text = st.session_state[scene_text_key]
                    if scene_text:
                        scene_texts.append(scene_text)
                    i += 1
                else:
                    break
            tts_text = ' '.join(scene_texts)
    else:
        # For single videos, get from video_content
        tts_text = st.session_state.get('video_content', '')
    
    if not tts_text:
        print("WARNING: No TTS text found in session state")
        return
    
    # Get audio file to calculate duration
    audio_output_file = get_session_option("audio_output_file")
    if not audio_output_file or not os.path.exists(audio_output_file):
        print("WARNING: Audio file not found, using default timing")
        audio_duration = len(tts_text) * 0.1  # Rough estimate: 0.1 seconds per character
    else:
        audio_duration = get_audio_duration(audio_output_file)
    
    # Get output subtitle file path
    captioning_output = get_session_option("captioning_output")
    if not captioning_output:
        print("ERROR: No subtitle output file specified")
        return
    
    # Generate SRT subtitle file with proper timing
    generate_srt_from_text(tts_text, audio_duration, captioning_output)
    print(f"Subtitle file generated from TTS text: {captioning_output}")


def generate_srt_from_text(text, duration, output_file):
    """Generate SRT subtitle file from text with smart text splitting"""
    import re
    
    def format_time_srt(seconds):
        """Format time for SRT subtitle format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    # Split text into sentences or chunks for better subtitle display
    # Split by punctuation marks including commas for more natural breaks
    sentences = re.split(r'[.!?。！？,，;；:：]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # If no sentences after splitting, use the whole text
    if not sentences:
        sentences = [text]
    
    # Further split very long sentences into smaller chunks
    max_chars_per_subtitle = 80
    final_sentences = []
    for sentence in sentences:
        if len(sentence) > max_chars_per_subtitle:
            # Split by spaces into chunks
            words = sentence.split()
            current_chunk = []
            current_length = 0
            for word in words:
                if current_length + len(word) + 1 <= max_chars_per_subtitle:
                    current_chunk.append(word)
                    current_length += len(word) + 1
                else:
                    if current_chunk:
                        final_sentences.append(' '.join(current_chunk))
                    current_chunk = [word]
                    current_length = len(word)
            if current_chunk:
                final_sentences.append(' '.join(current_chunk))
        else:
            final_sentences.append(sentence)
    
    # Calculate time per subtitle based on character count for more natural timing
    total_chars = sum(len(s) for s in final_sentences)
    if total_chars == 0:
        return
    
    # Write SRT file
    with open(output_file, 'w', encoding='utf-8') as f:
        current_time = 0
        for i, sentence in enumerate(final_sentences):
            # Calculate duration for this subtitle based on its length
            sentence_duration = (len(sentence) / total_chars) * duration if total_chars > 0 else duration
            # Ensure minimum display time
            sentence_duration = max(sentence_duration, 1.0)  # At least 1 second
            
            # Subtitle number
            f.write(f"{i + 1}\n")
            
            # Start and end time
            start_time = current_time
            end_time = min(current_time + sentence_duration, duration)
            f.write(f"{format_time_srt(start_time)} --> {format_time_srt(end_time)}\n")
            
            # Subtitle text (split into multiple lines if needed)
            if len(sentence) > 45:  # Split long lines for better readability
                words = sentence.split()
                lines = []
                current_line = []
                for word in words:
                    current_line.append(word)
                    if len(' '.join(current_line)) > 40:
                        if len(lines) < 2:  # Max 2 lines per subtitle
                            lines.append(' '.join(current_line[:-1]))
                            current_line = [word]
                        else:
                            break
                if current_line and len(lines) < 2:
                    lines.append(' '.join(current_line))
                f.write('\n'.join(lines) + '\n')
            else:
                f.write(sentence + '\n')
            
            # Empty line between subtitles
            f.write('\n')
            
            # Update current time
            current_time = end_time


# 生成字幕
def generate_caption():
    # Check if we should use TTS text directly instead of voice recognition
    use_tts_text = st.session_state.get('use_tts_text_for_subtitles', False)
    
    if use_tts_text:
        # Use TTS text directly for subtitles
        generate_caption_from_tts_text()
        return
    
    captioning = Captioning()
    captioning.initialize()
    speech_recognizer_data = captioning.speech_recognizer_from_user_config()
    # print(speech_recognizer_data)
    recognition_type = st.session_state.get('recognition_audio_type')
    if recognition_type == "remote":
        selected_audio_provider = my_config['audio']['provider']
        if selected_audio_provider == 'Azure':
            print("selected_audio_provider: Azure")
            captioning.recognize_continuous(speech_recognizer=speech_recognizer_data["speech_recognizer"],
                                            format=speech_recognizer_data["audio_stream_format"],
                                            callback=speech_recognizer_data["pull_input_audio_stream_callback"],
                                            stream=speech_recognizer_data["pull_input_audio_stream"])
        if selected_audio_provider == 'Ali':
            print("selected_audio_provider: Ali")
            ali_service = AliRecognitionService()
            result_list = ali_service.process(get_session_option("audio_output_file"))
            captioning._offline_results = result_list
        if selected_audio_provider == 'Tencent':
            print("selected_audio_provider: Tencent")
            tencent_service = TencentRecognitionService()
            result_list = tencent_service.process(get_session_option("audio_output_file"),
                                                  get_session_option("audio_language"))
            if result_list is None:
                return
            captioning._offline_results = result_list
    if recognition_type == "local":
        selected_audio_provider = my_config['audio'].get('local_recognition',{}).get('provider','fasterwhisper')
        if selected_audio_provider =='fasterwhisper':
            print("selected_audio_provider: fasterwhisper")
            fasterwhisper_service = FasterWhisperRecognitionService()
            result_list = fasterwhisper_service.process(get_session_option("audio_output_file"),
                                                  get_session_option("audio_language"))
            print(result_list)
            if result_list is None:
                return
            captioning._offline_results = result_list

    captioning.finish()


# 添加字幕
def add_subtitles(video_file, subtitle_file, font_name='Songti TC Bold', font_size=12, primary_colour='#FFFFFF',
                  outline_colour='#FFFFFF', margin_v=16, margin_l=4, margin_r=4, border_style=1, outline=0, alignment=2,
                  shadow=0, spacing=2):
    output_file = generate_temp_filename(video_file)
    # Convert color from #RRGGBB to &HBBGGRR& format (ASS/SSA subtitle format)
    def convert_color(color):
        # Remove # and get RGB values
        rgb = color.lstrip('#')
        # Convert to BGR order and add ASS format
        return f"&H{rgb[4:6]}{rgb[2:4]}{rgb[0:2]}&"
    
    primary_colour = convert_color(primary_colour)
    outline_colour = convert_color(outline_colour)
    # windows路径需要特殊处理
    if platform.system() == "Windows":
        subtitle_file = subtitle_file.replace("\\", "\\\\\\\\")
        subtitle_file = subtitle_file.replace(":", "\\\\:")
    vf_text = f"subtitles={subtitle_file}:fontsdir={font_dir}:force_style='Fontname={font_name},Fontsize={font_size},Alignment={alignment},MarginV={margin_v},MarginL={margin_l},MarginR={margin_r},BorderStyle={border_style},Outline={outline},Shadow={shadow},PrimaryColour={primary_colour},OutlineColour={outline_colour},Spacing={spacing}'"
    
    # Debug output
    print(f"[DEBUG] Subtitle parameters:")
    print(f"  Font: {font_name}, Size: {font_size}")
    print(f"  Primary color: {primary_colour}")
    print(f"  Outline color: {outline_colour}")
    print(f"  Outline width: {outline}")
    print(f"  Border style: {border_style}")
    
    # 构建FFmpeg命令
    ffmpeg_cmd = [
        'ffmpeg',
        '-i', video_file,  # 输入视频文件
        '-vf', vf_text,  # 输入字幕文件
        '-y',
        output_file  # 输出文件
    ]
    print(" ".join(ffmpeg_cmd))
    # 调用ffmpeg
    subprocess.run(ffmpeg_cmd, check=True)
    # 重命名最终的文件
    if os.path.exists(output_file):
        os.remove(video_file)
        os.renames(output_file, video_file)
