@echo off
echo Fixing Python Environment...

:: Check if venv exists and delete it
if exist venv (
    echo Removing broken virtual environment...
    rmdir /s /q venv
)

echo Creating new virtual environment...
python -m venv venv

echo Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt

echo Environment fixed!
