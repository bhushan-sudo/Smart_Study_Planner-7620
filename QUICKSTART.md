# 🚀 Quick Start Guide - Smart Study Planner

## Prerequisites Checklist

Before you begin, ensure you have:

- [ ] **Python 3.8+** installed ([Download](https://www.python.org/downloads/))
- [ ] **PostgreSQL 12+** installed ([Download](https://www.postgresql.org/download/))
- [ ] **pgAdmin** or command-line access to PostgreSQL

## 🎯 Quick Setup (5 Minutes)

### Step 1: Setup PostgreSQL Database

**Option A: Using pgAdmin (GUI)**

1. Open pgAdmin
2. Right-click on "Databases" → "Create" → "Database"
3. Name: `study_planner_db`
4. Click "Save"
5. Right-click on `study_planner_db` → "Query Tool"
6. Open file: `database/schema.sql`
7. Click "Execute" (▶️ button)

**Option B: Using Command Line**

```bash
# Create database
psql -U postgres
CREATE DATABASE study_planner_db;
\q

# Run schema
psql -U postgres -d study_planner_db -f database\schema.sql
```

### Step 2: Configure Database Connection

1. Open `.env.example` file
2. Update the PostgreSQL password:

```
DB_PASSWORD=your_actual_postgres_password
```

3. Save as `.env` (remove the `.example` extension)

### Step 3: Install Python Dependencies

**Option A: Automated Setup (Recommended)**

```bash
# Double-click setup.bat or run:
setup.bat
```

**Option B: Manual Setup**

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Start the Application

**Option A: Using Run Script**

```bash
# Double-click run.bat or run:
run.bat
```

**Option B: Manual Start**

```bash
# Activate virtual environment
venv\Scripts\activate

# Navigate to backend
cd backend

# Start Flask server
python main.py
```

### Step 5: Access the Application

1. Open your browser
2. Navigate to: **<http://localhost:5000>**
3. Start planning your studies! 🎓

## 🎨 First Steps in the App

### 1. Add Your Subjects

- Click "Add Subject" button
- Enter subject name (e.g., "Mathematics")
- Choose a color and priority
- Click "Add Subject"

### 2. Create Your First Task

- Click "New Task" button
- Fill in task details:
  - Title: "Complete Chapter 5 Exercises"
  - Subject: Select from dropdown
  - Priority: 1-5 (5 is highest)
  - Estimated Hours: How long you think it will take
  - Deadline: When it's due
- Click "Create Task"

### 3. Use Smart Features

- **Auto-Schedule**: Click "Auto-Schedule" to let AI organize your tasks
- **Progress Tracking**: Click on tasks to update progress
- **Weekly Summary**: View your productivity stats

## 🔧 Troubleshooting

### Database Connection Failed

**Problem**: Can't connect to PostgreSQL

**Solutions**:

1. Verify PostgreSQL is running (check Windows Services)
2. Check username/password in `.env` file
3. Ensure database `study_planner_db` exists
4. Test connection: `psql -U postgres -d study_planner_db`

### Port 5000 Already in Use

**Problem**: Error "Address already in use"

**Solutions**:

1. Change port in `.env`: `PORT=5001`
2. Or find and stop the process using port 5000:

```bash
netstat -ano | findstr :5000
taskkill /PID <process_id> /F
```

### Module Not Found Error

**Problem**: `ModuleNotFoundError: No module named 'flask'`

**Solutions**:

1. Ensure virtual environment is activated: `venv\Scripts\activate`
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Check Python version: `python --version` (should be 3.8+)

### Frontend Not Loading

**Problem**: Blank page or 404 error

**Solutions**:

1. Ensure you're accessing `http://localhost:5000` (not `http://localhost:5000/api`)
2. Check browser console for errors (F12)
3. Verify Flask server is running
4. Clear browser cache (Ctrl + Shift + Delete)

## 📊 Sample Data

The database comes pre-loaded with:

- 1 demo user
- 5 sample subjects (Math, Physics, Chemistry, CS, English)
- 3 sample tasks

You can delete or modify these as needed!

## 🎯 Key Features to Try

### 1. Smart Scheduling

```
GET /api/users/1/planner/schedule?hours_per_day=4&days_ahead=7
```

Returns an optimized study schedule for the next 7 days.

### 2. Auto-Rescheduling

Click "Auto-Schedule" button to:

- Reschedule overdue tasks
- Balance workload across days
- Prioritize urgent tasks

### 3. Progress Tracking

Update task progress to:

- Track actual vs estimated hours
- Calculate efficiency scores
- Monitor completion rates

### 4. Weekly Analytics

Generate weekly summaries to:

- See productivity trends
- Compare week-over-week performance
- Identify improvement areas

## 💡 Pro Tips

1. **Set Realistic Estimates**: Be honest about how long tasks take
2. **Use Priorities Wisely**: Reserve priority 5 for truly urgent tasks
3. **Regular Updates**: Update progress daily for accurate analytics
4. **Review Weekly**: Check weekly summaries to improve planning
5. **Balance Workload**: Don't overload any single day

## 🔐 Security Notes

For development:

- Default password in `.env.example` is fine
- CORS is open to localhost

For production:

- Change `SECRET_KEY` to a random string
- Use strong PostgreSQL password
- Update `CORS_ORIGINS` to your domain
- Set `SESSION_COOKIE_SECURE=True`
- Set `DEBUG=False`

## 📱 Browser Compatibility

Tested and works great on:

- ✅ Chrome/Edge (Recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Opera

## 🆘 Need Help?

1. Check the main `README.md` for detailed documentation
2. Review API endpoints in README
3. Check browser console for errors (F12)
4. Verify database connection with pgAdmin

## 🎉 You're All Set

Your Smart Study Planner is ready to help you ace your studies!

**Happy Learning! 📚✨**

---

**Quick Reference**:

- Frontend: <http://localhost:5000>
- API: <http://localhost:5000/api>
- Health Check: <http://localhost:5000/api/health>
