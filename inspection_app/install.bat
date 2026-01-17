@echo off
echo ========================================
echo  Inspection App - Installation Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

echo Python found. Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo ========================================
echo  Installation Complete!
echo ========================================
echo.
echo The application will open in your web browser.
echo.
echo To configure:
echo 1. Go to Settings in the app
echo 2. Enter your Gemini API key
echo 3. Add your code book folders
echo 4. Upload Google credentials (optional, for export)
echo.
echo Run 'run.bat' to start the application.
echo.
pause
