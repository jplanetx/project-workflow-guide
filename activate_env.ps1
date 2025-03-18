# PowerShell script to activate virtual environment
$venvPath = Join-Path $PSScriptRoot "venv\Scripts\Activate.ps1"

if (Test-Path $venvPath) {
    Write-Host "Activating Python virtual environment..." -ForegroundColor Green
    & $venvPath
    Write-Host "Virtual environment activated. You can now run your scripts." -ForegroundColor Green
} else {
    Write-Host "Virtual environment not found. Please run clean_environment.bat first." -ForegroundColor Red
}
