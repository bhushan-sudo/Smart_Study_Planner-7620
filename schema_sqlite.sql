-- Smart Study Planner Database Schema
-- SQLite Database

-- Drop existing tables if they exist
DROP TABLE IF EXISTS task_progress;
DROP TABLE IF EXISTS weekly_summaries;
DROP TABLE IF EXISTS study_sessions;
DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS subjects;
DROP TABLE IF EXISTS users;

-- Users table
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(200),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Subjects table
CREATE TABLE subjects (
    subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    subject_name VARCHAR(200) NOT NULL,
    color_code VARCHAR(7) DEFAULT '#3B82F6',
    priority INTEGER DEFAULT 1 CHECK (priority BETWEEN 1 AND 5),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, subject_name)
);\r\n\r\n-- Chapters table (for tracking subject chapters)\r\nCREATE TABLE chapters (\r\n    chapter_id INTEGER PRIMARY KEY AUTOINCREMENT,\r\n    subject_id INTEGER NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,\r\n    chapter_name VARCHAR(200) NOT NULL,\r\n    chapter_number INTEGER NOT NULL,\r\n    difficulty VARCHAR(20) DEFAULT 'MEDIUM', -- EASY, MEDIUM, HARD\r\n    estimated_hours DECIMAL(4,2) DEFAULT 2.0,\r\n    status VARCHAR(50) DEFAULT 'pending', -- pending, in_progress, completed\r\n    completed_date DATETIME,\r\n    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,\r\n    UNIQUE(subject_id, chapter_number)\r\n);\r\n\r\n-- Badges table (for gamification)\r\nCREATE TABLE badges (\r\n    badge_id INTEGER PRIMARY KEY AUTOINCREMENT,\r\n    name VARCHAR(100) NOT NULL,\r\n    description TEXT,\r\n    icon_name VARCHAR(50), -- Font Awesome icon name\r\n    criteria_type VARCHAR(50) NOT NULL, -- streak_days, study_hours, subjects_completed, etc.\r\n    criteria_value INTEGER NOT NULL,\r\n    badge_level INTEGER DEFAULT 1, -- 1=Bronze, 2=Silver, 3=Gold, 4=Platinum\r\n    created_at DATETIME DEFAULT CURRENT_TIMESTAMP\r\n);\r\n\r\n-- User Badges table (earned badges)\r\nCREATE TABLE user_badges (\r\n    user_badge_id INTEGER PRIMARY KEY AUTOINCREMENT,\r\n    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,\r\n    badge_id INTEGER NOT NULL REFERENCES badges(badge_id) ON DELETE CASCADE,\r\n    earned_date DATETIME DEFAULT CURRENT_TIMESTAMP,\r\n    UNIQUE(user_id, badge_id)\r\n);\r\n\r\n-- User Preferences table\r\nCREATE TABLE user_preferences (\r\n    user_id INTEGER PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,\r\n    pomodoro_work_duration INTEGER DEFAULT 25, -- minutes\r\n    pomodoro_break_duration INTEGER DEFAULT 5, -- minutes\r\n    pomodoro_long_break_duration INTEGER DEFAULT 15, -- minutes\r\n    daily_study_goal_hours DECIMAL(4,2) DEFAULT 4.0,\r\n    notifications_enabled BOOLEAN DEFAULT 1,\r\n    theme VARCHAR(20) DEFAULT 'light',\r\n    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,\r\n    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP\r\n);

-- Tasks table
CREATE TABLE tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    subject_id INTEGER REFERENCES subjects(subject_id) ON DELETE SET NULL,
    title VARCHAR(300) NOT NULL,
    description TEXT,
    task_type VARCHAR(50) DEFAULT 'study', -- study, assignment, exam, revision
    priority INTEGER DEFAULT 1 CHECK (priority BETWEEN 1 AND 5),
    estimated_hours DECIMAL(5,2) DEFAULT 1.0,
    deadline DATETIME,
    scheduled_date DATE,
    scheduled_time TIME,
    status VARCHAR(50) DEFAULT 'pending', -- pending, in_progress, completed, overdue, rescheduled
    completion_percentage INTEGER DEFAULT 0 CHECK (completion_percentage BETWEEN 0 AND 100),
    actual_hours DECIMAL(5,2) DEFAULT 0,
    is_recurring BOOLEAN DEFAULT 0,
    recurrence_pattern VARCHAR(50), -- daily, weekly, monthly
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME
);

-- Study Sessions table (for tracking actual study time)
CREATE TABLE study_sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER REFERENCES tasks(task_id) ON DELETE SET NULL, -- Made nullable for pomodoro sessions
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    duration_minutes INTEGER,
    session_type VARCHAR(50) DEFAULT 'study', -- 'study', 'work', 'break', 'long_break'
    notes TEXT,
    focus_score INTEGER CHECK (focus_score BETWEEN 1 AND 10),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Task Progress table (for detailed progress tracking)
CREATE TABLE task_progress (
    progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    progress_date DATE NOT NULL,
    hours_spent DECIMAL(5,2) DEFAULT 0,
    completion_delta INTEGER DEFAULT 0, -- change in completion percentage
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Weekly Summaries table
CREATE TABLE weekly_summaries (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    total_tasks_planned INTEGER DEFAULT 0,
    total_tasks_completed INTEGER DEFAULT 0,
    total_hours_planned DECIMAL(6,2) DEFAULT 0,
    total_hours_actual DECIMAL(6,2) DEFAULT 0,
    completion_rate DECIMAL(5,2) DEFAULT 0,
    productivity_score DECIMAL(5,2) DEFAULT 0,
    summary_data TEXT, -- Store detailed statistics as JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, week_start_date)
);

-- Study Goals table
CREATE TABLE study_goals (
    goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    target_value DECIMAL(8,2) NOT NULL, -- e.g., hours, tasks, etc.
    current_value DECIMAL(8,2) DEFAULT 0,
    goal_type VARCHAR(50) NOT NULL, -- hours_per_week, tasks_per_month, streak_days, etc.
    target_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'active', -- active, completed, expired
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Study Streaks table
CREATE TABLE study_streaks (
    streak_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    streak_date DATE NOT NULL,
    study_hours DECIMAL(4,2) DEFAULT 0,
    tasks_completed INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, streak_date)
);

-- Notifications table
CREATE TABLE notifications (
    notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    message TEXT,
    notification_type VARCHAR(50) DEFAULT 'info', -- info, warning, success, reminder
    is_read BOOLEAN DEFAULT 0,
    scheduled_for DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- File Attachments table
CREATE TABLE file_attachments (
    attachment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER REFERENCES tasks(task_id) ON DELETE SET NULL, -- Made nullable for general file uploads
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    file_type VARCHAR(100),
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better performance
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_deadline ON tasks(deadline);
CREATE INDEX idx_tasks_scheduled_date ON tasks(scheduled_date);
CREATE INDEX idx_subjects_user_id ON subjects(user_id);
CREATE INDEX idx_study_sessions_task_id ON study_sessions(task_id);
CREATE INDEX idx_study_sessions_user_id ON study_sessions(user_id);
CREATE INDEX idx_task_progress_task_id ON task_progress(task_id);
CREATE INDEX idx_weekly_summaries_user_id ON weekly_summaries(user_id);
CREATE INDEX idx_study_goals_user_id ON study_goals(user_id);
CREATE INDEX idx_study_streaks_user_id ON study_streaks(user_id);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_file_attachments_task_id ON file_attachments(task_id);

-- Insert sample data for testing
INSERT INTO users (username, email, password_hash, full_name) VALUES
('demo_user', 'demo@studyplanner.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPjYLC3zWJzO', 'Demo Student');

INSERT INTO subjects (user_id, subject_name, color_code, priority) VALUES
(1, 'Mathematics', '#EF4444', 5),
(1, 'Physics', '#3B82F6', 4),
(1, 'Chemistry', '#10B981', 4),
(1, 'Computer Science', '#8B5CF6', 5),
(1, 'English Literature', '#F59E0B', 3);

-- Indexes for new tables
CREATE INDEX idx_chapters_subject_id ON chapters(subject_id);
CREATE INDEX idx_chapters_status ON chapters(status);
CREATE INDEX idx_user_badges_user_id ON user_badges(user_id);
CREATE INDEX idx_user_badges_badge_id ON user_badges(badge_id);

-- Insert sample badges
INSERT INTO badges (name, description, icon_name, criteria_type, criteria_value, badge_level) VALUES
-- Streak Badges
('Week Warrior', 'Study for 7 consecutive days', 'fire', 'streak_days', 7, 1),
('Month Master', 'Study for 30 consecutive days', 'fire', 'streak_days', 30, 2),
('Century Scholar', 'Study for 100 consecutive days', 'fire', 'streak_days', 100, 3),
('Year Legend', 'Study for 365 consecutive days', 'fire', 'streak_days', 365, 4),

-- Study Hours Badges
('First Steps', 'Complete 10 hours of study', 'clock', 'study_hours', 10, 1),
('Dedicated Learner', 'Complete 50 hours of study', 'clock', 'study_hours', 50, 2),
('Centurion', 'Complete 100 hours of study', 'clock', 'study_hours', 100, 3),
('Study Marathon', 'Complete 500 hours of study', 'clock', 'study_hours', 500, 4),

-- Subject Completion Badges
('Subject Starter', 'Complete 1 subject', 'book', 'subjects_completed', 1, 1),
('Multi-Tasker', 'Complete 3 subjects', 'book', 'subjects_completed', 3, 2),
('Knowledge Seeker', 'Complete 5 subjects', 'book', 'subjects_completed', 5, 3),
('Master Scholar', 'Complete 10 subjects', 'book', 'subjects_completed', 10, 4),

-- Special Badges
('Early Bird', 'Complete 10 study sessions before 8 AM', 'sun', 'early_sessions', 10, 2),
('Night Owl', 'Complete 10 study sessions after 10 PM', 'moon', 'late_sessions', 10, 2),
('Focus Master', 'Complete 10 Pomodoro sessions in one day', 'bullseye', 'daily_pomodoros', 10, 3),
('Perfect Week', 'Study every day for a week with 100% goal completion', 'star', 'perfect_week', 1, 3);
