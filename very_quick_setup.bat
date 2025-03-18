@echo off
setlocal enabledelayedexpansion
echo Creating a minimal Python virtual environment...
echo This should take less than 30 seconds.

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

echo.
echo ===============================================
echo Virtual environment created successfully!
echo No packages have been installed yet.
echo.
echo To activate the virtual environment:
echo   - In PowerShell: .\venv\Scripts\Activate.ps1
echo   - In Command Prompt: venv\Scripts\activate.bat
echo   - In Git Bash: source venv/Scripts/activate
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
