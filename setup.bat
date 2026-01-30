@echo off
echo ========================================
echo Smart Study Planner - Setup Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo [1/5] Creating .env file from template...
if not exist .env (
    copy .env.example .env
    echo .env file created. Please edit it with your PostgreSQL credentials.
) else (
    echo .env file already exists. Skipping...
)
echo.

echo [2/5] Creating virtual environment...
if not exist venv (
    python -m venv venv
    echo Virtual environment created successfully.
) else (
    echo Virtual environment already exists. Skipping...
)
echo.

echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat
echo.

echo [4/5] Installing Python dependencies...
pip install -r requirements.txt
echo.

echo [5/5] Setup complete!
echo.
echo ========================================
echo Next Steps:
echo ========================================
echo 1. Edit .env file with your PostgreSQL credentials
echo 2. Create PostgreSQL database: CREATE DATABASE study_planner_db;
echo 3. Run database schema: psql -U postgres -d study_planner_db -f database\schema.sql
echo 4. Start the application: cd backend ^&^& python main.py
echo 5. Open browser: http://localhost:5000
echo ========================================
echo.
pause
