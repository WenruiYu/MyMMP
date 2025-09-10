chcp 65001
@echo off

set "CURRENT_DIR=%cd%"

set "FFMPEG_PATH=%CURRENT_DIR%\ffmpeg-6.1.1\bin"
set "PYTHON_PATH=%CURRENT_DIR%\python311"

REM Add CUDA libraries for FasterWhisper GPU acceleration
set "CUDA_PATH_312=C:\Users\plove\AppData\Local\Programs\Python\Python312\Lib\site-packages\nvidia"
set "CUDA_PATH_313=C:\Users\plove\AppData\Roaming\Python\Python313\site-packages\nvidia"

set "PATH=%FFMPEG_PATH%;%PYTHON_PATH%;%CUDA_PATH_312%\cublas\bin;%CUDA_PATH_312%\cudnn\bin;%CUDA_PATH_313%\cublas\bin;%CUDA_PATH_313%\cudnn\bin;%PATH%"

IF EXIST venv (
    echo venv dir exist
    call .\venv\Scripts\deactivate.bat

    call .\venv\Scripts\activate.bat
) ELSE (
    echo venv dir not exist
)

REM Check if the batch was started via double-click
IF /i "%%comspec%% /c %%~0 " equ "%%cmdcmdline:"=%%" (
    REM echo This script was started by double clicking.
    cmd /k streamlit run gui.py %*
) ELSE (
    REM echo This script was started from a command prompt.
    streamlit run gui.py %*
)

