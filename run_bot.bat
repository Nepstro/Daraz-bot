@echo off
title Daraz Bot Launcher

echo ======================================================
echo  Daraz Bot Launcher
echo ======================================================
echo.
echo This script will automatically install the required
echo Python libraries and then start the bot.
echo.

REM Navigate to the script's directory, so it can be run from anywhere
cd /d "%~dp0"

echo [+] Installing/Verifying required libraries from requirements.txt...
pip install -r requirements.txt > nul 2>&1

echo [+] Libraries are up to date. Launching the Daraz Bot...
echo.

python Daraz_Bot_by_Nepstro.py

echo.
echo ======================================================
echo  The bot has finished or been closed. Press any key to exit.
echo ======================================================
pause