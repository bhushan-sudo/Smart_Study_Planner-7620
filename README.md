# Smart Study Planner

An intelligent study planning application with AI-powered scheduling, automatic task rescheduling, progress tracking, and productivity analytics.

## 🎯 Features

- **Smart Task Management**: Create and organize study tasks with priorities, deadlines, and subjects
- **Intelligent Scheduling**: AI-powered algorithm suggests optimal study schedules
- **Automatic Rescheduling**: Automatically reschedules overdue and incomplete tasks
- **Progress Tracking**: Track study sessions, hours spent, and completion percentages
- **Weekly Summaries**: Comprehensive weekly productivity reports and analytics
- **Subject Management**: Organize tasks by subjects with custom colors and priorities
- **Workload Balancing**: Automatically balances study load across days
- **Beautiful UI**: Modern, premium dark-themed interface with smooth animations

## 🏗️ Project Structure

```
smart_study_planner/
│
├── frontend/
│   └── index.html              # Single-page application with premium UI
│
├── backend/
│   ├── db_config.py            # Database configuration
│   ├── database.py             # PostgreSQL connection pooling
│   ├── models.py               # Data models (ORM-like)
│   ├── planner_logic.py        # Smart scheduling algorithms
│   ├── rescheduler.py          # Automatic rescheduling logic
│   ├── progress_tracker.py     # Progress tracking and analytics
│   ├── weekly_summary.py       # Weekly summary generation
│   └── main.py                 # Flask REST API
│
└── database/
    └── schema.sql              # PostgreSQL database schema
```

## 🚀 Setup Instructions

### Prerequisites

- Python 3.8 or higher
- **PostgreSQL 12 or higher** OR **Supabase account** (recommended for easy setup)
- pip (Python package manager)

> 💡 **New to PostgreSQL?** We recommend using [Supabase](https://supabase.com) - a free, cloud-hosted PostgreSQL database that requires no local installation. See [SUPABASE_SETUP.md](SUPABASE_SETUP.md) for detailed instructions.

### 1. Database Setup

1. Install PostgreSQL if not already installed
2. Create a new database:

```sql
CREATE DATABASE study_planner_db;
```

1. Run the schema file to create tables:

```bash
psql -U postgres -d study_planner_db -f database/schema.sql
```

Or using pgAdmin, connect to the database and execute the `schema.sql` file.

### 2. Backend Setup

1. Navigate to the project directory:

```bash
cd Study_Planner
```

1. Create a virtual environment (recommended):

```bash
python -m venv venv
```

1. Activate the virtual environment:

- Windows:

```bash
venv\Scripts\activate
```

- Linux/Mac:

```bash
source venv/bin/activate
```

1. Install dependencies:

```bash
pip install -r requirements.txt
```

1. Configure environment variables:

- Copy `.env.example` to `.env`:

```bash
copy .env.example .env
```

- Edit `.env` and update your PostgreSQL credentials:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=study_planner_db
DB_USER=postgres
DB_PASSWORD=your_password_here
```

### 3. Run the Application

1. Start the Flask backend:

```bash
cd backend
python main.py
```

The server will start at `http://localhost:5000`

1. Open your browser and navigate to:

```
http://localhost:5000
```

## 📖 API Documentation

### Base URL

```
http://localhost:5000/api
```

### Endpoints

#### Health Check

- `GET /api/health` - Check API and database status

#### Users

- `GET /api/users` - Get all users
- `POST /api/users` - Create a new user
- `GET /api/users/{user_id}` - Get user by ID

#### Subjects

- `GET /api/users/{user_id}/subjects` - Get user's subjects
- `POST /api/users/{user_id}/subjects` - Create a new subject
- `GET /api/subjects/{subject_id}` - Get subject details
- `PUT /api/subjects/{subject_id}` - Update subject
- `DELETE /api/subjects/{subject_id}` - Delete subject

#### Tasks

- `GET /api/users/{user_id}/tasks` - Get user's tasks
- `POST /api/users/{user_id}/tasks` - Create a new task
- `GET /api/tasks/{task_id}` - Get task details
- `PUT /api/tasks/{task_id}` - Update task
- `DELETE /api/tasks/{task_id}` - Delete task
- `GET /api/users/{user_id}/tasks/overdue` - Get overdue tasks

#### Smart Planner

- `GET /api/users/{user_id}/planner/schedule` - Get suggested schedule
- `GET /api/users/{user_id}/planner/recommendations` - Get daily recommendations
- `GET /api/users/{user_id}/planner/workload` - Analyze workload

#### Rescheduler

- `POST /api/users/{user_id}/reschedule/auto` - Run automatic rescheduling
- `POST /api/users/{user_id}/reschedule/balance` - Balance workload

#### Progress Tracking

- `POST /api/tasks/{task_id}/progress` - Update task progress
- `GET /api/tasks/{task_id}/analytics` - Get task analytics
- `POST /api/tasks/{task_id}/sessions` - Log study session

#### Weekly Summary

- `GET /api/users/{user_id}/summary/weekly` - Get weekly summaries
- `POST /api/users/{user_id}/summary/weekly` - Generate weekly summary
- `GET /api/users/{user_id}/summary/comparison` - Compare weekly summaries

## 🎨 Features in Detail

### Smart Scheduling Algorithm

The planner uses a priority-based algorithm that considers:

- Task priority (1-5)
- Deadline urgency
- Task type (exam, assignment, study, revision)
- Completion percentage
- Estimated hours

### Automatic Rescheduling

- Reschedules overdue tasks based on priority
- Moves incomplete tasks to the next available day
- Balances workload to prevent overloading any single day

### Progress Tracking

- Log study sessions with start/end times
- Track actual hours vs estimated hours
- Calculate efficiency scores
- Monitor focus scores (1-10)

### Weekly Summaries

- Total tasks planned vs completed
- Total hours planned vs actual
- Completion rate and productivity score
- Subject-wise breakdown
- Trend analysis over multiple weeks

## 🛠️ Technology Stack

- **Backend**: Python, Flask, psycopg2
- **Database**: PostgreSQL
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Design**: Modern dark theme with gradients and animations

## 📝 Default Demo Data

The schema includes sample data:

- Demo user (username: `demo_user`)
- 5 sample subjects (Mathematics, Physics, Chemistry, Computer Science, English Literature)
- 3 sample tasks

## 🔒 Security Notes

- Change the `SECRET_KEY` in `.env` for production
- Use strong PostgreSQL passwords
- Enable `SESSION_COOKIE_SECURE` in production (HTTPS)
- Configure proper CORS origins for production

## 📊 Database Schema

The application uses the following main tables:

- `users` - User accounts
- `subjects` - Study subjects
- `tasks` - Study tasks and assignments
- `study_sessions` - Logged study sessions
- `task_progress` - Daily progress tracking
- `weekly_summaries` - Weekly productivity summaries

## 🤝 Contributing

This is a demo project. Feel free to fork and customize for your needs!

## 📄 License

MIT License - feel free to use this project for personal or educational purposes.

## 🐛 Troubleshooting

### Database Connection Error

- Verify PostgreSQL is running
- Check database credentials in `.env`
- Ensure database `study_planner_db` exists

### Port Already in Use

- Change the `PORT` in `.env` to a different port
- Or stop the process using port 5000

### Module Not Found Error

- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again

## 📧 Support

For issues or questions, please check the code comments or create an issue in the repository.

---

**Happy Studying! 📚✨**
