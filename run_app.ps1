write-host "Starting Smart Study Planner..." -ForegroundColor Cyan

# Check for python in venv
$pythonPath = "venv\Scripts\python.exe"
if (-not (Test-Path $pythonPath)) {
    write-host "Virtual environment not found at $pythonPath. Please run setup.bat first." -ForegroundColor Red
    exit 1
}

# Check if tables need initialization (optional check, better to just let user run initialization manually if needed)
# But we can print a hint
write-host "Ensure you have initialized the database using 'python init_supabase.py' if this is the first run." -ForegroundColor Yellow

# Change directory to backend
Set-Location backend

# Run the app
& "..\$pythonPath" main.py
