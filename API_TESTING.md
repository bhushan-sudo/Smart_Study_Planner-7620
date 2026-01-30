# 🧪 API Testing Guide

Quick reference for testing the Smart Study Planner API endpoints.

## 🔧 Setup

Base URL: `http://localhost:5000/api`
Default User ID: `1` (demo_user)

## 📋 Testing Tools

You can test the API using:

- **Browser** (for GET requests)
- **Postman** ([Download](https://www.postman.com/downloads/))
- **cURL** (command line)
- **Thunder Client** (VS Code extension)

## ✅ Health Check

### Check API Status

```bash
GET http://localhost:5000/api/health
```

**Expected Response:**

```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-01-13T23:00:00"
}
```

## 👤 User Endpoints

### Get All Users

```bash
GET http://localhost:5000/api/users
```

### Get User by ID

```bash
GET http://localhost:5000/api/users/1
```

### Create New User

```bash
POST http://localhost:5000/api/users
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password_hash": "hashed_password",
  "full_name": "John Doe"
}
```

## 📚 Subject Endpoints

### Get User's Subjects

```bash
GET http://localhost:5000/api/users/1/subjects
```

### Create New Subject

```bash
POST http://localhost:5000/api/users/1/subjects
Content-Type: application/json

{
  "subject_name": "Advanced Mathematics",
  "color_code": "#EF4444",
  "priority": 5
}
```

### Update Subject

```bash
PUT http://localhost:5000/api/subjects/1
Content-Type: application/json

{
  "subject_name": "Calculus",
  "priority": 4
}
```

### Delete Subject

```bash
DELETE http://localhost:5000/api/subjects/1
```

## 📝 Task Endpoints

### Get All Tasks for User

```bash
GET http://localhost:5000/api/users/1/tasks
```

### Get Tasks by Status

```bash
GET http://localhost:5000/api/users/1/tasks?status=pending
GET http://localhost:5000/api/users/1/tasks?status=completed
```

### Get Limited Tasks

```bash
GET http://localhost:5000/api/users/1/tasks?limit=5
```

### Create New Task

```bash
POST http://localhost:5000/api/users/1/tasks
Content-Type: application/json

{
  "title": "Complete Calculus Assignment",
  "description": "Solve problems 1-20 from Chapter 5",
  "subject_id": 1,
  "task_type": "assignment",
  "priority": 5,
  "estimated_hours": 3.5,
  "deadline": "2026-01-20T23:59:00",
  "scheduled_date": "2026-01-15",
  "scheduled_time": "14:00:00"
}
```

### Update Task

```bash
PUT http://localhost:5000/api/tasks/1
Content-Type: application/json

{
  "completion_percentage": 50,
  "status": "in_progress",
  "actual_hours": 1.5
}
```

### Mark Task as Completed

```bash
PUT http://localhost:5000/api/tasks/1
Content-Type: application/json

{
  "completion_percentage": 100,
  "status": "completed",
  "completed_at": "2026-01-15T16:30:00"
}
```

### Delete Task

```bash
DELETE http://localhost:5000/api/tasks/1
```

### Get Overdue Tasks

```bash
GET http://localhost:5000/api/users/1/tasks/overdue
```

## 🧠 Smart Planner Endpoints

### Get Suggested Schedule

```bash
GET http://localhost:5000/api/users/1/planner/schedule?hours_per_day=4&days_ahead=7
```

**Parameters:**

- `hours_per_day`: Available study hours per day (default: 4)
- `days_ahead`: Number of days to plan (default: 7)

### Get Daily Recommendations

```bash
GET http://localhost:5000/api/users/1/planner/recommendations
GET http://localhost:5000/api/users/1/planner/recommendations?date=2026-01-15
```

### Analyze Workload

```bash
GET http://localhost:5000/api/users/1/planner/workload?days_ahead=7
```

## 🔄 Rescheduler Endpoints

### Auto Reschedule All

```bash
POST http://localhost:5000/api/users/1/reschedule/auto
```

**Response:**

```json
{
  "overdue_rescheduled": [...],
  "incomplete_rescheduled": [...],
  "workload_balanced": [...],
  "timestamp": "2026-01-13T23:00:00"
}
```

### Balance Workload

```bash
POST http://localhost:5000/api/users/1/reschedule/balance?days_ahead=7&max_hours=6
```

## 📊 Progress Tracking Endpoints

### Update Task Progress

```bash
POST http://localhost:5000/api/tasks/1/progress
Content-Type: application/json

{
  "user_id": 1,
  "hours_spent": 2.5,
  "completion_percentage": 60,
  "notes": "Completed sections A and B"
}
```

### Get Task Analytics

```bash
GET http://localhost:5000/api/tasks/1/analytics
```

**Response:**

```json
{
  "task": {...},
  "progress_history": [...],
  "study_sessions": [...],
  "metrics": {
    "estimated_hours": 3.5,
    "actual_hours": 2.5,
    "completion_percentage": 60,
    "hours_remaining": 1.0,
    "efficiency_score": 0.85,
    "average_focus_score": 8.5,
    "total_sessions": 3,
    "is_on_track": true
  }
}
```

### Log Study Session

```bash
POST http://localhost:5000/api/tasks/1/sessions
Content-Type: application/json

{
  "user_id": 1,
  "start_time": "2026-01-15T14:00:00",
  "end_time": "2026-01-15T16:30:00",
  "notes": "Focused study session, completed 10 problems",
  "focus_score": 9
}
```

## 📈 Weekly Summary Endpoints

### Get Weekly Summaries

```bash
GET http://localhost:5000/api/users/1/summary/weekly
```

### Generate Weekly Summary

```bash
POST http://localhost:5000/api/users/1/summary/weekly
POST http://localhost:5000/api/users/1/summary/weekly?week_start=2026-01-13
```

### Get Summary Comparison

```bash
GET http://localhost:5000/api/users/1/summary/comparison?weeks=4
```

## 🧪 Sample Test Workflow

### 1. Create a Complete Study Plan

```bash
# 1. Create subjects
POST /api/users/1/subjects
{
  "subject_name": "Data Structures",
  "color_code": "#8B5CF6",
  "priority": 5
}

# 2. Create tasks
POST /api/users/1/tasks
{
  "title": "Implement Binary Search Tree",
  "subject_id": 1,
  "task_type": "assignment",
  "priority": 5,
  "estimated_hours": 4,
  "deadline": "2026-01-20T23:59:00"
}

# 3. Get smart schedule
GET /api/users/1/planner/schedule?hours_per_day=5&days_ahead=7

# 4. Log study session
POST /api/tasks/1/sessions
{
  "user_id": 1,
  "start_time": "2026-01-15T14:00:00",
  "end_time": "2026-01-15T16:00:00",
  "focus_score": 8
}

# 5. Update progress
POST /api/tasks/1/progress
{
  "user_id": 1,
  "hours_spent": 2,
  "completion_percentage": 50
}

# 6. Get analytics
GET /api/tasks/1/analytics

# 7. Generate weekly summary
POST /api/users/1/summary/weekly
```

## 🐛 Common Issues

### 404 Not Found

- Check the URL is correct
- Ensure Flask server is running
- Verify the resource ID exists

### 500 Internal Server Error

- Check database connection
- Review Flask console for error details
- Verify request body format

### CORS Error

- Ensure CORS_ORIGINS in .env includes your origin
- Check browser console for specific error

## 📝 cURL Examples

### GET Request

```bash
curl http://localhost:5000/api/users/1/tasks
```

### POST Request

```bash
curl -X POST http://localhost:5000/api/users/1/tasks \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"Study Session\",\"priority\":3,\"estimated_hours\":2}"
```

### PUT Request

```bash
curl -X PUT http://localhost:5000/api/tasks/1 \
  -H "Content-Type: application/json" \
  -d "{\"completion_percentage\":75,\"status\":\"in_progress\"}"
```

### DELETE Request

```bash
curl -X DELETE http://localhost:5000/api/tasks/1
```

## 🎯 Testing Checklist

- [ ] Health check returns "healthy"
- [ ] Can create new subjects
- [ ] Can create new tasks
- [ ] Can update task progress
- [ ] Smart schedule generates valid plan
- [ ] Auto-reschedule works
- [ ] Task analytics show correct metrics
- [ ] Weekly summary generates successfully
- [ ] All CRUD operations work
- [ ] Error handling works properly

## 📊 Response Status Codes

- `200 OK` - Successful GET/PUT/DELETE
- `201 Created` - Successful POST
- `400 Bad Request` - Invalid request data
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

**Happy Testing! 🧪✨**
