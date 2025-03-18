@echo off
setlocal

echo Forcefully terminating all Python processes...
echo This will close any running Python scripts and pip installations.
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause > nul

taskkill /F /IM python.exe /T
taskkill /F /IM pythonw.exe /T
taskkill /F /IM pip.exe /T

echo.
echo Checking for locked files in virtual environment...
echo.

:: Wait a moment for processes to fully terminate
timeout /t 2 /nobreak > nul

:: If venv exists, check if we can delete it to test permissions
if exist venv (
    echo Attempting to clean up locked virtual environment...
    
    :: Try to remove the Scripts directory first (often contains locked files)
    rd /s /q venv\Scripts 2> nul
    
    :: Attempt to remove specific problematic files if directory removal fails
    if exist venv\Scripts (
        if exist venv\Scripts\python.exe del /f venv\Scripts\python.exe 2> nul
        if exist venv\Scripts\pythonw.exe del /f venv\Scripts\pythonw.exe 2> nul
    )
    
    :: Final check - can we remove the entire venv?
    rd /s /q venv 2> nul
    
    if exist venv (
        echo [WARNING] Some files in the virtual environment may still be locked.
        echo Try closing all command prompts, terminals, and IDE windows,
        echo then restart your computer before running setup again.
    ) else (
        echo Virtual environment successfully cleaned up.
    )
)

echo.
echo All Python processes should now be terminated.
echo You can now run very_quick_setup.bat to create a fresh environment.
echo.
echo If you continue having permission issues, please restart your computer
echo and try again before running any Python commands.
echo.
pause

endlocal
