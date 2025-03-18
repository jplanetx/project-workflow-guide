#!/bin/bash
# Bash script to activate virtual environment

VENV_PATH="./venv/Scripts/activate"

if [ -f "$VENV_PATH" ]; then
    echo "Activating Python virtual environment..."
    source "$VENV_PATH"
    echo "Virtual environment activated. You can now run your scripts."
else
    echo "Virtual environment not found. Please run clean_environment.bat first."
fi
