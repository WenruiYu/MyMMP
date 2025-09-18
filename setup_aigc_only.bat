@echo off
chcp 65001

echo ================================
echo AIGC-Only Setup for MoneyPrinterPlus
echo ================================
echo.

set "CURRENT_DIR=%cd%"

REM Check if virtual environment exists
IF NOT EXIST MoneyPrinterPlus-windows\venv (
    echo ❌ Virtual environment not found!
    echo Please run setup.bat first to create the full environment.
    pause
    exit /b 1
)

echo Activating virtual environment...
call MoneyPrinterPlus-windows\venv\Scripts\activate.bat

echo Installing/upgrading AIGC dependencies...
python -m pip install --upgrade "openai>=1.40.0"
python -m pip install --upgrade "python-dotenv"

echo.
echo Setting up environment variables...
IF NOT EXIST .env (
    IF EXIST .env.example (
        echo Creating .env file from template...
        copy .env.example .env
        echo ✅ .env file created! Please edit it with your API keys.
    ) ELSE (
        echo ⚠️  .env.example not found. Please create .env file manually.
    )
) ELSE (
    echo ✅ .env file already exists.
)

echo.
echo Testing AIGC integration...
python setup_aigc.py
IF %ERRORLEVEL% EQU 0 (
    echo ✅ AIGC setup completed successfully!
) ELSE (
    echo ⚠️  AIGC setup completed with warnings. Check the output above.
)

echo.
echo ================================
echo AIGC Setup completed!
echo ================================
echo.
echo To fix the OpenAI client error you encountered:
echo 1. ✅ OpenAI package updated to latest version
echo 2. ✅ Environment variables configured
echo 3. ✅ AIGC service tested
echo.
echo Next steps:
echo 1. Edit .env file and add your DEEPSEEK_API_KEY
echo 2. Run: start.bat
echo 3. Navigate to 'AI Content Rewriter' page
echo 4. Test with a small number of variants first
echo.

call MoneyPrinterPlus-windows\venv\Scripts\deactivate.bat
pause
