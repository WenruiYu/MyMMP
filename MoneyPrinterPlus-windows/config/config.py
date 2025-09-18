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
import shutil
import streamlit as st
import yaml
import re

from tools.file_utils import read_yaml, save_yaml

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env file from project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env_file = os.path.join(project_root, '.env')
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"✅ Loaded environment variables from {env_file}")
    else:
        print("⚠️  .env file not found, using system environment variables only")
except ImportError:
    print("⚠️  python-dotenv not installed, .env file will not be loaded automatically")
    print("   Install with: pip install python-dotenv")

app_title = "AI工具箱"

local_audio_tts_providers = ['chatTTS', 'GPTSoVITS']
local_audio_recognition_providers = ['fasterwhisper', ]
local_audio_recognition_fasterwhisper_module_names = ['large-v3', 'large-v2', 'large-v1', 'distil-large-v3',
                                                      'distil-large-v2', 'medium', 'base', 'small', 'tiny']
local_audio_recognition_fasterwhisper_device_types = ['cuda', 'cpu', 'auto']
local_audio_recognition_fasterwhisper_compute_types = ['int8', 'int8_float16', 'float16']

GPT_soVITS_languages = {
    "auto": "多语种混合",
    "all_zh": "中文",
    "all_yue": "粤语",
    "en": "英文",
    "all_ja": "日文",
    "all_ko": "韩文",
    "zh": "中英混合",
    "yue": "粤英混合",
    "ja": "日英混合",
    "ko": "韩英混合",
    "auto_yue": "多语种混合(粤语)",
}

audio_types = {'remote': "云服务", 'local': "本地模型"}
languages = {'zh-CN': "简体中文", 'en': "english", 'zh-TW': "繁體中文"}
audio_languages = {'zh-CN': "中文", 'en-US': "english"}
audio_voices_tencent = {
    "zh-CN": {
        "602003": "爱小悠(女)",  # Default voice - Best quality but only for text <150 chars
        "501001": "智兰(女)",     # Supports long text (>150 chars) and Chinese+English
        "501002": "智菊(女)",     # Supports long text (>150 chars) and Chinese+English
        "501004": "月华(女)",
        "502001": "智小柔(女)",
        "502003": "智小敏(女)",
        "502004": "智小满(女)",
        "501000": "智斌(男)",
        "501003": "智宇(男)",
        "501005": "飞镜(男)",
        "501006": "千嶂(男)",
        "501007": "浅草(男)",
        "502005": "智小解(男)",
        "502006": "智小悟(男)",
        "502007": "智小虎(童声)"
    },
    "en-US": {
        "501008": "WeJames(男)",  # Supports long text and English
        "501009": "WeWinny(女)"   # Supports long text and English
    }
}

audio_voices_azure = {
    "zh-CN": {
        "zh-CN-XiaoxiaoNeural": "晓晓(女)",
        "zh-CN-YunxiNeural": "云希(男)",
        "zh-CN-YunjianNeural": "云健(男)",
        "zh-CN-XiaoyiNeural": "晓伊(女)",
        "zh-CN-YunyangNeural": "云扬(男)",
        "zh-CN-XiaochenNeural": "晓晨(女)",
        "zh-CN-XiaohanNeural": "晓涵(女)",
        "zh-CN-XiaomengNeural": "晓萌(女)",
        "zh-CN-XiaomoNeural": "晓墨(女)",
        "zh-CN-XiaoqiuNeural": "晓秋(女)",
        "zh-CN-XiaoruiNeural": "晓睿(女)",
        "zh-CN-XiaoshuangNeural": "晓双(女,儿童)",
        "zh-CN-XiaoyanNeural": "晓颜(女)",
        "zh-CN-XiaoyouNeural": "晓悠(女,儿童)",
        "zh-CN-XiaozhenNeura": "晓珍(女)",
        "zh-CN-YunfengNeural": "云峰(男)",
        "zh-CN-YunhaoNeural": "云浩(男)",
        "zh-CN-YunxiaNeural": "云夏(男)",
        "zh-CN-YunyeNeural": "云野(男)",
        "zh-CN-YunzeNeural": "云泽(男)",
        "zh-CN-XiaochenMultilingualNeural": "晓晨(女),多语言",
        "zh-CN-XiaorouNeural": "晓蓉(女)",
        "zh-CN-XiaoxiaoDialectsNeural": "晓晓(女),方言",
        "zh-CN-XiaoxiaoMultilingualNeural": "晓晓(女),多语言",
        "zh-CN-XiaoyuMultilingualNeural": "晓雨(女),多语言",
        "zh-CN-YunjieNeural": "云杰(男)",
        "zh-CN-YunyiMultilingualNeural": "云逸(男),多语言"
    },
    "en-US": {
        "en-US-AvaMultilingualNeural": "Ava(female)",
        "en-US-AndrewNeural": "Andrew(male)",
        "en-US-EmmaNeural": "Emma(female)",
        "en-US-BrianNeural": "Brian(male)",
        "en-US-JennyNeural": "Jenny(female)",
        "en-US-GuyNeural": "Guy(male)",
        "en-US-AriaNeural": "Aria(female)",
        "en-US-DavisNeural": "Davis(male)",
        "en-US-JaneNeural": "Jane(female)",
        "en-US-JasonNeural": "Jason(male)",
        "en-US-SaraNeural": "Sara(female)",
        "en-US-TonyNeural": "Tony(male)",
        "en-US-NancyNeural": "Nancy(female)",
        "en-US-AmberNeural": "Amber(female)",
        "en-US-AnaNeural": "Ana(female),child",
        "en-US-AshleyNeural": "Ashley(female)",
        "en-US-BrandonNeural": "Brandon(male)",
        "en-US-ChristopherNeural": "Christopher(male)",
        "en-US-CoraNeural": "Cora(female)",
        "en-US-ElizabethNeural": "Elizabeth(female)",
        "en-US-EricNeural": "Eric(male)",
        "en-US-JacobNeural": "Jacob(male)",
        "en-US-JennyMultilingualNeural": "Jenny(female),multilingual",
        "en-US-MichelleNeural": "Michelle(female)",
        "en-US-MonicaNeural": "Monica(female)",
        "en-US-RogerNeural": "Roger(male)",
        "en-US-RyanMultilingualNeural": "Ryan(male),multilingual",
        "en-US-SteffanNeural": "Steffan(male)",
        "en-US-AndrewMultilingualNeura": "Andrew(male),multilingual",
        "en-US-BlueNeural": "Blue(neural)",
        "en-US-BrianMultilingualNeural": "Brian(male),multilingual",
        "en-US-EmmaMultilingualNeural": "Emma(female),multilingual",
        "en-US-AlloyMultilingualNeural": "Alloy(male),multilingual",
        "en-US-EchoMultilingualNeural": "Echo(male),multilingual",
        "en-US-FableMultilingualNeural": "Fable(neural),multilingual",
        "en-US-OnyxMultilingualNeural": "Onyx(male),multilingual",
        "en-US-NovaMultilingualNeural": "Nova(female),multilingual",
        "en-US-ShimmerMultilingualNeural": "Shimmer(female),multilingual",
    }
}

audio_voices_ali = {
    "zh-CN": {
        "zhixiaobai": "知小白(普通话女声)",
        "zhixiaoxia": "知小夏(普通话女声)",
        "zhixiaomei": "知小妹(普通话女声)",
        "zhigui": "知柜(普通话女声)",
        "zhishuo": "知硕(普通话男声)",
        "aixia": "艾夏(普通话女声)",
        "xiaoyun": "小云(标准女声)",
        "xiaogang": "小刚(标准男声)",
        "ruoxi": "若兮(温柔女声)",
        "siqi": "思琪(温柔女声)",
        "sijia": "思佳(标准女声)",
        "sicheng": "思诚(标准男声)",
        "aiqi": "艾琪(温柔女声)",
        "aijia": "艾佳(标准女声)",
        "aicheng": "艾诚(标准男声)",
        "aida": "艾达(标准男声)",
        "ninger": "宁儿(标准女声)",
        "ruilin": "瑞琳(标准女声)",
        "siyue": "思悦(温柔女声)",
        "aiya": "艾雅(严厉女声)",
        "aimei": "艾美(甜美女声)",
        "aiyu": "艾雨(自然女声)",
        "aiyue": "艾悦(温柔女声)",
        "aijing": "艾静(严厉女声)",
        "xiaomei": "小美(甜美女声)",
        "aina": "艾娜(浙普女声)",
        "yina": "依娜(浙普女声)",
        "sijing": "思婧(严厉女声)",
        "sitong": "思彤(儿童音)",
        "xiaobei": "小北(萝莉女声)",
        "aitong": "艾彤(儿童音)",
        "aiwei": "艾薇(萝莉女声)",
        "aibao": "艾宝(萝莉女声)"

    },
    "en-US": {
        "zhixiaobai": "知小白(普通话女声)",
        "zhixiaoxia": "知小夏(普通话女声)",
        "zhixiaomei": "知小妹(普通话女声)",
        "zhigui": "知柜(普通话女声)",
        "zhishuo": "知硕(普通话男声)",
        "aixia": "艾夏(普通话女声)",
        "cally": "Cally(美式英文女声)",
        "xiaoyun": "小云(标准女声)",
        "xiaogang": "小刚(标准男声)",
        "ruoxi": "若兮(温柔女声)",
        "siqi": "思琪(温柔女声)",
        "sijia": "思佳(标准女声)",
        "sicheng": "思诚(标准男声)",
        "aiqi": "艾琪(温柔女声)",
        "aijia": "艾佳(标准女声)",
        "aicheng": "艾诚(标准男声)",
        "aida": "艾达(标准男声)",
        "siyue": "思悦(温柔女声)",
        "aiya": "艾雅(严厉女声)",
        "aimei": "艾美(甜美女声)",
        "aiyu": "艾雨(自然女声)",
        "aiyue": "艾悦(温柔女声)",
        "aijing": "艾静(严厉女声)",
        "xiaomei": "小美(甜美女声)",
        "harry": "Harry(英音男声)",
        "abby": "Abby(美音女声)",
        "andy": "Andy(美音男声)",
        "eric": "Eric(英音男声)",
        "emily": "Emily(英音女声)",
        "luna": "Luna(英音女声)",
        "luca": "Luca(英音男声)",
        "wendy": "Wendy(英音女声)",
        "william": "William(英音男声)",
        "olivia": "Olivia(英音女声)"
    }
}

transition_types = ['xfade']
fade_list = ['fade', 'smoothleft', 'smoothright', 'smoothup', 'smoothdown', 'circlecrop', 'rectcrop', 'circleclose',
             'circleopen', 'horzclose', 'horzopen', 'vertclose',
             'vertopen', 'diagbl', 'diagbr', 'diagtl', 'diagtr', 'hlslice', 'hrslice', 'vuslice', 'vdslice', 'dissolve',
             'pixelize', 'radial', 'hblur',
             'wipetl', 'wipetr', 'wipebl', 'wipebr', 'zoomin', 'hlwind', 'hrwind', 'vuwind', 'vdwind', 'coverleft',
             'coverright', 'covertop', 'coverbottom', 'revealleft', 'revealright', 'revealup', 'revealdown']

driver_types = {
    "chrome": 'chrome',
    "firefox": 'firefox'}

douyin_site = "https://creator.douyin.com/creator-micro/content/upload"
shipinhao_site = "https://channels.weixin.qq.com/platform/post/create"
kuaishou_site = "https://cp.kuaishou.com/article/publish/video"
xiaohongshu_site = "https://creator.xiaohongshu.com/publish/publish?source=official"

# 获取当前脚本的绝对路径
script_path = os.path.abspath(__file__)

# print("当前脚本的绝对路径是:", script_path)

# 脚本所在的目录
script_dir = os.path.dirname(script_path)

config_example_file_name = "config.example.yml"
config_file_name = "config.yml"
session_file_name = "session.yml"

config_example_file = os.path.join(script_dir, config_example_file_name)
config_file = os.path.join(script_dir, config_file_name)
session_file = os.path.join(script_dir, session_file_name)
exclude_keys = ['01_first_visit', '02_first_visit', '03_first_visit', '04_first_visit','reference_audio','audio_temperature','audio_voice']


def save_session_state_to_yaml():
    # 创建一个字典副本，排除指定的键
    state_to_save = {key: value for key, value in st.session_state.items() if key not in exclude_keys}

    """将 Streamlit session_state 中的所有值保存到 YAML 文件"""
    with open(session_file, 'w') as file:
        yaml.dump(dict(state_to_save), file)


def delete_first_visit_session_state(first_visit):
    # 从session_state中删除其他first_vist标记
    for key in exclude_keys:
        if key != first_visit and key in st.session_state:
            del st.session_state[key]


def load_session_state_from_yaml(first_visit):
    delete_first_visit_session_state(first_visit)
    # 检查是否存在 "first_visit" 标志
    if first_visit not in st.session_state:
        # 第一次进入页面，设置标志为 True
        st.session_state[first_visit] = True
        """从 YAML 文件中读取数据并更新 session_state"""
        if os.path.exists(session_file):
            try:
                with open(session_file, 'r') as file:
                    data = yaml.safe_load(file)
                    for key, value in data.items():
                        st.session_state[key] = value
            except FileNotFoundError:
                st.warning(f"File {session_file} not found.")
    else:
        # 后续访问页面，标志设置为 False
        st.session_state[first_visit] = False


def substitute_env_vars(obj):
    """
    Recursively substitute environment variables in a nested data structure.
    Supports ${VAR_NAME} syntax.
    """
    if isinstance(obj, dict):
        return {key: substitute_env_vars(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [substitute_env_vars(item) for item in obj]
    elif isinstance(obj, str):
        # Replace ${VAR_NAME} with environment variable values
        def replace_var(match):
            var_name = match.group(1)
            return os.getenv(var_name, match.group(0))  # Keep original if env var not found

        return re.sub(r'\$\{([^}]+)\}', replace_var, obj)
    else:
        return obj

def load_config():
    print("load_config")
    # 加载配置文件
    if not os.path.exists(config_file):
        shutil.copy(config_example_file, config_file)
    if os.path.exists(config_file):
        config_data = read_yaml(config_file)
        # Substitute environment variables
        config_data = substitute_env_vars(config_data)
        return config_data


def test_config(todo_config, *args):
    temp_config = todo_config
    for arg in args:
        if arg not in temp_config:
            temp_config[arg] = {}
        temp_config = temp_config[arg]


def save_config():
    # 保存配置文件
    if os.path.exists(config_file):
        save_yaml(config_file, my_config)


my_config = load_config()

