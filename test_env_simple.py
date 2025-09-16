#!/usr/bin/env python3
"""
Simple test to verify environment variables are loaded
"""

import os
import re
from pathlib import Path

# Load .env file manually
try:
    from dotenv import load_dotenv
    project_root = Path(__file__).parent
    env_file = project_root / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Loaded environment variables from {env_file}")
    else:
        print("❌ .env file not found")
        exit(1)
except ImportError:
    print("❌ python-dotenv not installed")
    exit(1)

def substitute_env_vars(obj):
    """Substitute environment variables in a nested data structure"""
    if isinstance(obj, dict):
        return {key: substitute_env_vars(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [substitute_env_vars(item) for item in obj]
    elif isinstance(obj, str):
        def replace_var(match):
            var_name = match.group(1)
            return os.getenv(var_name, match.group(0))
        return re.sub(r'\$\{([^}]+)\}', replace_var, obj)
    else:
        return obj

# Test environment variables
test_vars = [
    'TENCENT_ACCESS_KEY_ID',
    'TENCENT_ACCESS_KEY_SECRET',
    'DEEPSEEK_API_KEY',
    'ALI_ACCESS_KEY_ID'
]

print("\n🔍 Testing Environment Variables:")
print("-" * 40)

all_set = True
for var in test_vars:
    value = os.getenv(var)
    if value:
        masked = value[:4] + "*" * (len(value) - 8) + value[-4:] if len(value) > 8 else "*" * len(value)
        print(f"✅ {var}: {masked}")
    else:
        print(f"❌ {var}: NOT SET")
        all_set = False

# Test substitution
print("\n🔄 Testing Variable Substitution:")
print("-" * 40)

test_config = {
    "tencent_key": "${TENCENT_ACCESS_KEY_ID}",
    "deepseek_key": "${DEEPSEEK_API_KEY}",
    "ali_key": "${ALI_ACCESS_KEY_ID}"
}

substituted = substitute_env_vars(test_config)

for key, value in substituted.items():
    if value.startswith('${'):
        print(f"❌ {key}: NOT SUBSTITUTED")
        all_set = False
    else:
        masked = value[:4] + "*" * (len(value) - 8) + value[-4:] if len(value) > 8 else "*" * len(value)
        print(f"✅ {key}: {masked}")

if all_set:
    print("\n🎉 All environment variables are working correctly!")
else:
    print("\n⚠️  Some environment variables are not working properly.")
