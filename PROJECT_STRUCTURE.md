# Smart Study Planner - Project Structure

```
Study_Planner/
│
├── 📁 frontend/
│   └── index.html                    # Premium SPA with dark theme UI
│
├── 📁 backend/
│   ├── db_config.py                  # Database & app configuration
│   ├── database.py                   # PostgreSQL connection pooling
│   ├── models.py                     # Data models (User, Subject, Task, etc.)
│   ├── planner_logic.py              # Smart scheduling algorithms
│   ├── rescheduler.py                # Automatic task rescheduling
│   ├── progress_tracker.py           # Progress tracking & analytics
│   ├── weekly_summary.py             # Weekly summary generation
│   └── main.py                       # Flask REST API (entry point)
│
├── 📁 database/
│   └── schema.sql                    # PostgreSQL database schema
│
├── 📄 .env.example                   # Environment variables template
├── 📄 .gitignore                     # Git ignore rules
├── 📄 requirements.txt               # Python dependencies
├── 📄 README.md                      # Full documentation
├── 📄 QUICKSTART.md                  # Quick start guide
├── 📄 setup.bat                      # Automated setup script
└── 📄 run.bat                        # Application launcher
```

## 📊 Database Schema

```
┌─────────────┐
│    users    │
└──────┬──────┘
       │
       ├──────────┬──────────────┬──────────────┬──────────────┐
       │          │              │              │              │
┌──────▼──────┐ ┌─▼─────────┐ ┌─▼──────────┐ ┌─▼──────────┐ ┌─▼──────────────┐
│  subjects   │ │   tasks    │ │  study_    │ │   task_    │ │   weekly_      │
│             │ │            │ │  sessions  │ │  progress  │ │  summaries     │
└─────────────┘ └────┬───────┘ └────────────┘ └────────────┘ └────────────────┘
                     │
              ┌──────┴──────┐
              │             │
       ┌──────▼──────┐ ┌────▼────────┐
       │   study_    │ │   task_     │
       │  sessions   │ │  progress   │
       └─────────────┘ └─────────────┘
```

## 🔄 Application Flow

```
┌──────────────┐
│   Browser    │
│ (Frontend)   │
└──────┬───────┘
       │ HTTP Requests
       │
┌──────▼───────┐
│  Flask API   │ ◄─── main.py
│  (Backend)   │
└──────┬───────┘
       │
       ├─────────────┬──────────────┬──────────────┐
       │             │              │              │
┌──────▼──────┐ ┌────▼─────┐ ┌─────▼──────┐ ┌────▼──────────┐
│   Models    │ │ Planner  │ │Rescheduler │ │   Progress    │
│             │ │  Logic   │ │            │ │   Tracker     │
└──────┬──────┘ └────┬─────┘ └─────┬──────┘ └────┬──────────┘
       │             │              │              │
       └─────────────┴──────────────┴──────────────┘
                     │
              ┌──────▼──────┐
              │ PostgreSQL  │
              │  Database   │
              └─────────────┘
```

## 🎯 Core Modules

### 1. **Frontend (index.html)**

- Single-page application
- Modern dark theme with gradients
- Real-time task management
- Interactive dashboard
- Responsive design

### 2. **Backend API (main.py)**

- RESTful API endpoints
- CORS enabled
- JSON responses
- Error handling
- Health checks

### 3. **Database Layer (database.py)**

- Connection pooling
- Context managers
- Transaction handling
- Query helpers

### 4. **Data Models (models.py)**

- User management
- Subject CRUD
- Task operations
- Session tracking
- Progress logging

### 5. **Smart Planner (planner_logic.py)**

- Priority scoring algorithm
- Schedule optimization
- Daily recommendations
- Workload analysis

### 6. **Auto Rescheduler (rescheduler.py)**

- Overdue task handling
- Incomplete task management
- Workload balancing
- Deadline recalculation

### 7. **Progress Tracker (progress_tracker.py)**

- Task progress updates
- Study session logging
- Analytics generation
- Efficiency calculations

### 8. **Weekly Summary (weekly_summary.py)**

- Summary generation
- Productivity metrics
- Trend analysis
- Comparison reports

## 🔌 API Endpoints Overview

### Users

- `GET/POST /api/users`
- `GET /api/users/{id}`

### Subjects

- `GET/POST /api/users/{id}/subjects`
- `GET/PUT/DELETE /api/subjects/{id}`

### Tasks

- `GET/POST /api/users/{id}/tasks`
- `GET/PUT/DELETE /api/tasks/{id}`
- `GET /api/users/{id}/tasks/overdue`

### Planning

- `GET /api/users/{id}/planner/schedule`
- `GET /api/users/{id}/planner/recommendations`
- `GET /api/users/{id}/planner/workload`

### Rescheduling

- `POST /api/users/{id}/reschedule/auto`
- `POST /api/users/{id}/reschedule/balance`

### Progress

- `POST /api/tasks/{id}/progress`
- `GET /api/tasks/{id}/analytics`
- `POST /api/tasks/{id}/sessions`

### Summaries

- `GET/POST /api/users/{id}/summary/weekly`
- `GET /api/users/{id}/summary/comparison`

## 🎨 UI Components

### Dashboard Cards

- Total Tasks
- Completed Tasks
- Study Hours
- Productivity Score

### Task Management

- Task creation form
- Task list with filters
- Progress bars
- Priority badges
- Status indicators

### Subject Management

- Subject cards
- Color coding
- Priority levels

### Modals

- Create Task Modal
- Add Subject Modal
- Animated transitions

## 🚀 Deployment Checklist

- [ ] Update `.env` with production values
- [ ] Set `DEBUG=False`
- [ ] Use strong `SECRET_KEY`
- [ ] Configure production database
- [ ] Set proper `CORS_ORIGINS`
- [ ] Enable HTTPS
- [ ] Set `SESSION_COOKIE_SECURE=True`
- [ ] Configure firewall rules
- [ ] Set up database backups
- [ ] Monitor application logs

## 📈 Performance Optimizations

### Database

- Connection pooling (5-10 connections)
- Indexed columns (user_id, task_id, dates)
- Efficient queries with JOINs

### Frontend

- Minimal dependencies (no frameworks)
- CSS animations (GPU accelerated)
- Lazy loading for large lists
- Debounced API calls

### Backend

- Async-ready architecture
- Cached database connections
- Efficient JSON serialization
- Request validation

## 🔒 Security Features

- Environment variable configuration
- SQL injection protection (parameterized queries)
- CORS configuration
- Session management
- Password hashing support
- Input validation

## 📊 Analytics & Metrics

### Task Metrics

- Completion percentage
- Actual vs estimated hours
- Efficiency score
- Priority distribution

### User Metrics

- Weekly productivity
- Completion rate
- Study hours
- Subject distribution

### System Metrics

- Database connection health
- API response times
- Error rates

---

**Built with ❤️ for students who want to study smarter, not harder!**
