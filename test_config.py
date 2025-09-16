#!/usr/bin/env python3
"""
Test script to verify environment variable substitution in configuration
"""

import sys
from pathlib import Path

# Add MoneyPrinterPlus-windows to path
sys.path.insert(0, str(Path(__file__).parent / "MoneyPrinterPlus-windows"))

try:
    from config.config import my_config
    print("✅ Config loaded successfully")

    # Test Tencent API keys
    tencent_key = my_config['audio']['Tencent']['access_key_id']
    if tencent_key.startswith('AKIDD'):
        print("✅ TENCENT_ACCESS_KEY_ID substituted correctly")
        print(f"   Value: {tencent_key[:10]}...")
    else:
        print("❌ TENCENT_ACCESS_KEY_ID not substituted")
        print(f"   Value: {tencent_key}")

    # Test DeepSeek API key
    deepseek_key = my_config['llm']['DeepSeek']['api_key']
    if deepseek_key.startswith('sk-'):
        print("✅ DEEPSEEK_API_KEY substituted correctly")
        print(f"   Value: {deepseek_key[:10]}...")
    else:
        print("❌ DEEPSEEK_API_KEY not substituted")
        print(f"   Value: {deepseek_key}")

    # Test AIGC DeepSeek key
    aigc_key = my_config['aigc']['api_key']
    if aigc_key.startswith('sk-'):
        print("✅ AIGC DEEPSEEK_API_KEY substituted correctly")
        print(f"   Value: {aigc_key[:10]}...")
    else:
        print("❌ AIGC DEEPSEEK_API_KEY not substituted")
        print(f"   Value: {aigc_key}")

except Exception as e:
    print(f"❌ Error loading config: {e}")
    import traceback
    traceback.print_exc()
