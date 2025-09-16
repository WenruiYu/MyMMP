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

import subprocess
import re
import os
import platform


# fc-scan Songti.ttc | grep fullname

def get_font_fullname(font_path):
    try:
        # Run fc-scan and capture the output
        result = subprocess.run(['fc-scan', font_path], capture_output=True, text=True)

        # Check for errors
        if result.returncode != 0:
            print(result.stderr)
            return None

        # Use regex to find the fullname
        match = re.search(r'fullname: "(.*?)"', result.stdout)

        if match:
            return match.group(1)  # Return the extracted font name
        else:
            print("Font name not found in fc-scan output")
            return None

    except Exception as e:
        print(f"Error: {e}")
        return None


def get_font_name_windows(font_path):
    """Get font name on Windows using system calls or fallback methods"""
    try:
        # First try to extract font name using Windows registry or font APIs
        # For now, we'll use a mapping for known fonts
        filename = os.path.basename(font_path).lower()
        
        # Known font mappings
        font_mappings = {
            # Arial fonts
            'arial.ttf': 'Arial',
            'arialbd.ttf': 'Arial Bold',
            'arialbi.ttf': 'Arial Bold Italic',
            'ariali.ttf': 'Arial Italic',
            'ariblk.ttf': 'Arial Black',
            
            # Source Han Sans CN
            'sourcehansanscn-bold_0.ttf': 'Source Han Sans CN Bold',
            'sourcehansanscn-extralight_0.ttf': 'Source Han Sans CN ExtraLight',
            'sourcehansanscn-heavy_0.ttf': 'Source Han Sans CN Heavy',
            'sourcehansanscn-light_0.ttf': 'Source Han Sans CN Light',
            'sourcehansanscn-medium_0.ttf': 'Source Han Sans CN Medium',
            'sourcehansanscn-normal_0.ttf': 'Source Han Sans CN Normal',
            'sourcehansanscn-regular_0.ttf': 'Source Han Sans CN Regular',
            
            # Source Han Serif CN
            'sourcehanserifcn-bold.ttf': 'Source Han Serif CN Bold',
            'sourcehanserifcn-extralight.ttf': 'Source Han Serif CN ExtraLight',
            'sourcehanserifcn-heavy.ttf': 'Source Han Serif CN Heavy',
            'sourcehanserifcn-light.ttf': 'Source Han Serif CN Light',
            'sourcehanserifcn-medium.ttf': 'Source Han Serif CN Medium',
            'sourcehanserifcn-regular.ttf': 'Source Han Serif CN Regular',
            'sourcehanserifcn-semibold.ttf': 'Source Han Serif CN SemiBold',
        }
        
        # Check if we have a known mapping
        if filename in font_mappings:
            return font_mappings[filename]
        
        # For TTC files, extract font names differently
        if filename.endswith('.ttc'):
            if 'songti' in filename:
                # Return one of the Songti variants that was in the original list
                return 'Songti SC Regular'
            elif 'pingfang' in filename:
                # Return one of the PingFang variants that was in the original list
                return 'PingFang SC Regular'
        
        # Fallback: clean up the filename
        base_name = os.path.splitext(os.path.basename(font_path))[0]
        font_name = base_name.replace('_', ' ').replace('-', ' ')
        # Handle common patterns
        font_name = re.sub(r'([a-z])([A-Z])', r'\1 \2', font_name)
        font_name = re.sub(r'_\d+$', '', font_name)  # Remove trailing _0, _1, etc.
        
        return font_name.strip()
    except Exception as e:
        print(f"Error getting font name on Windows: {e}")
        return None


def get_all_fonts_from_directory(font_dir):
    """
    Load all fonts from a directory and return a dictionary of font paths and names.
    Supports both TTF and TTC font files.
    """
    font_map = {}
    
    if not os.path.exists(font_dir):
        print(f"Font directory does not exist: {font_dir}")
        return font_map
    
    # Supported font extensions
    font_extensions = ['.ttf', '.ttc', '.otf']
    
    for filename in os.listdir(font_dir):
        file_path = os.path.join(font_dir, filename)
        
        # Check if it's a file with a supported extension
        if os.path.isfile(file_path):
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext in font_extensions:
                # Try to get the font name
                font_name = None
                
                # Check if we're on Windows
                if platform.system() == 'Windows':
                    font_name = get_font_name_windows(file_path)
                else:
                    # Try using fc-scan for Linux/Mac
                    font_name = get_font_fullname(file_path)
                
                # If we couldn't get the font name, use the filename
                if not font_name:
                    font_name = os.path.splitext(filename)[0]
                
                # For TTC files, there might be multiple fonts inside
                # For now, we'll use the primary font name
                font_map[font_name] = file_path
                print(f"Loaded font: {font_name} from {filename}")
    
    return font_map


def get_font_list_for_ui(font_dir):
    """
    Get a list of font names suitable for use in a UI dropdown.
    Returns a sorted list of font names, including multiple fonts from TTC files.
    """
    font_names = []
    
    if not os.path.exists(font_dir):
        print(f"Font directory does not exist: {font_dir}")
        return ["Arial", "Times New Roman", "Courier New"]
    
    # Get all font files
    for filename in os.listdir(font_dir):
        file_path = os.path.join(font_dir, filename)
        
        if os.path.isfile(file_path):
            file_ext = os.path.splitext(filename)[1].lower()
            
            # Handle TTC files specially - they contain multiple fonts
            if file_ext == '.ttc':
                if 'songti' in filename.lower():
                    # Add all Songti variants from the original list
                    font_names.extend([
                        "Songti SC Bold",
                        "Songti SC Black", 
                        "Songti SC Light",
                        "STSong",
                        "Songti SC Regular"
                    ])
                elif 'pingfang' in filename.lower():
                    # Add all PingFang variants from the original list
                    font_names.extend([
                        "PingFang SC Regular",
                        "PingFang SC Medium",
                        "PingFang SC Semibold",
                        "PingFang SC Light",
                        "PingFang SC Thin",
                        "PingFang SC Ultralight"
                    ])
            elif file_ext in ['.ttf', '.otf']:
                # Get font name for TTF/OTF files
                if platform.system() == 'Windows':
                    font_name = get_font_name_windows(file_path)
                else:
                    font_name = get_font_fullname(file_path)
                
                if font_name:
                    font_names.append(font_name)
    
    # Remove duplicates and sort
    font_names = sorted(list(set(font_names)))
    
    # If no fonts found, return default options
    if not font_names:
        return ["Arial", "Times New Roman", "Courier New"]
    
    return font_names

