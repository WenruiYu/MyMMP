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

import base64
import json
import os
import time
import types

from pydub import AudioSegment
from pydub.playback import play
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.tts.v20190823 import tts_client, models

from config.config import my_config
from services.audio.audio_service import AudioService
from tools.file_utils import download_file_from_url
from tools.utils import must_have_value, random_with_system_time

# 获取当前脚本的绝对路径
script_path = os.path.abspath(__file__)

# print("当前脚本的绝对路径是:", script_path)

# 脚本所在的目录
script_dir = os.path.dirname(script_path)
# 音频输出目录
audio_output_dir = os.path.join(script_dir, "../../work")
audio_output_dir = os.path.abspath(audio_output_dir)


class TencentAudioService(AudioService):
    # Valid Tencent voice types based on official documentation
    # https://cloud.tencent.com/document/product/1073/92668
    VALID_VOICE_TYPES = {
        # 实时语音合成音色 (Real-time synthesis voices)
        502001, 502003, 502004, 502005, 502006, 502007,  # 超自然大模型音色
        602003,  # 爱小悠
        501000, 501001, 501002, 501003, 501004, 501005, 501006, 501007,  # 大模型音色 中文
        501008, 501009,  # 大模型音色 英文
        601000, 601001, 601002, 601003, 601004, 601005, 601006, 601007,  # 大模型音色 情感
        601008, 601009, 601010, 601011, 601012, 601013, 601014, 601015,  # 大模型音色 更多
        601016, 601017, 601018, 601019, 601020,  # 大模型音色 更多
        
        # 精品音色
        301000, 301001, 301002, 301003, 301004, 301005, 301006, 301007,
        301008, 301009, 301010, 301011, 301012, 301013, 301014, 301015,
        301016, 301017, 301018, 301019, 301020, 301021, 301022, 301023,
        301024, 301025, 301026, 301027, 301028, 301029, 301030, 301031,
        301032, 301033, 301034, 301035, 301036, 301037, 301038, 301039,
        301040, 301041,
        
        # 标准音色
        10510000, 1001, 1002, 1003, 1004, 1005, 1008, 1009, 1010,
        1017, 1018, 1050, 1051,
        
        # 基础语音合成音色
        0, 1, 2, 5, 7, 1000, 1001, 1002, 1003, 1004, 1005, 1007, 1008, 1009,
        1010, 1015, 1016, 1017, 1018, 1019, 1020, 1021, 1022, 1025, 1026,
        1027, 1028, 1029, 1030, 1040, 1050, 1051, 1052, 1053, 1054, 1055,
        1056, 1057, 1058, 1059, 1060, 1061, 1062, 1063, 1064, 1065, 1066,
        1067, 1068, 1069, 1070, 1080, 100510000,
    }
    
    def __init__(self):
        super().__init__()
        self.TENCENT_ACCESS_AKID = my_config['audio'].get('Tencent', {}).get('access_key_id')
        self.TENCENT_ACCESS_AKKEY = my_config['audio'].get('Tencent', {}).get('access_key_secret')
        must_have_value(self.TENCENT_ACCESS_AKID, "请设置Tencent access key id")
        must_have_value(self.TENCENT_ACCESS_AKKEY, "请设置Tencent access key secret")
        self.endpoint = "tts.tencentcloudapi.com"

    def save_with_ssml(self, text, file_name, voice, rate="0.00"):
        from tools.utils import preprocess_tts_text
        # Preprocess text to convert punctuation to newlines
        text = preprocess_tts_text(text)
        
        # Validate and convert voice parameter
        try:
            # If voice is already an integer string, use it directly
            if isinstance(voice, str) and voice.isdigit():
                voice_type = int(voice)
            # If voice is an integer, use it directly
            elif isinstance(voice, int):
                voice_type = voice
            else:
                # Try to extract numeric part from voice string
                import re
                match = re.search(r'\d+', str(voice))
                if match:
                    voice_type = int(match.group())
                else:
                    print(f"WARNING: Invalid voice type '{voice}', using default voice 602003")
                    voice_type = 602003  # Default to 爱小悠(女)
            
            # Validate that the voice type is supported
            if voice_type not in self.VALID_VOICE_TYPES:
                print(f"WARNING: Voice type {voice_type} may not be supported by Tencent TTS")
                print(f"Valid voice types: {sorted(self.VALID_VOICE_TYPES)}")
                # Don't change it, let the API handle the error
                
        except Exception as e:
            print(f"ERROR: Failed to parse voice type '{voice}': {e}, using default")
            voice_type = 602003  # Default to 爱小悠(女)
        
        cred = credential.Credential(self.TENCENT_ACCESS_AKID, self.TENCENT_ACCESS_AKKEY)
        # 实例化一个http选项，可选的，没有特殊需求可以跳过
        httpProfile = HttpProfile()
        httpProfile.endpoint = self.endpoint

        # 实例化一个client选项，可选的，没有特殊需求可以跳过
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        # 实例化要请求产品的client对象,clientProfile是可选的
        client = tts_client.TtsClient(cred, "ap-beijing", clientProfile)

        # 返回的resp是一个TextToVoiceResponse的实例，与请求对象对应
        # Tencent TTS uses 150 characters as the threshold for long text
        # Short text (<150 chars) uses TextToVoice API
        # Long text (>=150 chars) uses CreateTtsTask API
        if len(text) < 150:
            # 实例化一个请求对象,每个接口都会对应一个request对象
            req = models.TextToVoiceRequest()
            params = {
                "Text": text,
                "SessionId": str(random_with_system_time()),
                "Codec": "wav",
                "VoiceType": voice_type,
                "Speed": float(rate)

            }
            req.from_json_string(json.dumps(params))
            try:
                resp = client.TextToVoice(req)
            except Exception as e:
                if "VoiceType" in str(e):
                    print(f"ERROR: Voice type {voice_type} not supported, trying default voice 602003")
                    params["VoiceType"] = 602003
                    req.from_json_string(json.dumps(params))
                    resp = client.TextToVoice(req)
                else:
                    raise
            # 输出json格式的字符串回包
            # print(resp.to_json_string())
            # 使用base64库解码字符串
            decoded_audio_data = base64.b64decode(resp.Audio)
            # 写入WAV文件
            print("腾讯语音合成任务成功")
            with open(file_name, 'wb') as wav_file:
                wav_file.write(decoded_audio_data)
        else:
            # 使用腾讯长文本语音合成
            # 实例化一个请求对象,每个接口都会对应一个request对象
            req = models.CreateTtsTaskRequest()
            params = {
                "Text": text,
                "SessionId": str(random_with_system_time()),
                "Codec": "wav",
                "VoiceType": voice_type,
                "Speed": float(rate)
            }
            req.from_json_string(json.dumps(params))
            # 返回的resp是一个CreateTtsTaskResponse的实例，与请求对象对应
            try:
                resp = client.CreateTtsTask(req)
            except Exception as e:
                if "VoiceType" in str(e):
                    # For long text, we need a voice that supports long text synthesis
                    # 602003 (爱小悠) doesn't support long text API (>150 chars)
                    # We need to choose a fallback voice based on content
                    
                    import re
                    # Count language characters
                    english_chars = len(re.findall(r'[a-zA-Z]', text))
                    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
                    total_chars = len(text)
                    
                    # Calculate language ratios
                    english_ratio = (english_chars / total_chars) if total_chars > 0 else 0
                    chinese_ratio = (chinese_chars / total_chars) if total_chars > 0 else 0
                    
                    print(f"Text analysis: Length={len(text)}, English={english_ratio:.1%}, Chinese={chinese_ratio:.1%}")
                    
                    # Choose fallback voice based on content
                    # 501001 (智兰) is the best alternative that supports both Chinese and English
                    # Only use English-specific voices if text is >70% English
                    if english_ratio > 0.7 and chinese_ratio < 0.1:
                        # Mostly pure English, use English voice
                        print(f"Voice {voice_type} not supported for long text. Using 501008 (WeJames) for English content")
                        params["VoiceType"] = 501008
                    else:
                        # Chinese, mixed content, or moderate English - use 501001 which handles both well
                        print(f"Voice {voice_type} not supported for long text (>150 chars).")
                        print(f"Using voice 501001 (智兰) - supports both Chinese and English")
                        params["VoiceType"] = 501001
                    req.from_json_string(json.dumps(params))
                    resp = client.CreateTtsTask(req)
                else:
                    raise
            # 输出json格式的字符串回包
            print(resp.to_json_string())
            long_tts_request_id = resp.RequestId
            long_tts_request_task = resp.Data.TaskId
            time.sleep(2)
            # 查询结果
            while True:
                # 实例化一个请求对象,每个接口都会对应一个request对象
                req = models.DescribeTtsTaskStatusRequest()
                params = {
                    "TaskId": long_tts_request_task
                }
                req.from_json_string(json.dumps(params))
                # 返回的resp是一个DescribeTtsTaskStatusResponse的实例，与请求对象对应
                resp = client.DescribeTtsTaskStatus(req)
                # 输出json格式的字符串回包
                # print(resp.to_json_string())
                # Status: 任务状态码，0：任务等待，1：任务执行中，2：任务成功，3：任务失败。
                if resp.Data.Status == 0:
                    print("腾讯语音合成任务等待中...")
                    time.sleep(2)
                    continue
                elif resp.Data.Status == 1:
                    print("腾讯语音合成任务执行中...")
                    time.sleep(2)
                    continue
                elif resp.Data.Status == 2:
                    print("腾讯语音合成任务成功")
                    result_url = resp.Data.ResultUrl
                    if result_url:
                        download_file_from_url(result_url, file_name)
                    break
                elif resp.Data.Status == 3:
                    print("腾讯语音合成任务失败")
                    break

    def read_with_ssml(self, text, voice, rate="0.00"):
        temp_file = os.path.join(audio_output_dir, "temp.wav")
        try:
            self.save_with_ssml(text, temp_file, voice, rate)
            # Check if file was created successfully
            if not os.path.exists(temp_file):
                print("ERROR: Audio file was not created")
                return
            # 读取音频文件
            audio = AudioSegment.from_file(temp_file)
            # 剪辑音频（例如，剪辑前5秒）
            # audio_snippet = audio[:5000]
            # 播放剪辑后的音频
            play(audio)
        except Exception as e:
            print(f"ERROR in read_with_ssml: {e}")
            import streamlit as st
            st.error(f"腾讯语音测试失败: {str(e)}")


if __name__ == '__main__':
    service = TencentAudioService()
    service.save_with_ssml("你好", "/tmp/temp.wav", 602003)
