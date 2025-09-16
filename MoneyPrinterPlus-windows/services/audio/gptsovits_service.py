﻿#  Copyright © [2024] Wenrui Yu
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

import requests
from pydub import AudioSegment
from pydub.playback import play

from config.config import my_config
from tools.file_utils import save_uploaded_file
from tools.utils import must_have_value, random_with_system_time
import streamlit as st

# 获取当前脚本的绝对路径
script_path = os.path.abspath(__file__)

# print("当前脚本的绝对路径是:", script_path)

# 脚本所在的目录
script_dir = os.path.dirname(script_path)

# 音频输出目录
audio_output_dir = os.path.join(script_dir, "../../work")
audio_output_dir = os.path.abspath(audio_output_dir)


class GPTSoVITSAudioService:
    def __init__(self):
        super().__init__()
        self.service_location = my_config['audio']['local_tts']['GPTSoVITS']['server_location']
        must_have_value(self.service_location, "请设置GPTSoVITS server location")
        self.service_location = self.service_location.rstrip('/') + '?'

        self.audio_temperature = st.session_state.get('audio_temperature')
        self.audio_top_p = st.session_state.get('audio_top_p')
        self.audio_top_k = int(st.session_state.get('audio_top_k'))

        audio_speed = st.session_state.get("audio_speed")
        if audio_speed == "normal":
            self.audio_speed = 1.0
        if audio_speed == "fast":
            self.audio_speed = 1.1
        if audio_speed == "slow":
            self.audio_speed = 0.9
        if audio_speed == "faster":
            self.audio_speed = 1.2
        if audio_speed == "slower":
            self.audio_speed = 0.8
        if audio_speed == "fastest":
            self.audio_speed = 1.3
        if audio_speed == "slowest":
            self.audio_speed = 0.7

        if st.session_state.get("use_reference_audio"):
            uploaded_file = st.session_state.get("reference_audio")
            if uploaded_file is not None:
                output_file_name = os.path.join(audio_output_dir, str(random_with_system_time())+uploaded_file.name)
                save_uploaded_file(uploaded_file, output_file_name)
                self.refer_wav_path=output_file_name
                self.prompt_text = st.session_state.get("reference_audio_text")
                self.prompt_language = st.session_state.get("reference_audio_language")

        self.text_language = st.session_state.get("inference_audio_language")

    def read_with_content(self, content):
        wav_file = os.path.join(audio_output_dir, str(random_with_system_time()) + ".wav")
        temp_file = self.chat_with_content(content, wav_file)
        # 读取音频文件
        audio = AudioSegment.from_file(temp_file)
        play(audio)

    def chat_with_content(self, content, audio_output_file):
        from tools.utils import preprocess_tts_text
        # Preprocess text to convert punctuation to newlines
        content = preprocess_tts_text(content)
        
        # main infer params
        if hasattr(self, 'refer_wav_path') and self.refer_wav_path:
            body = {
                "text": content,
                "refer_wav_path": self.refer_wav_path,
                "prompt_text": self.prompt_text,
                "prompt_language": self.prompt_language,
                "text_language": self.text_language,
                "top_k": self.audio_top_k,
                "top_p": self.audio_top_p,
                "temperature": self.audio_temperature,
                "speed": self.audio_speed,
            }
        else:
            body = {
                "text": content,
                "text_language": self.text_language,
                "top_k": self.audio_top_k,
                "top_p": self.audio_top_p,
                "temperature": self.audio_temperature,
                "speed": self.audio_speed,
            }

        print(body)

        try:
            response = requests.post(self.service_location, json=body)
            response.raise_for_status()
            # 读取响应内容
            content = response.content
            # 打开一个文件用于写入二进制数据
            with open(audio_output_file, 'wb') as file:
                file.write(content)  # 将响应内容写入文件
            print(f"文件已保存到 {audio_output_file}")
            return audio_output_file

        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")

