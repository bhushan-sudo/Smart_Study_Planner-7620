-- Smart Study Planner Database Schema
-- PostgreSQL Database

-- Drop existing tables if they exist
DROP TABLE IF EXISTS task_progress CASCADE;
DROP TABLE IF EXISTS weekly_summaries CASCADE;
DROP TABLE IF EXISTS study_sessions CASCADE;
DROP TABLE IF EXISTS tasks CASCADE;
DROP TABLE IF EXISTS subjects CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS file_attachments CASCADE;
DROP TABLE IF EXISTS study_goals CASCADE;
DROP TABLE IF EXISTS study_streaks CASCADE;

-- Users table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subjects table
CREATE TABLE subjects (
    subject_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    subject_name VARCHAR(200) NOT NULL,
    color_code VARCHAR(7) DEFAULT '#3B82F6',
    priority INTEGER DEFAULT 1 CHECK (priority BETWEEN 1 AND 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, subject_name)
);

-- Tasks table
CREATE TABLE tasks (
    task_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    subject_id INTEGER REFERENCES subjects(subject_id) ON DELETE SET NULL,
    title VARCHAR(300) NOT NULL,
    description TEXT,
    task_type VARCHAR(50) DEFAULT 'study', -- study, assignment, exam, revision
    priority INTEGER DEFAULT 1 CHECK (priority BETWEEN 1 AND 5),
    estimated_hours DECIMAL(5,2) DEFAULT 1.0,
    deadline TIMESTAMP,
    scheduled_date DATE,
    scheduled_time TIME,
    status VARCHAR(50) DEFAULT 'pending', -- pending, in_progress, completed, overdue, rescheduled
    completion_percentage INTEGER DEFAULT 0 CHECK (completion_percentage BETWEEN 0 AND 100),
    actual_hours DECIMAL(5,2) DEFAULT 0,
    is_recurring BOOLEAN DEFAULT FALSE,
    recurrence_pattern VARCHAR(50), -- daily, weekly, monthly
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Study Sessions table (for tracking actual study time)
CREATE TABLE study_sessions (
    session_id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(task_id) ON DELETE SET NULL, -- Made nullable for pomodoro sessions
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_minutes INTEGER,
    session_type VARCHAR(50) DEFAULT 'study', -- 'study', 'work', 'break', 'long_break'
    notes TEXT,
    focus_score INTEGER CHECK (focus_score BETWEEN 1 AND 10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Task Progress table (for detailed progress tracking)
CREATE TABLE task_progress (
    progress_id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    progress_date DATE NOT NULL,
    hours_spent DECIMAL(5,2) DEFAULT 0,
    completion_delta INTEGER DEFAULT 0, -- change in completion percentage
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Weekly Summaries table
CREATE TABLE weekly_summaries (
    summary_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    total_tasks_planned INTEGER DEFAULT 0,
    total_tasks_completed INTEGER DEFAULT 0,
    total_hours_planned DECIMAL(6,2) DEFAULT 0,
    total_hours_actual DECIMAL(6,2) DEFAULT 0,
    completion_rate DECIMAL(5,2) DEFAULT 0,
    productivity_score DECIMAL(5,2) DEFAULT 0,
    summary_data JSONB, -- Store detailed statistics
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, week_start_date)
);

-- Study Goals table
CREATE TABLE study_goals (
    goal_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    target_value DECIMAL(8,2) NOT NULL, -- e.g., hours, tasks, etc.
    current_value DECIMAL(8,2) DEFAULT 0,
    goal_type VARCHAR(50) NOT NULL, -- hours_per_week, tasks_per_month, streak_days, etc.
    target_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'active', -- active, completed, expired
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Study Streaks table
CREATE TABLE study_streaks (
    streak_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    streak_date DATE NOT NULL,
    study_hours DECIMAL(4,2) DEFAULT 0,
    tasks_completed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, streak_date)
);

-- Notifications table
CREATE TABLE notifications (
    notification_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    message TEXT,
    notification_type VARCHAR(50) DEFAULT 'info', -- info, warning, success, reminder
    is_read BOOLEAN DEFAULT FALSE,
    scheduled_for TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- File Attachments table
CREATE TABLE file_attachments (
    attachment_id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(task_id) ON DELETE SET NULL, -- Made nullable for general file uploads
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    file_type VARCHAR(100),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing
INSERT INTO users (username, email, password_hash, full_name) VALUES
('demo_user', 'demo@studyplanner.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/Le0KdV0K1Z9K9K9K', 'Demo Student');

INSERT INTO subjects (user_id, subject_name, color_code, priority) VALUES
(1, 'Mathematics', '#EF4444', 5),
(1, 'Physics', '#3B82F6', 4),
(1, 'Chemistry', '#10B981', 4),
(1, 'Computer Science', '#8B5CF6', 5),
(1, 'English Literature', '#F59E0B', 3);

INSERT INTO tasks (user_id, subject_id, title, description, task_type, priority, estimated_hours, deadline, scheduled_date, status) VALUES
(1, 1, 'Calculus Chapter 5', 'Complete derivatives and integration exercises', 'study', 5, 3.0, CURRENT_TIMESTAMP + INTERVAL '3 days', CURRENT_DATE + 1, 'pending'),
(1, 2, 'Physics Lab Report', 'Write lab report on pendulum experiment', 'assignment', 4, 2.5, CURRENT_TIMESTAMP + INTERVAL '5 days', CURRENT_DATE + 2, 'pending'),
(1, 4, 'Data Structures Project', 'Implement binary search tree', 'assignment', 5, 5.0, CURRENT_TIMESTAMP + INTERVAL '7 days', CURRENT_DATE + 3, 'pending');
INSERT INTO study_goals (user_id, title, description, target_value, goal_type, target_date) VALUES
(1, 'Weekly Study Hours', 'Study at least 15 hours this week', 15.0, 'hours_per_week', CURRENT_DATE + INTERVAL '7 days'),
(1, 'Monthly Task Completion', 'Complete at least 10 tasks this month', 10.0, 'tasks_per_month', CURRENT_DATE + INTERVAL '30 days');                                                