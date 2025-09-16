# Environment Variables Setup Guide

This guide explains how to set up environment variables for MoneyPrinterPlus securely.

## 🚀 Quick Setup

### 1. Copy Environment Template
```bash
cp .env.example .env
```

### 2. Edit .env File
Open `.env` and fill in your actual API keys:
```bash
# Example .env file
ALI_ACCESS_KEY_ID=your_actual_ali_key_here
ALI_ACCESS_KEY_SECRET=your_actual_ali_secret_here
DEEPSEEK_API_KEY=sk-your-actual-deepseek-key-here
# ... add other keys
```

### 3. Load Environment Variables
Choose one of the methods below:

#### Option A: Automatic Loading (Recommended)
The application automatically loads `.env` files if they exist.

#### Option B: Manual Loading
```bash
# Linux/Mac
export $(cat .env | xargs)

# Windows PowerShell
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2])
    }
}
```

## 🔐 Security Best Practices

### ✅ What We Do Right
- API keys are stored in environment variables, not in code
- `.env` files are ignored by git (added to `.gitignore`)
- Configuration uses `${VAR_NAME}` syntax for substitution
- Fallback to placeholder values if environment variables are missing

### ⚠️ Important Security Notes
- **Never commit `.env` files** to version control
- **Share API keys privately** with team members
- **Use different keys for different environments** (dev/staging/prod)
- **Rotate keys regularly** for better security

## 📋 Required Environment Variables

### Audio Services

#### Ali (阿里云)
```bash
ALI_ACCESS_KEY_ID=your_access_key_id
ALI_ACCESS_KEY_SECRET=your_access_key_secret
ALI_APP_KEY=your_app_key
```

#### Tencent (腾讯云)
```bash
TENCENT_ACCESS_KEY_ID=your_access_key_id
TENCENT_ACCESS_KEY_SECRET=your_access_key_secret
TENCENT_APP_KEY=your_app_key
```

#### Azure (微软云)
```bash
AZURE_SERVICE_REGION=eastasia
AZURE_SPEECH_KEY=your_speech_key
```

### LLM Services

#### DeepSeek
```bash
DEEPSEEK_API_KEY=sk-your-deepseek-key
```

#### OpenAI
```bash
OPENAI_API_KEY=sk-your-openai-key
```

#### Moonshot
```bash
MOONSHOT_API_KEY=sk-your-moonshot-key
```

#### Baichuan
```bash
BAICHUAN_API_KEY=sk-your-baichuan-key
```

#### Qianfan (百度)
```bash
QIANFAN_API_KEY=your_qianfan_key
QIANFAN_SECRET_KEY=your_qianfan_secret
```

#### Tongyi (阿里云)
```bash
TONGYI_API_KEY=sk-your-tongyi-key
```

#### Azure OpenAI
```bash
AZURE_OPENAI_API_KEY=your_azure_openai_key
```

## 🔧 Configuration Details

### Environment Variable Substitution
The application uses `${VAR_NAME}` syntax in configuration files:
```yaml
# config.yml
llm:
  DeepSeek:
    api_key: ${DEEPSEEK_API_KEY}  # Will be replaced with env var value
```

### Fallback Behavior
If an environment variable is not set:
- The `${VAR_NAME}` placeholder remains unchanged
- Application may show errors or use default values
- Check logs for missing environment variable warnings

## 🛠️ Troubleshooting

### Check Environment Variables
```bash
# Linux/Mac
echo $DEEPSEEK_API_KEY

# Windows PowerShell
echo $env:DEEPSEEK_API_KEY
```

### Validate Configuration
```bash
# Test if config loads correctly
python -c "from MoneyPrinterPlus-windows.config.config import my_config; print('Config loaded successfully')"
```

### Debug Environment Loading
```python
import os
from MoneyPrinterPlus-windows.config.config import substitute_env_vars

# Test substitution
test_config = {"api_key": "${DEEPSEEK_API_KEY}"}
result = substitute_env_vars(test_config)
print(result)
```

## 📚 Additional Resources

- [python-dotenv documentation](https://pypi.org/project/python-dotenv/)
- [12 Factor App Config](https://12factor.net/config)
- [OWASP Environment Variables](https://owasp.org/www-project-web-security-testing-guide/v42/4-Web_Application_Security_Testing/11-Client-side_Testing/34-Testing_for_Client-side_URL_Redirect)

## 🎯 Best Practices Summary

1. ✅ **Use environment variables** for sensitive data
2. ✅ **Keep .env files out of version control**
3. ✅ **Use descriptive variable names**
4. ✅ **Document required variables**
5. ✅ **Test configuration loading**
6. ✅ **Share keys privately** with team members

---

**Remember**: Always treat API keys like passwords. Never commit them to version control! 🔐
