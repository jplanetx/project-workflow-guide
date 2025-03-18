@echo off
echo Cleaning up Python environment...

:: Remove existing virtual environment
if exist venv (
    echo Removing existing virtual environment...
    rd /s /q venv
)

:: Create a new virtual environment
echo Creating new virtual environment...
python -m venv venv

:: Activate and install requirements
echo Activating virtual environment and installing requirements...
call venv\Scripts\activate
pip install -r requirements.txt

echo Environment setup complete!
echo.
echo To activate the virtual environment in PowerShell: .\venv\Scripts\Activate.ps1
echo To activate the virtual environment in Git Bash: source venv/Scripts/activate
echo.
pause
