@echo off
setlocal enabledelayedexpansion

echo FORCE CLEAN - Python Environment
echo ==============================
echo This will aggressively remove virtual environment with locked files
echo.

:: First try to kill any Python processes
echo Step 1: Terminating Python processes...
taskkill /F /IM python.exe /T 2> nul
taskkill /F /IM pythonw.exe /T 2> nul
taskkill /F /IM pip.exe /T 2> nul

:: Wait a moment for processes to terminate
timeout /t 2 /nobreak > nul

:: Check if venv exists
echo Step 2: Cleaning up virtual environment...
if not exist venv (
    echo No virtual environment found. Nothing to clean.
    goto :end
)

:: Try standard removal first
rd /s /q venv 2> nul

:: If that fails, get more aggressive with specific problematic files
if exist venv (
    echo Standard removal failed. Trying more aggressive cleanup...

    :: List of common locked files to delete individually 
    set "files_to_delete=python.exe pythonw.exe python3.dll python39.dll python310.dll pip.exe"
    
    for %%F in (%files_to_delete%) do (
        if exist venv\Scripts\%%F (
            echo Removing venv\Scripts\%%F...
            del /f /q venv\Scripts\%%F 2> nul
        )
    )
    
    :: Try to remove directories in stages
    if exist venv\Scripts rd /s /q venv\Scripts 2> nul
    if exist venv\Lib rd /s /q venv\Lib 2> nul
    if exist venv\Include rd /s /q venv\Include 2> nul
    
    :: Final attempt to remove venv
    rd /s /q venv 2> nul
    
    :: Check if venv still exists
    if exist venv (
        echo [WARNING] Could not fully remove virtual environment.
        echo Some files appear to be locked by another process.
        echo Please close all command prompts, terminals, and Python applications,
        echo then restart your computer before trying again.
    ) else (
        echo Successfully removed virtual environment.
    )
) else (
    echo Successfully removed virtual environment.
)

:end
echo.
echo Cleanup complete. You can now run very_quick_setup.bat to create a fresh environment.
echo.
echo Press any key to exit...
pause > nul
endlocal
