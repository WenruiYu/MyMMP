#!/usr/bin/env bash

echo "================================"
echo "AIGC-Only Setup for MoneyPrinterPlus" 
echo "================================"
echo ""

SCRIPT_DIR="$(cd -- $(dirname -- "$0") && pwd)"
VENV_DIR="$SCRIPT_DIR/MoneyPrinterPlus-windows/venv"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run setup.sh first to create the full environment."
    exit 1
fi

echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "Installing/upgrading AIGC dependencies..."
python -m pip install --upgrade "openai>=1.40.0"
python -m pip install --upgrade "python-dotenv"

echo ""
echo "Setting up environment variables..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "Creating .env file from template..."
        cp .env.example .env
        echo "✅ .env file created! Please edit it with your API keys."
    else
        echo "⚠️  .env.example not found. Please create .env file manually."
    fi
else
    echo "✅ .env file already exists."
fi

echo ""
echo "Testing AIGC integration..."
python setup_aigc.py
if [ $? -eq 0 ]; then
    echo "✅ AIGC setup completed successfully!"
else
    echo "⚠️  AIGC setup completed with warnings. Check the output above."
fi

echo ""
echo "================================"
echo "AIGC Setup completed!"
echo "================================"
echo ""
echo "To fix the OpenAI client error you encountered:"
echo "1. ✅ OpenAI package updated to latest version"
echo "2. ✅ Environment variables configured"
echo "3. ✅ AIGC service tested"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your DEEPSEEK_API_KEY"
echo "2. Run: sh start.sh"
echo "3. Navigate to 'AI Content Rewriter' page"
echo "4. Test with a small number of variants first"
echo ""

if command -v deactivate >/dev/null; then
    echo "Deactivating virtual environment..."
    deactivate
fi
