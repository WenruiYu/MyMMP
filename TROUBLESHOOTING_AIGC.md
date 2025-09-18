# AIGC Troubleshooting Guide

## Common Issues and Solutions

### 🔥 OpenAI Client Error: `TypeError: Client.__init__() got an unexpected keyword argument 'proxies'`

**Error Message:**
```
[STDERR] TypeError: Client.__init__() got an unexpected keyword argument 'proxies'
[STDERR] File "aigc\rewrite_tiktok_ds.py", line 286, in main
[STDERR] client = OpenAI(api_key=api_key, base_url=args.base_url)
```

**Root Cause:**
This error occurs due to OpenAI package version conflicts, usually caused by:
1. Outdated `openai` package version
2. Conflicting `langchain` packages that install older OpenAI versions
3. Mixed dependency versions in virtual environment

**Solutions:**

#### ✅ **Quick Fix (Recommended):**
```bash
# Update OpenAI package to latest version
pip install --upgrade openai>=1.35.0

# Remove conflicting packages
pip uninstall langchain langchain-openai langchain-community -y

# Reinstall if needed
pip install openai>=1.40.0
```

#### ✅ **Complete Environment Reset:**
```bash
# Create fresh virtual environment
python -m venv venv_new
venv_new\Scripts\activate  # Windows
# or: source venv_new/bin/activate  # Linux/Mac

# Install only required packages
pip install -r requirements.txt
```

#### ✅ **Automated Setup:**
```bash
# Run the setup script
python setup_aigc.py
```

### 🔧 Environment Variable Issues

**Error: `RuntimeError: 请先设置环境变量 DEEPSEEK_API_KEY`**

**Solutions:**
1. **Check .env file exists:**
   ```bash
   # Copy template if needed
   cp .env.example .env
   ```

2. **Edit .env file:**
   ```bash
   # Add your actual API key
   DEEPSEEK_API_KEY=sk-your-actual-key-here
   ```

3. **Verify environment loading:**
   ```bash
   python validate_env.py
   ```

### 📁 File Path Issues

**Error: `File not found` or `Invalid file path`**

**Common Causes:**
- File paths with spaces not properly quoted
- Network drive paths not accessible
- Permission issues

**Solutions:**
1. **Use quotes for paths with spaces:**
   ```
   "C:\Users\user name\Downloads\test\caption.txt"
   ```

2. **Use forward slashes or escaped backslashes:**
   ```
   C:/Users/user1/Downloads/test/caption.txt
   C:\\Users\\user1\\Downloads\\test\\caption.txt
   ```

3. **Check file permissions:**
   - Ensure files are not read-only
   - Verify directory write permissions

### 🌐 Network and Connectivity

**Error: Connection errors or timeout**

**Solutions:**
1. **Check internet connection**
2. **Verify API key is valid and has credits**
3. **Check firewall/proxy settings**
4. **Try different base URL if using custom endpoint**

### 🔄 Session State Issues

**Error: `StreamlitAPIException` or widget conflicts**

**Solutions:**
1. **Clear browser cache and refresh page**
2. **Restart Streamlit application:**
   ```bash
   # Stop current session (Ctrl+C)
   # Restart
   streamlit run MoneyPrinterPlus-windows/main.py
   ```

3. **Clear session state:**
   - Delete `MoneyPrinterPlus-windows/config/session.yml`
   - Restart application

### 📊 Performance Issues

**Issue: Slow processing or timeouts**

**Optimization Tips:**
1. **Reduce batch size:**
   - Use fewer variants per request (10-20 instead of 50)
   - Process in smaller batches

2. **Adjust timeout settings:**
   - Increase max_tokens if needed
   - Lower temperature for faster responses

3. **Use faster models:**
   - `deepseek-chat` is faster than `deepseek-reasoner`
   - Consider model trade-offs

### 🛠️ Development and Debugging

**Enable Debug Mode:**
```python
# Add to .env file
DEBUG=true

# Or set environment variable
export DEBUG=true  # Linux/Mac
set DEBUG=true     # Windows
```

**Check Service Status:**
```bash
# Test AIGC service
python MoneyPrinterPlus-windows/services/aigc/aigc_service.py

# Test configuration
python -c "from MoneyPrinterPlus-windows.config.config import my_config; print('Config loaded:', bool(my_config.get('aigc')))"

# Test TikTokRewriter directly
python aigc/rewrite_tiktok_ds.py --caption path/to/caption.txt --num 1
```

## 🆘 Getting Help

### Before Reporting Issues:
1. ✅ Run `python setup_aigc.py` to verify setup
2. ✅ Check this troubleshooting guide
3. ✅ Verify your .env file has correct API keys
4. ✅ Test with a simple 1-variant generation first

### When Reporting Issues:
Include:
- **Error message** (full traceback)
- **Python version** (`python --version`)
- **OpenAI package version** (`pip show openai`)
- **Operating system**
- **Input file examples** (if relevant)

### Common Commands for Debugging:
```bash
# Check package versions
pip list | grep openai
pip list | grep streamlit

# Test environment variables
python -c "import os; print('DEEPSEEK_API_KEY:', 'SET' if os.getenv('DEEPSEEK_API_KEY') else 'NOT SET')"

# Test file access
python -c "from pathlib import Path; print('File exists:', Path('your/file/path.txt').exists())"

# Check write permissions
python -c "import tempfile; print('Temp dir writable:', bool(tempfile.mkdtemp()))"
```

---

**Most issues are resolved by updating the OpenAI package and ensuring proper environment variable setup!** 🎯✨
