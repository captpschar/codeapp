@echo off
echo Starting Inspection App...
echo.
echo The application will open in your web browser at http://127.0.0.1:8080
echo.

REM Activate virtual environment
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Run install.bat first.
    pause
    exit /b 1
)

REM Run the application directly
python main.py

REM Keep window open if there was an error
if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)
