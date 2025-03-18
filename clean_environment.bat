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

echo.
echo About to install packages from requirements.txt. This may take several minutes.
echo Some packages like matplotlib, pandas, and AI libraries require significant time to download and install.
echo.
echo Press Ctrl+C if you want to abort the installation process.
echo Press any key to continue with package installation...
pause

:: Install with verbose output to show progress
pip install -r requirements.txt -v

echo Environment setup complete!
echo.
echo To activate the virtual environment in PowerShell: .\venv\Scripts\Activate.ps1
echo To activate the virtual environment in Git Bash: source venv/Scripts/activate
echo.
pause
