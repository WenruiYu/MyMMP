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
#  Website: [www.flydean.com](http://www.flydean.com)
#  GitHub: [https://github.com/ddean2009/MoneyPrinterPlus](https://github.com/ddean2009/MoneyPrinterPlus)
#
#  All rights reserved.
#
#

import os
import subprocess

import streamlit as st

from tools.file_utils import random_line_from_text_file, read_all_lines_from_text_file
from tools.utils import get_must_session_option, random_with_system_time, extent_audio, run_ffmpeg_command

# 获取当前脚本的绝对路径
script_path = os.path.abspath(__file__)

# print("当前脚本的绝对路径是:", script_path)

# 脚本所在的目录
script_dir = os.path.dirname(script_path)
# 音频输出目录
audio_output_dir = os.path.join(script_dir, "../../work")
audio_output_dir = os.path.abspath(audio_output_dir)


def get_session_video_scene_text():
    video_dir_list = []
    video_text_list = []
    if 'scene_number' not in st.session_state:
        st.session_state['scene_number'] = 0
    
    # Check if TTS is skipped
    skip_tts = st.session_state.get("skip_tts", False)
    
    # Get the single TTS text file path (only if TTS is not skipped)
    single_tts_text_file = None
    if not skip_tts:
        single_tts_text_file = st.session_state.get("tts_text_file", None)
    
    for i in range(int(st.session_state.get('scene_number'))+1):
        print("select video scene " + str(i + 1))
        if "video_scene_folder_" + str(i + 1) in st.session_state and st.session_state["video_scene_folder_" + str(i + 1)] is not None:
            video_dir_list.append(st.session_state["video_scene_folder_" + str(i + 1)])
            # Use the single TTS text file for all scenes (or None if TTS is skipped)
            video_text_list.append(single_tts_text_file)
    return video_dir_list, video_text_list


def get_video_scene_text_list(video_text_list, use_all_lines=True):
    """
    Process text files for each video scene.
    
    Args:
        video_text_list: List of text file paths for each scene (now all point to same file)
        use_all_lines: If True, use all lines from text file. If False, use random line (old behavior)
    
    Returns:
        List of text segments for each scene (each scene can have multiple segments)
    """
    video_scene_text_list = []
    
    # Check if we have a single text file for all scenes
    if video_text_list and all(text == video_text_list[0] for text in video_text_list):
        # All scenes use the same text file
        single_text_file = video_text_list[0]
        if single_text_file is not None and single_text_file != "":
            print(f"Processing single TTS text file for all {len(video_text_list)} scenes: {single_text_file}")
            if use_all_lines:
                # Read all lines and split long lines if needed
                all_segments = read_all_lines_from_text_file(single_text_file, max_char_per_line=150)
                
                # Distribute text segments across scenes
                if all_segments:
                    segments_per_scene = max(1, len(all_segments) // len(video_text_list))
                    remainder = len(all_segments) % len(video_text_list)
                    
                    start_idx = 0
                    for i in range(len(video_text_list)):
                        # Calculate how many segments this scene gets
                        scene_segment_count = segments_per_scene + (1 if i < remainder else 0)
                        
                        # Get segments for this scene
                        scene_segments = all_segments[start_idx:start_idx + scene_segment_count]
                        video_scene_text_list.append(scene_segments)
                        
                        start_idx += scene_segment_count
                else:
                    # No segments found, add empty lists
                    for _ in range(len(video_text_list)):
                        video_scene_text_list.append([])
            else:
                # Old behavior: random single line for each scene
                for _ in range(len(video_text_list)):
                    video_line = random_line_from_text_file(single_text_file)
                    video_scene_text_list.append([video_line] if video_line else [])
        else:
            # No text file provided, add empty lists
            for _ in range(len(video_text_list)):
                video_scene_text_list.append([])
    else:
        # Legacy behavior: different text files for each scene
        for i, video_text in enumerate(video_text_list):
            if video_text is not None and video_text != "":
                print(f"Processing video text file {i+1}/{len(video_text_list)}: {video_text}")
                if use_all_lines:
                    # Read all lines and split long lines if needed
                    text_segments = read_all_lines_from_text_file(video_text, max_char_per_line=150)
                    video_scene_text_list.append(text_segments)
                else:
                    # Old behavior: random single line
                    video_line = random_line_from_text_file(video_text)
                    video_scene_text_list.append([video_line] if video_line else [])
            else:
                video_scene_text_list.append([])
    
    return video_scene_text_list


def get_video_text_from_list(video_scene_text_list):
    """
    Combine text segments from all scenes into one string.
    
    Args:
        video_scene_text_list: List of text segments for each scene (can be nested list)
    """
    combined_text = []
    for scene_text in video_scene_text_list:
        if isinstance(scene_text, list):
            # Scene has multiple segments
            combined_text.extend(scene_text)
        elif scene_text:
            # Single text segment
            combined_text.append(scene_text)
    return " ".join(combined_text)


def get_audio_and_video_list(audio_service, audio_rate):
    audio_output_file_list = []
    video_dir_list, video_text_list = get_session_video_scene_text()
    
    # Check if TTS is skipped
    skip_tts = st.session_state.get("skip_tts", False)
    if skip_tts:
        # Return empty audio list and video list when TTS is skipped
        return audio_output_file_list, video_dir_list
    
    video_scene_text_list = get_video_scene_text_list(video_text_list, use_all_lines=True)  # Use all lines
    audio_voice = get_must_session_option("audio_voice", "请先设置配音语音")
    
    scene_idx = 0
    for scene_segments in video_scene_text_list:
        if scene_segments:  # If scene has text segments
            scene_audio_files = []  # Audio files for this scene
            
            # Generate audio for each segment in the scene
            for segment_idx, segment_text in enumerate(scene_segments):
                if segment_text:
                    temp_file_name = f"{random_with_system_time()}_{scene_idx}_{segment_idx}"
                    audio_output_file = os.path.join(audio_output_dir, f"{temp_file_name}.wav")
                    
                    # Try to generate audio
                    try:
                        print(f"  Generating audio for scene {scene_idx+1}, segment {segment_idx+1}/{len(scene_segments)}: {segment_text[:50]}...")
                        audio_service.save_with_ssml(segment_text,
                                                     audio_output_file,
                                                     audio_voice,
                                                     audio_rate)
                    except Exception as e:
                        st.error(f"音频生成失败: {str(e)}", icon="❌")
                        st.stop()
                    
                    # Check if audio file was actually created
                    if not os.path.exists(audio_output_file):
                        st.error(f"音频文件生成失败，可能是TTS服务问题（免费试用过期或配额用尽）", icon="❌")
                        st.info("请检查您的TTS服务配置或更换其他TTS服务提供商")
                        st.stop()
                    
                    # Check if audio file has content
                    if os.path.getsize(audio_output_file) == 0:
                        st.error(f"音频文件为空，TTS服务可能未正确生成内容", icon="❌")
                        st.stop()
                    
                    scene_audio_files.append(audio_output_file)
            
            # Concatenate all segments for this scene into one audio file
            if len(scene_audio_files) > 1:
                scene_output_file = os.path.join(audio_output_dir, f"{random_with_system_time()}_scene_{scene_idx}.wav")
                concat_audio_files_for_scene(scene_audio_files, scene_output_file)
                # Clean up segment files
                for segment_file in scene_audio_files:
                    if os.path.exists(segment_file):
                        os.remove(segment_file)
                final_scene_audio = scene_output_file
            else:
                final_scene_audio = scene_audio_files[0]
            
            # Extend audio for smoother transitions
            try:
                extent_audio(final_scene_audio, 1)
            except Exception as e:
                st.error(f"音频处理失败: {str(e)}", icon="❌")
                if os.path.exists(final_scene_audio):
                    os.remove(final_scene_audio)
                st.stop()
            
            audio_output_file_list.append(final_scene_audio)
        else:
            st.toast(f"场景 {scene_idx+1} 的配音文字为空", icon="⚠️")
            st.stop()
        
        scene_idx += 1

    return audio_output_file_list, video_dir_list


def get_audio_and_video_list_local(audio_service):
    audio_output_file_list = []
    video_dir_list, video_text_list = get_session_video_scene_text()
    
    # Check if TTS is skipped
    skip_tts = st.session_state.get("skip_tts", False)
    if skip_tts:
        # Return empty audio list and video list when TTS is skipped
        return audio_output_file_list, video_dir_list
    
    video_scene_text_list = get_video_scene_text_list(video_text_list, use_all_lines=True)  # Use all lines
    
    scene_idx = 0
    for scene_segments in video_scene_text_list:
        if scene_segments:  # If scene has text segments
            scene_audio_files = []  # Audio files for this scene
            
            # Generate audio for each segment in the scene
            for segment_idx, segment_text in enumerate(scene_segments):
                if segment_text:
                    temp_file_name = f"{random_with_system_time()}_{scene_idx}_{segment_idx}"
                    audio_output_file = os.path.join(audio_output_dir, f"{temp_file_name}.wav")
                    
                    # Try to generate audio
                    try:
                        print(f"  Generating local audio for scene {scene_idx+1}, segment {segment_idx+1}/{len(scene_segments)}: {segment_text[:50]}...")
                        audio_service.chat_with_content(segment_text, audio_output_file)
                    except Exception as e:
                        st.error(f"本地音频生成失败: {str(e)}", icon="❌")
                        st.stop()
                    
                    # Check if audio file was actually created
                    if not os.path.exists(audio_output_file):
                        st.error(f"音频文件生成失败，请检查本地TTS服务是否正常运行", icon="❌")
                        st.stop()
                    
                    # Check if audio file has content
                    if os.path.getsize(audio_output_file) == 0:
                        st.error(f"音频文件为空，本地TTS服务可能未正确生成内容", icon="❌")
                        st.stop()
                    
                    scene_audio_files.append(audio_output_file)
            
            # Concatenate all segments for this scene into one audio file
            if len(scene_audio_files) > 1:
                scene_output_file = os.path.join(audio_output_dir, f"{random_with_system_time()}_scene_{scene_idx}.wav")
                concat_audio_files_for_scene(scene_audio_files, scene_output_file)
                # Clean up segment files
                for segment_file in scene_audio_files:
                    if os.path.exists(segment_file):
                        os.remove(segment_file)
                final_scene_audio = scene_output_file
            else:
                final_scene_audio = scene_audio_files[0]
            
            # Extend audio for smoother transitions
            try:
                extent_audio(final_scene_audio, 1)
            except Exception as e:
                st.error(f"音频处理失败: {str(e)}", icon="❌")
                if os.path.exists(final_scene_audio):
                    os.remove(final_scene_audio)
                st.stop()
            
            audio_output_file_list.append(final_scene_audio)
        else:
            st.toast(f"场景 {scene_idx+1} 的配音文字为空", icon="⚠️")
            st.stop()
        
        scene_idx += 1
            
    return audio_output_file_list, video_dir_list


def concat_audio_files_for_scene(audio_files, output_file):
    """
    Concatenate multiple audio files for a single scene.
    
    Args:
        audio_files: List of audio file paths to concatenate
        output_file: Output file path for concatenated audio
    """
    if len(audio_files) == 1:
        # If only one file, just copy it
        import shutil
        shutil.copy(audio_files[0], output_file)
        return
    
    # Create a temporary file listing all audio files
    concat_list_file = os.path.join(audio_output_dir, f"concat_scene_{random_with_system_time()}.txt")
    with open(concat_list_file, 'w', encoding='utf-8') as f:
        for audio_file in audio_files:
            f.write(f"file '{os.path.abspath(audio_file)}'\n")
    
    # Use ffmpeg to concatenate
    command = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', concat_list_file,
        '-c', 'copy',
        output_file
    ]
    run_ffmpeg_command(command)
    
    # Clean up temporary file
    if os.path.exists(concat_list_file):
        os.remove(concat_list_file)
    
    print(f"  Concatenated {len(audio_files)} segments into {os.path.basename(output_file)}")


def get_video_text():
    # Check if TTS is skipped
    skip_tts = st.session_state.get("skip_tts", False)
    if skip_tts:
        # Return empty string when TTS is skipped
        return ""
    
    video_dir_list, video_text_list = get_session_video_scene_text()
    video_scene_text_list = get_video_scene_text_list(video_text_list, use_all_lines=True)  # Use all lines
    combined_text = get_video_text_from_list(video_scene_text_list)
    # Store combined text for subtitle generation
    st.session_state['combined_tts_text'] = combined_text
    return combined_text


def concat_audio_list(audio_output_file_list):
    temp_output_file_name = os.path.join(audio_output_dir, str(random_with_system_time()) + ".wav")
    concat_audio_file = os.path.join(audio_output_dir, "concat_audio_file.txt")
    with open(concat_audio_file, 'w', encoding='utf-8') as f:
        for audio_file in audio_output_file_list:
            f.write("file '{}'\n".format(os.path.abspath(audio_file)))
    # 调用ffmpeg来合并音频
    # 注意：这里假设ffmpeg在你的PATH中，否则你需要提供ffmpeg的完整路径
    command = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', concat_audio_file,
        '-c', 'copy',  # 如果可能，直接复制流而不是重新编码
        temp_output_file_name
    ]
    run_ffmpeg_command(command)
    # 完成后，删除临时文件（如果你不再需要它）
    os.remove(concat_audio_file)
    print(f"Audio files have been merged into {temp_output_file_name}")
    return temp_output_file_name

