#!/usr/bin/env python3
"""
Environment Variables Validation Script
Run this script to validate that your environment variables are properly set up.
"""

import os
import sys
from pathlib import Path

# Add the project path to sys.path to import modules
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "MoneyPrinterPlus-windows"))

def check_environment_variable(var_name, description=""):
    """Check if an environment variable is set and print status."""
    value = os.getenv(var_name)
    if value:
        # Mask the value for security (show first 4 and last 4 characters)
        if len(value) > 8:
            masked_value = value[:4] + "*" * (len(value) - 8) + value[-4:]
        else:
            masked_value = "*" * len(value)
        print(f"✅ {var_name}: {masked_value} {description}")
        return True
    else:
        print(f"❌ {var_name}: NOT SET {description}")
        return False

def main():
    print("🔍 MoneyPrinterPlus Environment Variables Validation")
    print("=" * 60)
    print()

    # Required environment variables
    required_vars = [
        ("DEEPSEEK_API_KEY", "(Required for AIGC and LLM)"),
        ("ALI_ACCESS_KEY_ID", "(Ali audio service)"),
        ("ALI_ACCESS_KEY_SECRET", "(Ali audio service)"),
        ("ALI_APP_KEY", "(Ali audio service)"),
        ("TENCENT_ACCESS_KEY_ID", "(Tencent audio service)"),
        ("TENCENT_ACCESS_KEY_SECRET", "(Tencent audio service)"),
        ("TENCENT_APP_KEY", "(Tencent audio service)"),
    ]

    # Optional environment variables
    optional_vars = [
        ("AZURE_SERVICE_REGION", "(Azure audio service)"),
        ("AZURE_SPEECH_KEY", "(Azure audio service)"),
        ("OPENAI_API_KEY", "(OpenAI LLM service)"),
        ("MOONSHOT_API_KEY", "(Moonshot LLM service)"),
        ("BAICHUAN_API_KEY", "(Baichuan LLM service)"),
        ("QIANFAN_API_KEY", "(Qianfan LLM service)"),
        ("QIANFAN_SECRET_KEY", "(Qianfan LLM service)"),
        ("TONGYI_API_KEY", "(Tongyi LLM service)"),
        ("AZURE_OPENAI_API_KEY", "(Azure OpenAI service)"),
    ]

    print("📋 REQUIRED VARIABLES:")
    print("-" * 30)
    required_ok = 0
    for var_name, description in required_vars:
        if check_environment_variable(var_name, description):
            required_ok += 1

    print()
    print("📋 OPTIONAL VARIABLES:")
    print("-" * 30)
    optional_ok = 0
    for var_name, description in optional_vars:
        if check_environment_variable(var_name, description):
            optional_ok += 1

    print()
    print("📊 SUMMARY:")
    print("-" * 30)
    print(f"Required variables set: {required_ok}/{len(required_vars)}")
    print(f"Optional variables set: {optional_ok}/{len(optional_vars)}")

    if required_ok == len(required_vars):
        print("🎉 All required environment variables are configured!")
        print("✅ Your MoneyPrinterPlus should work correctly.")
    else:
        print("⚠️  Some required environment variables are missing.")
        print("❌ Please set the missing variables in your .env file.")
        print("📖 See ENVIRONMENT_SETUP.md for detailed instructions.")

    print()
    print("🔧 To reload environment variables:")
    print("   Linux/Mac: source .env")
    print("   Windows: Get-Content .env | ForEach-Object { if ($_ -match '^([^=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }")

    return required_ok == len(required_vars)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
