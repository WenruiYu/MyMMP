chcp 65001
@echo off

set "CURRENT_DIR=%cd%"

set "FFMPEG_PATH=%CURRENT_DIR%\ffmpeg-6.1.1\bin"
set "PYTHON_PATH=%CURRENT_DIR%\python311"

set "PATH=%FFMPEG_PATH%;%PYTHON_PATH%;%PATH%"


python.exe -m venv venv
IF NOT EXIST venv (
    echo Creating venv...
    python.exe -m venv venv
)

call .\venv\Scripts\deactivate.bat

call .\venv\Scripts\activate.bat

REM first make sure we have setuptools available in the venv    
python.exe -m pip install --require-virtualenv --no-input -q -q  setuptools

REM Check if the batch was started via double-click
IF /i "%%comspec%% /c %%~0 " equ "%%cmdcmdline:"=%%" (
    REM echo This script was started by double clicking.
    cmd /k python.exe .\setup\setup_windows.py
) ELSE (
    REM echo This script was started from a command prompt.
    python.exe .\setup\setup_windows.py %*
)

REM Setup AIGC functionality
echo.
echo ================================
echo Setting up AIGC functionality...
echo ================================

REM Install/upgrade OpenAI package for AIGC compatibility
echo Installing OpenAI package for AIGC...
python.exe -m pip install --upgrade "openai>=1.40.0"

REM Setup environment variables
echo Setting up environment variables...
cd ..
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

REM Test AIGC setup
echo Testing AIGC integration...
python setup_aigc.py
IF %ERRORLEVEL% EQU 0 (
    echo ✅ AIGC setup completed successfully!
) ELSE (
    echo ⚠️  AIGC setup completed with warnings. Check the output above.
)

cd MoneyPrinterPlus-windows

echo.
echo ================================
echo Setup completed!
echo ================================
echo.
echo Next steps:
echo 1. Edit .env file with your API keys
echo 2. Run: start.bat
echo 3. Navigate to 'AI Content Rewriter' page
echo.

:: Deactivate the virtual environment
call .\venv\Scripts\deactivate.bat