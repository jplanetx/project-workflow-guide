@echo off
echo Progressive Python Package Installation
echo =====================================
echo.

call venv\Scripts\activate || (
    echo Virtual environment not found. Please run quick_setup.bat first.
    pause
    exit /b 1
)

echo Installing packages in stages...
echo.

echo STAGE 1: Essential packages
pip install requests python-dotenv httpx --timeout 60
echo.
echo Stage 1 complete! Press any key to continue to Stage 2 or Ctrl+C to stop here.
pause

echo STAGE 2: AI tokenization and async tools
pip install asyncio tiktoken --timeout 60
echo.
echo Stage 2 complete! Press any key to continue to Stage 3 or Ctrl+C to stop here.
pause

echo STAGE 3: AI API libraries
pip install openai --timeout 60
pip install anthropic --timeout 60
echo.
echo Stage 3 complete! Press any key to continue to Stage 4 or Ctrl+C to stop here.
pause

echo STAGE 4: Data science packages (will take longest)
echo Installing matplotlib (this may take several minutes)...
pip install matplotlib --timeout 120
echo Installing pandas (this may take several minutes)...
pip install pandas --timeout 120
pip install python-dateutil --timeout 60
echo.

echo All packages have been installed successfully!
echo.
pause
