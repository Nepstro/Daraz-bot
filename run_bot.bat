@echo off
echo ==================================================
echo  Daraz Bot by Nepstro - Setup and Launch
echo ==================================================

REM Check if pip is installed
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pip is not found. Please ensure Python is installed and added to your PATH.
    pause
    exit /b 1
)

echo.
echo [+] Checking for required Python libraries...
pip install -r requirements.txt >nul 2>&1

echo [+] Libraries are up to date.
echo [+] Launching the bot...
echo.
REM The 'start' command launches the bot in a new, maximized window.
REM The '& pause' ensures the new window waits for a keypress after the script finishes.
start "Daraz Deep Search Bot" /max cmd /c "python Daraz_Bot_by_Nepstro.py & pause"
exit