@echo off
setlocal enabledelayedexpansion
echo Setting up minimal Python environment...
echo This should take less than 2 minutes on most systems.

:: Remove existing virtual environment
if exist venv (
    echo Removing existing virtual environment...
    rd /s /q venv
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Failed to remove existing virtual environment.
        goto :error
    )
)

:: Create a new virtual environment
echo Creating new virtual environment...
python -m venv venv
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] Failed to create virtual environment. Please check your Python installation.
    goto :error
)

:: Activate and install minimal requirements
echo Activating virtual environment and installing core requirements...
call venv\Scripts\activate
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] Failed to activate virtual environment.
    goto :error
)

:: Install only essential packages one by one with feedback
echo Installing requests...
pip install requests
if !ERRORLEVEL! NEQ 0 (
    echo [WARNING] Failed to install requests package.
)

echo Installing python-dotenv...
pip install python-dotenv
if !ERRORLEVEL! NEQ 0 (
    echo [WARNING] Failed to install python-dotenv package.
)

echo Installing httpx...
pip install httpx
if !ERRORLEVEL! NEQ 0 (
    echo [WARNING] Failed to install httpx package.
)

echo.
echo ===============================================
echo Basic environment setup complete!
echo.
echo To install additional packages gradually:
echo   run progressive_install.bat
echo.
echo To activate the virtual environment in PowerShell: .\venv\Scripts\Activate.ps1
echo To activate the virtual environment in Git Bash: source venv/Scripts\activate
echo ===============================================
echo.
goto :end

:error
echo.
echo [ERROR] Setup failed. Please check the error messages above.
echo.

:end
echo Press any key to exit...
pause > nul
endlocal
