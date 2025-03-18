@echo off
setlocal enabledelayedexpansion
echo Checking Python environment...
echo.

:: Check if Python is installed
echo Testing Python installation...
python --version > nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH
    set error_found=1
) else (
    echo [OK] Python is installed
    python --version
)

:: Check if virtual environment exists
echo.
echo Checking virtual environment...
if exist venv (
    echo [OK] Virtual environment folder exists
) else (
    echo [ERROR] Virtual environment folder not found
    set error_found=1
    goto :summary
)

:: Try to activate virtual environment
echo.
echo Testing virtual environment activation...
call venv\Scripts\activate 2> nul
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] Failed to activate virtual environment
    set error_found=1
    goto :summary
) else (
    echo [OK] Virtual environment activated
)

:: Check if basic packages are installed
echo.
echo Checking for basic packages...
python -c "import requests" 2> nul
if !ERRORLEVEL! NEQ 0 (
    echo [NOT FOUND] requests package
    set packages_missing=1
) else (
    echo [OK] requests package
)

python -c "import dotenv" 2> nul
if !ERRORLEVEL! NEQ 0 (
    echo [NOT FOUND] python-dotenv package
    set packages_missing=1
) else (
    echo [OK] python-dotenv package
)

python -c "import httpx" 2> nul
if !ERRORLEVEL! NEQ 0 (
    echo [NOT FOUND] httpx package
    set packages_missing=1
) else (
    echo [OK] httpx package
)

:: Deactivate virtual environment
call deactivate

:summary
echo.
echo =============================================
echo ENVIRONMENT CHECK SUMMARY:

if "!error_found!"=="1" (
    echo [CRITICAL ISSUES FOUND] Some components of your environment are not working properly.
    echo Recommendation: Run very_quick_setup.bat to create a fresh virtual environment.
) else if "!packages_missing!"=="1" (
    echo [MINOR ISSUES FOUND] Your environment exists but some packages are missing.
    echo Recommendation: Run quick_setup.bat to install required packages.
) else (
    echo [ALL CHECKS PASSED] Your environment is set up correctly.
    echo You can now run your Python scripts within the virtual environment.
)
echo =============================================
echo.
echo Press any key to exit...
pause > nul
endlocal
