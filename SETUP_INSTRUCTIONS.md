# Setup Instructions for MoneyPrinterPlus with AIGC

## 🚀 Quick Setup

### Windows
```bash
# Full setup (recommended for new installations)
setup.bat

# AIGC-only setup (if you already have MoneyPrinterPlus installed)
setup_aigc_only.bat
```

### Linux/Mac
```bash
# Make scripts executable (first time only)
chmod +x setup.sh setup_aigc_only.sh

# Full setup (recommended for new installations)
./setup.sh

# AIGC-only setup (if you already have MoneyPrinterPlus installed)  
./setup_aigc_only.sh
```

## 📋 What the Setup Does

### Full Setup (`setup.bat` / `setup.sh`)
1. ✅ **Creates virtual environment**
2. ✅ **Installs core dependencies** (FFmpeg, Python packages)
3. ✅ **Sets up MoneyPrinterPlus** functionality
4. ✅ **Installs AIGC dependencies** (OpenAI 1.40.0+, python-dotenv)
5. ✅ **Creates .env file** from template
6. ✅ **Tests AIGC integration**
7. ✅ **Provides next steps guidance**

### AIGC-Only Setup (`setup_aigc_only.bat` / `setup_aigc_only.sh`)
1. ✅ **Upgrades OpenAI package** to fix compatibility issues
2. ✅ **Installs python-dotenv** for environment variables
3. ✅ **Sets up .env file** if missing
4. ✅ **Tests AIGC functionality**
5. ✅ **Provides troubleshooting guidance**

## 🔧 Fixing the OpenAI Client Error

The error you encountered:
```
TypeError: Client.__init__() got an unexpected keyword argument 'proxies'
```

**Is automatically fixed by running either setup script**, which:
- ✅ Upgrades OpenAI package to version 1.40.0+
- ✅ Removes conflicting dependencies
- ✅ Tests the installation

## 📁 File Structure After Setup

```
MoneyPrinterPlus/
├── .env                           # Your API keys (created from template)
├── .env.example                   # Template file
├── setup.bat / setup.sh           # Full setup scripts
├── setup_aigc_only.bat/.sh        # AIGC-only setup scripts
├── setup_aigc.py                  # AIGC validation script
├── TROUBLESHOOTING_AIGC.md        # Troubleshooting guide
└── MoneyPrinterPlus-windows/
    ├── requirements.txt           # Updated with AIGC dependencies
    ├── pages/04_aigc_rewriter.py  # AIGC rewriter page
    └── services/aigc/             # AIGC service layer
```

## 🎯 Setup Scenarios

### Scenario 1: Fresh Installation
```bash
# Windows
setup.bat

# Linux/Mac  
./setup.sh
```

### Scenario 2: Existing Installation + AIGC Issues
```bash
# Windows
setup_aigc_only.bat

# Linux/Mac
./setup_aigc_only.sh
```

### Scenario 3: Manual Troubleshooting
```bash
# Test environment
python setup_aigc.py

# Update OpenAI manually
pip install --upgrade "openai>=1.40.0"

# Create .env file
cp .env.example .env
# Edit .env file with your API keys
```

## 🔑 Environment Variables Setup

After running setup, edit your `.env` file:

```bash
# Required for AIGC functionality
DEEPSEEK_API_KEY=sk-your-actual-deepseek-key-here

# Optional (for other services)
ALI_ACCESS_KEY_ID=your_ali_key
TENCENT_ACCESS_KEY_ID=your_tencent_key
OPENAI_API_KEY=sk-your-openai-key
# ... other keys as needed
```

## ✅ Verification

After setup, verify everything works:

1. **Start application:**
   ```bash
   # Windows
   start.bat
   
   # Linux/Mac
   ./start.sh
   ```

2. **Navigate to:** "AI Content Rewriter" in sidebar

3. **Test with small batch:**
   - Add file paths for TTS and Caption
   - Set variants to 2-3 for testing
   - Click "开始改写"

## 🆘 If Setup Fails

1. **Check Python version:** `python --version` (3.8+ required)
2. **Check virtual environment:** Ensure venv folder exists
3. **Run troubleshooting:** `python setup_aigc.py`
4. **Check logs:** Look for specific error messages
5. **Manual installation:** See TROUBLESHOOTING_AIGC.md

## 📞 Support

- **Documentation:** See TROUBLESHOOTING_AIGC.md
- **Environment setup:** See ENVIRONMENT_SETUP.md  
- **GitHub Issues:** Report problems with full error logs

---

**The setup scripts now automatically handle AIGC installation and the OpenAI client compatibility issue!** 🎯✨
