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
import re
import string
import subprocess

import yaml
from PIL.Image import Image


def random_line(afile):
    lines = afile.readlines()
    if not lines:
        return ""
    return random.choice(lines)


def read_yaml(file_name):
    with open(file_name, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data


def save_yaml(file_name, data):
    with open(file_name, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True)


def is_chinese(char):
    if '\u4e00' <= char <= '\u9fff':
        return True
    else:
        return False


def split_at_first_chinese_char(s):
    for i, char in enumerate(s):
        # 检查字符是否是中文字符
        if '\u4e00' <= char <= '\u9fff':  # Unicode范围大致对应于常用中文字符
            return s[:i], s[i:]
    return s, ""  # 如果没有找到中文字符，返回原字符串和一个空字符串


def add_next_line_at_first_chinese_char(s):
    for i, char in enumerate(s):
        # 检查字符是否是中文字符
        if '\u4e00' <= char <= '\u9fff':  # Unicode范围大致对应于常用中文字符
            return s[:i] + "\n" + s[i:], max(len(s[:i]), len(s[i:]))
    return s, len(s)


def insert_newline(text):
    # 创建一个正则表达式，匹配任何标点符号
    punctuations = '[' + re.escape(string.punctuation) + ']'
    # 正则表达式匹配长度为30的字符串，后面紧跟空格或标点符号
    pattern = r'(.{30})(?=' + punctuations + r'|\s)'
    # 使用 re.sub 替换匹配的部分，在匹配到的字符串后添加换行符
    return re.sub(pattern, r'\1\n', text)


def generate_temp_filename(original_filepath, new_ext="", new_directory=None):
    # 获取文件的目录、文件名和扩展名
    directory, filename_with_ext = os.path.split(original_filepath)
    filename, ext = os.path.splitext(filename_with_ext)

    # 在文件名后添加.temp，但不改变扩展名
    if new_ext:
        new_filename = filename + '.temp' + new_ext
    else:
        new_filename = filename + '.temp' + ext

    # 如果你需要完整的路径，可以使用os.path.join
    if new_directory:
        new_filepath = os.path.join(new_directory, new_filename)
    else:
        new_filepath = os.path.join(directory, new_filename)

    return new_filepath


def get_file_extension(filename):
    _, ext = os.path.splitext(filename)
    # return ext[1:]  # 去掉前面的点（.）
    return ext


import requests


def download_file_from_url(url, output_path):
    """
    从给定的URL下载文件并保存到指定的输出路径。

    参数:
    url (str): 要下载的文件的URL。
    output_path (str): 保存文件的本地路径。

    返回:
    None
    """
    try:
        # 发送GET请求到URL
        response = requests.get(url, stream=True)

        # 检查请求是否成功
        if response.status_code == 200:
            # 打开一个文件以二进制写模式
            with open(output_path, 'wb') as file:
                # 使用chunk迭代数据
                for chunk in response.iter_content(chunk_size=8192):
                    # 写入文件
                    file.write(chunk)
            print(f"文件已成功下载到 {output_path}")
        else:
            print(f"请求失败，状态码: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"发生了一个错误: {e}")


def get_random_text_file_from_directory(directory_path):
    """从目录中随机选择一个文本文件"""
    text_extensions = ['.txt', '.text', '.md']
    text_files = []
    
    try:
        for file in os.listdir(directory_path):
            file_path = os.path.join(directory_path, file)
            if os.path.isfile(file_path):
                # Check if it's a text file
                if any(file.lower().endswith(ext) for ext in text_extensions):
                    text_files.append(file_path)
                # Also include files without extension that might be text
                elif '.' not in file:
                    text_files.append(file_path)
        
        if not text_files:
            print(f"WARNING: No text files found in directory: {directory_path}")
            return None
        
        selected_file = random.choice(text_files)
        print(f"  Selected random text file: {os.path.basename(selected_file)}")
        return selected_file
    except Exception as e:
        print(f"ERROR: Failed to list files in directory '{directory_path}': {e}")
        return None


def random_line_from_text_file(text_file):
    # 从文本文件中随机读取文本
    if not text_file:
        print(f"ERROR: Empty or None file path provided to random_line_from_text_file")
        return ""
    
    if not os.path.exists(text_file):
        print(f"ERROR: Path does not exist: '{text_file}'")
        print(f"  Current working directory: {os.getcwd()}")
        print(f"  Absolute path attempted: {os.path.abspath(text_file)}")
        return ""
    
    # Check if it's a directory
    if os.path.isdir(text_file):
        print(f"INFO: Path is a directory, selecting random text file from: {text_file}")
        selected_file = get_random_text_file_from_directory(text_file)
        if not selected_file:
            return ""
        text_file = selected_file
    
    # Now text_file should be a file path
    try:
        with open(text_file, 'r', encoding='utf-8') as file:
            line = random_line(file)
            if not line:
                print(f"WARNING: File is empty or has no valid lines: {text_file}")
            else:
                print(f"  Read line from: {os.path.basename(text_file)}")
            return line.strip()
    except Exception as e:
        print(f"ERROR: Failed to read file '{text_file}': {e}")
        print(f"  File exists: {os.path.exists(text_file)}")
        print(f"  File is readable: {os.access(text_file, os.R_OK) if os.path.exists(text_file) else False}")
        return ""


def read_head(file):
    if os.path.exists(file):
        with open(file, 'r', encoding='UTF-8') as file:
            # 读取文件内容
            head = file.readline()
            return head
    else:
        return ""


# 读取第一行之后 添加一个回车，适用于第一行是文章标题的情况
def read_file_with_extra_enter(file):
    with open(file, 'r', encoding='UTF-8') as f:
        # 读取文件内容
        content = f.read()
        # 使用splitlines()将内容分割成行列表
        lines = content.splitlines()
        # 检查列表是否为空，并且只处理第一行（如果存在）
        if lines:
            # 在第一行末尾添加换行符（如果它不存在）
            if not lines[0].endswith('\n'):
                lines[0] += '\n'
        # 使用join()将行重新组合成字符串
        cleaned_content = '\n'.join(lines)
        return cleaned_content


def read_all_lines_from_text_file(text_file, max_char_per_line=150):
    """
    Read all lines from a text file and split long lines if needed.
    
    Args:
        text_file: Path to the text file
        max_char_per_line: Maximum characters per line for TTS (default 150 for Tencent)
    
    Returns:
        List of text segments, each under max_char_per_line length
    """
    if not text_file:
        print(f"ERROR: Empty or None file path provided")
        return []
    
    if not os.path.exists(text_file):
        print(f"ERROR: Path does not exist: '{text_file}'")
        return []
    
    # Check if it's a directory
    if os.path.isdir(text_file):
        print(f"INFO: Path is a directory, selecting random text file from: {text_file}")
        selected_file = get_random_text_file_from_directory(text_file)
        if not selected_file:
            return []
        text_file = selected_file
    
    segments = []
    try:
        with open(text_file, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            
            if not lines:
                print(f"WARNING: File is empty: {text_file}")
                return []
            
            print(f"  Reading all lines from: {os.path.basename(text_file)}")
            print(f"  Total lines in file: {len(lines)}")
            
            for line in lines:
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                
                # If line is short enough, add it directly
                if len(line) < max_char_per_line:
                    segments.append(line)
                else:
                    # Split long lines into chunks
                    chunks = split_long_text(line, max_char_per_line)
                    segments.extend(chunks)
            
            print(f"  Total segments after processing: {len(segments)}")
            return segments
            
    except Exception as e:
        print(f"ERROR: Failed to read file '{text_file}': {e}")
        return []


def split_long_text(text, max_length=150):
    """
    Split long text into chunks under max_length, trying to break at punctuation.
    
    Args:
        text: Text to split
        max_length: Maximum length per chunk
    
    Returns:
        List of text chunks
    """
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    # Try to split by Chinese and English sentence endings
    sentences = re.split(r'([。！？；.!?;])', text)
    
    current_chunk = ""
    for i in range(0, len(sentences)):
        if i % 2 == 1 and i > 0:  # This is a punctuation mark
            # Add punctuation to previous sentence
            sentences[i-1] += sentences[i]
            continue
        
        sentence = sentences[i]
        if not sentence:
            continue
            
        # If adding this sentence exceeds max_length
        if len(current_chunk) + len(sentence) >= max_length:
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            # If the sentence itself is too long, split it further
            if len(sentence) >= max_length:
                # Split by commas and other delimiters
                sub_parts = re.split(r'([，,、：:])', sentence)
                sub_chunk = ""
                for j in range(0, len(sub_parts)):
                    if j % 2 == 1 and j > 0:  # This is a delimiter
                        sub_parts[j-1] += sub_parts[j]
                        continue
                    
                    part = sub_parts[j]
                    if not part:
                        continue
                    
                    if len(sub_chunk) + len(part) < max_length:
                        sub_chunk += part
                    else:
                        if sub_chunk:
                            chunks.append(sub_chunk.strip())
                        
                        # If part is still too long, hard split
                        if len(part) >= max_length:
                            while len(part) > 0:
                                chunks.append(part[:max_length-1].strip())
                                part = part[max_length-1:]
                        else:
                            sub_chunk = part
                
                if sub_chunk:
                    current_chunk = sub_chunk
                else:
                    current_chunk = ""
            else:
                current_chunk = sentence
        else:
            current_chunk += sentence
    
    # Add remaining chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks


def read_file(file):
    # 打开文件
    with open(file, 'r', encoding='UTF-8') as file:
        # 读取文件内容
        content = file.read()
        return content


def write_to_file(content, file_name):
    with open(file_name, 'w', encoding='UTF-8') as file:
        file.write(content)


def list_all_files(video_dir, extension='.mp4'):
    return_files = []
    for root, dirs, files in os.walk(video_dir):
        for file in files:
            if file.endswith(extension):
                return_files.append(os.path.join(root, file))
    return sorted(return_files)


def list_files(video_dir, extension='.mp4'):
    return_files = []
    for file in os.listdir(video_dir):
        if file.endswith(extension):
            return_files.append(os.path.join(video_dir, file))
    return sorted(return_files)


def convert_mp3_to_wav(input, output):
    # 构建ffmpeg命令
    cmd = [
        'ffmpeg',
        '-i', input,
        # '-ar', '44100',
        # '-ac', '2',
        output
    ]
    # 运行ffmpeg命令
    subprocess.run(cmd)


def save_uploaded_file(uploaded_file, save_path):
    # 假设你已经获取了文件内容
    file_content = uploaded_file.read()
    # 将文件内容写入到服务器的文件系统中
    with open(save_path, 'wb') as f:
        f.write(file_content)


def split_text(text, min_length):
    # 首先按照。！；拆分文本
    paragraph_segments = re.split(r'[。！？；.!?;]', text)

    merged_segments = []

    for paragraph in paragraph_segments:
        if paragraph:  # 确保段落非空
            # 然后按照空格、逗号、冒号拆分段落
            sub_segments = re.split(r'[ ，：,:]+', paragraph.strip())

            # 初始化变量，用于累积片段
            current_segment = ""
            for sub_segment in sub_segments:
                # 如果当前片段加上新片段的长度小于min_length，累积片段
                if len(current_segment) + len(sub_segment) < min_length:
                    current_segment += sub_segment
                else:
                    # 否则，如果当前片段非空，将其添加到结果列表
                    if current_segment:
                        merged_segments.append(current_segment)
                    # 开始新的片段
                    current_segment = sub_segment

            # 如果最后累积的片段非空，也添加到结果列表
            if current_segment:
                merged_segments.append(current_segment)

    return merged_segments
