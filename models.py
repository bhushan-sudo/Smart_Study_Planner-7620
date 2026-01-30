"""
Data models for Smart Study Planner
ORM-like models for database operations
"""

from database import Database
from datetime import datetime, date, time
import json

class User:
    """User model"""
    
    @staticmethod
    def create(username, email, password_hash, full_name=None):
        """Create a new user"""
        query = """
            INSERT INTO users (username, email, password_hash, full_name, profile_image_url)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING user_id, username, email, full_name, profile_image_url, created_at
        """
        return Database.fetch_one(query, (username, email, password_hash, full_name, None))
    
    @staticmethod
    def get_by_id(user_id):
        """Get user by ID"""
        query = "SELECT * FROM users WHERE user_id = %s"
        return Database.fetch_one(query, (user_id,))
    
    @staticmethod
    def get_by_username(username):
        """Get user by username"""
        query = "SELECT * FROM users WHERE username = %s"
        return Database.fetch_one(query, (username,))
    
    @staticmethod
    def get_by_email(email):
        """Get user by email"""
        query = "SELECT * FROM users WHERE email = %s"
        return Database.fetch_one(query, (email,))
    
    @staticmethod
    def get_all():
        """Get all users"""
        query = "SELECT user_id, username, email, full_name, profile_image_url, created_at FROM users"
        return Database.fetch_all(query)

class Subject:
    """Subject model"""
    
    @staticmethod
    def create(user_id, subject_name, color_code='#3B82F6', priority=1, level=None, target_grade=None, current_topic=None, sub_topics=None):
        """Create a new subject"""
        query = """
            INSERT INTO subjects (user_id, subject_name, color_code, priority, level, target_grade, current_topic, sub_topics)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING subject_id, user_id, subject_name, color_code, priority, level, target_grade, current_topic, sub_topics, created_at
        """
        return Database.fetch_one(query, (user_id, subject_name, color_code, priority, level, target_grade, current_topic, sub_topics))
    
    @staticmethod
    def get_by_user(user_id):
        """Get all subjects for a user"""
        query = "SELECT * FROM subjects WHERE user_id = %s ORDER BY priority DESC, subject_name"
        return Database.fetch_all(query, (user_id,))
    
    @staticmethod
    def get_by_id(subject_id):
        """Get subject by ID"""
        query = "SELECT * FROM subjects WHERE subject_id = %s"
        return Database.fetch_one(query, (subject_id,))
    
    @staticmethod
    def update(subject_id, **kwargs):
        """Update subject"""
        allowed_fields = ['subject_name', 'color_code', 'priority', 'level', 'target_grade', 'current_topic', 'sub_topics']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return None
        
        set_clause = ', '.join([f"{k} = %s" for k in updates.keys()])
        query = f"UPDATE subjects SET {set_clause} WHERE subject_id = %s RETURNING *"
        params = list(updates.values()) + [subject_id]
        
        return Database.fetch_one(query, params)
    
    @staticmethod
    def delete(subject_id):
        """Delete subject"""
        query = "DELETE FROM subjects WHERE subject_id = %s"
        return Database.execute_query(query, (subject_id,), fetch=False)

class Task:
    """Task model"""
    
    @staticmethod
    def create(user_id, title, **kwargs):
        """Create a new task"""
        fields = ['user_id', 'title']
        values = [user_id, title]
        
        optional_fields = {
            'subject_id': kwargs.get('subject_id'),
            'description': kwargs.get('description'),
            'task_type': kwargs.get('task_type', 'study'),
            'priority': kwargs.get('priority', 1),
            'estimated_hours': kwargs.get('estimated_hours', 1.0),
            'deadline': kwargs.get('deadline'),
            'scheduled_date': kwargs.get('scheduled_date'),
            'scheduled_time': kwargs.get('scheduled_time'),
            'status': kwargs.get('status', 'pending'),
            'is_recurring': kwargs.get('is_recurring', False),
            'recurrence_pattern': kwargs.get('recurrence_pattern')
        }
        
        for field, value in optional_fields.items():
            if value is not None:
                fields.append(field)
                values.append(value)
        
        placeholders = ', '.join(['%s'] * len(values))
        query = f"""
            INSERT INTO tasks ({', '.join(fields)})
            VALUES ({placeholders})
            RETURNING *
        """
        
        return Database.fetch_one(query, values)
    
    @staticmethod
    def get_by_id(task_id):
        """Get task by ID"""
        query = """
            SELECT t.*, s.subject_name, s.color_code
            FROM tasks t
            LEFT JOIN subjects s ON t.subject_id = s.subject_id
            WHERE t.task_id = %s
        """
        return Database.fetch_one(query, (task_id,))
    
    @staticmethod
    def get_by_user(user_id, status=None, limit=None):
        """Get tasks for a user"""
        query = """
            SELECT t.*, s.subject_name, s.color_code
            FROM tasks t
            LEFT JOIN subjects s ON t.subject_id = s.subject_id
            WHERE t.user_id = %s
        """
        params = [user_id]
        
        if status:
            query += " AND t.status = %s"
            params.append(status)
        
        query += " ORDER BY t.deadline ASC NULLS LAST, t.priority DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        return Database.fetch_all(query, params)
    
    @staticmethod
    def get_by_date_range(user_id, start_date, end_date):
        """Get tasks within a date range"""
        query = """
            SELECT t.*, s.subject_name, s.color_code
            FROM tasks t
            LEFT JOIN subjects s ON t.subject_id = s.subject_id
            WHERE t.user_id = %s AND t.scheduled_date BETWEEN %s AND %s
            ORDER BY t.scheduled_date, t.scheduled_time
        """
        return Database.fetch_all(query, (user_id, start_date, end_date))
    
    @staticmethod
    def update(task_id, **kwargs):
        """Update task"""
        allowed_fields = [
            'title', 'description', 'subject_id', 'task_type', 'priority',
            'estimated_hours', 'deadline', 'scheduled_date', 'scheduled_time',
            'status', 'completion_percentage', 'actual_hours', 'completed_at'
        ]
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return None
        
        set_clause = ', '.join([f"{k} = %s" for k in updates.keys()])
        query = f"UPDATE tasks SET {set_clause} WHERE task_id = %s RETURNING *"
        params = list(updates.values()) + [task_id]
        
        return Database.fetch_one(query, params)
    
    @staticmethod
    def delete(task_id):
        """Delete task"""
        query = "DELETE FROM tasks WHERE task_id = %s"
        return Database.execute_query(query, (task_id,), fetch=False)
    
    @staticmethod
    def get_overdue_tasks(user_id):
        """Get overdue tasks"""
        query = """
            SELECT t.*, s.subject_name, s.color_code
            FROM tasks t
            LEFT JOIN subjects s ON t.subject_id = s.subject_id
            WHERE t.user_id = %s 
            AND t.status NOT IN ('completed', 'rescheduled')
            AND t.deadline < NOW()
            ORDER BY t.deadline
        """
        return Database.fetch_all(query, (user_id,))

class StudySession:
    """Study session model"""
    
    @staticmethod
    def create(task_id, user_id, start_time, end_time=None, notes=None, focus_score=None, session_type='study'):
        """Create a new study session"""
        duration_minutes = None
        if end_time and start_time:
            duration = end_time - start_time
            duration_minutes = int(duration.total_seconds() / 60)
        
        query = """
            INSERT INTO study_sessions (task_id, user_id, start_time, end_time, duration_minutes, notes, focus_score, session_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        return Database.fetch_one(query, (task_id, user_id, start_time, end_time, duration_minutes, notes, focus_score, session_type))
    
    @staticmethod
    def get_by_task(task_id):
        """Get all sessions for a task"""
        query = "SELECT * FROM study_sessions WHERE task_id = %s ORDER BY start_time DESC"
        return Database.fetch_all(query, (task_id,))
    
    @staticmethod
    def create_pomodoro_session(user_id, session_type, duration_minutes, completed_at, notes=None):
        """Create a pomodoro session (without task_id)"""
        query = """
            INSERT INTO study_sessions (task_id, user_id, start_time, duration_minutes, session_type, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        return Database.fetch_one(query, (None, user_id, completed_at, duration_minutes, session_type, notes))
    
    @staticmethod
    def get_by_user_and_date_range(user_id, start_date, end_date):
        """Get sessions for a user within a date range"""
        query = """
            SELECT * FROM study_sessions 
            WHERE user_id = %s AND start_time >= %s AND start_time <= %s 
            ORDER BY start_time DESC
        """
        return Database.fetch_all(query, (user_id, start_date, end_date))
    
    @staticmethod
    def get_by_user_and_date(user_id, date):
        """Get sessions for a user on a specific date"""
        start_of_day = datetime.combine(date, time.min)
        end_of_day = datetime.combine(date, time.max)
        return StudySession.get_by_user_and_date_range(user_id, start_of_day, end_of_day)

class TaskProgress:
    """Task progress model"""
    
    @staticmethod
    def create(task_id, user_id, progress_date, hours_spent, completion_delta, notes=None):
        """Create a progress entry"""
        query = """
            INSERT INTO task_progress (task_id, user_id, progress_date, hours_spent, completion_delta, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        return Database.fetch_one(query, (task_id, user_id, progress_date, hours_spent, completion_delta, notes))
    
    @staticmethod
    def get_by_task(task_id):
        """Get progress for a task"""
        query = "SELECT * FROM task_progress WHERE task_id = %s ORDER BY progress_date DESC"
        return Database.fetch_all(query, (task_id,))

class WeeklySummary:
    """Weekly summary model"""
    
    @staticmethod
    def create(user_id, week_start_date, week_end_date, summary_data):
        """Create or update weekly summary"""
        query = """
            INSERT INTO weekly_summaries 
            (user_id, week_start_date, week_end_date, total_tasks_planned, total_tasks_completed,
             total_hours_planned, total_hours_actual, completion_rate, productivity_score, summary_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, week_start_date) 
            DO UPDATE SET
                total_tasks_planned = EXCLUDED.total_tasks_planned,
                total_tasks_completed = EXCLUDED.total_tasks_completed,
                total_hours_planned = EXCLUDED.total_hours_planned,
                total_hours_actual = EXCLUDED.total_hours_actual,
                completion_rate = EXCLUDED.completion_rate,
                productivity_score = EXCLUDED.productivity_score,
                summary_data = EXCLUDED.summary_data
            RETURNING *
        """
        params = (
            user_id, week_start_date, week_end_date,
            summary_data.get('total_tasks_planned', 0),
            summary_data.get('total_tasks_completed', 0),
            summary_data.get('total_hours_planned', 0),
            summary_data.get('total_hours_actual', 0),
            summary_data.get('completion_rate', 0),
            summary_data.get('productivity_score', 0),
            json.dumps(summary_data)
        )
        return Database.fetch_one(query, params)
    
    @staticmethod
    def get_by_user(user_id, limit=10):
        """Get summaries for a user"""
        query = """
            SELECT * FROM weekly_summaries 
            WHERE user_id = %s 
            ORDER BY week_start_date DESC 
            LIMIT %s
        """
        return Database.fetch_all(query, (user_id, limit))
    
    @staticmethod
    def get_by_week(user_id, week_start_date):
        """Get summary for a specific week"""
        query = """
            SELECT * FROM weekly_summaries 
            WHERE user_id = %s AND week_start_date = %s
        """
        return Database.fetch_one(query, (user_id, week_start_date))


class StudyGoal:
    """Study Goals model"""

    @staticmethod
    def create(user_id, title, description, target_value, goal_type, target_date):
        """Create a new study goal"""
        query = """
            INSERT INTO study_goals (user_id, title, description, target_value, goal_type, target_date)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING goal_id, title, description, target_value, current_value, goal_type, target_date, status, created_at
        """
        return Database.fetch_one(query, (user_id, title, description, target_value, goal_type, target_date))

    @staticmethod
    def get_by_user(user_id):
        """Get all goals for a user"""
        query = """
            SELECT * FROM study_goals
            WHERE user_id = %s
            ORDER BY target_date ASC, created_at DESC
        """
        return Database.fetch_all(query, (user_id,))

    @staticmethod
    def get_by_id(goal_id):
        """Get goal by ID"""
        query = "SELECT * FROM study_goals WHERE goal_id = %s"
        return Database.fetch_one(query, (goal_id,))

    @staticmethod
    def update_progress(goal_id, current_value):
        """Update goal progress"""
        query = """
            UPDATE study_goals
            SET current_value = %s, updated_at = CURRENT_TIMESTAMP
            WHERE goal_id = %s
            RETURNING *
        """
        return Database.fetch_one(query, (current_value, goal_id))

    @staticmethod
    def update_status(goal_id, status):
        """Update goal status"""
        query = """
            UPDATE study_goals
            SET status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE goal_id = %s
            RETURNING *
        """
        return Database.fetch_one(query, (status, goal_id))

    @staticmethod
    def delete(goal_id):
        """Delete a goal"""
        query = "DELETE FROM study_goals WHERE goal_id = %s"
        Database.execute_query(query, (goal_id,))


class StudyStreak:
    """Study Streaks model"""

    @staticmethod
    def create_or_update(user_id, streak_date, study_hours=0, tasks_completed=0):
        """Create or update a study streak for a date"""
        query = """
            INSERT INTO study_streaks (user_id, streak_date, study_hours, tasks_completed)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, streak_date)
            DO UPDATE SET
                study_hours = study_streaks.study_hours + EXCLUDED.study_hours,
                tasks_completed = study_streaks.tasks_completed + EXCLUDED.tasks_completed
            RETURNING *
        """
        return Database.fetch_one(query, (user_id, streak_date, study_hours, tasks_completed))

    @staticmethod
    def get_by_user(user_id, limit=30):
        """Get recent streaks for a user"""
        query = """
            SELECT * FROM study_streaks
            WHERE user_id = %s
            ORDER BY streak_date DESC
            LIMIT %s
        """
        return Database.fetch_all(query, (user_id, limit))

    @staticmethod
    def get_current_streak(user_id):
        """Calculate current study streak"""
        query = """
            SELECT COUNT(*) as streak_days
            FROM (
                SELECT streak_date,
                       streak_date - ROW_NUMBER() OVER (ORDER BY streak_date) * INTERVAL '1 day' as grp
                FROM study_streaks
                WHERE user_id = %s AND study_hours > 0
                ORDER BY streak_date DESC
            ) t
            GROUP BY grp
            ORDER BY MIN(streak_date) DESC
            LIMIT 1
        """
        result = Database.fetch_one(query, (user_id,))
        return result['streak_days'] if result else 0

    @staticmethod
    def get_streak_stats(user_id):
        """Get comprehensive streak statistics"""
        query = """
            SELECT
                COUNT(*) as total_study_days,
                SUM(study_hours) as total_hours,
                AVG(study_hours) as avg_daily_hours,
                MAX(study_hours) as max_daily_hours,
                SUM(tasks_completed) as total_tasks_completed
            FROM study_streaks
            WHERE user_id = %s AND study_hours > 0
        """
        return Database.fetch_one(query, (user_id,))


class Notification:
    """Notifications model"""

    @staticmethod
    def create(user_id, title, message, notification_type='info', scheduled_for=None):
        """Create a new notification"""
        query = """
            INSERT INTO notifications (user_id, title, message, notification_type, scheduled_for)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING notification_id, title, message, notification_type, is_read, scheduled_for, created_at
        """
        return Database.fetch_one(query, (user_id, title, message, notification_type, scheduled_for))

    @staticmethod
    def get_by_user(user_id, unread_only=False, limit=20):
        """Get notifications for a user"""
        if unread_only:
            query = """
                SELECT * FROM notifications
                WHERE user_id = %s AND is_read = FALSE
                ORDER BY created_at DESC
                LIMIT %s
            """
        else:
            query = """
                SELECT * FROM notifications
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """
        return Database.fetch_all(query, (user_id, limit))

    @staticmethod
    def mark_as_read(notification_id):
        """Mark notification as read"""
        query = "UPDATE notifications SET is_read = TRUE WHERE notification_id = %s"
        Database.execute_query(query, (notification_id,))

    @staticmethod
    def mark_all_read(user_id):
        """Mark all notifications as read for a user"""
        query = "UPDATE notifications SET is_read = TRUE WHERE user_id = %s"
        Database.execute_query(query, (user_id,))

    @staticmethod
    def delete(notification_id):
        """Delete a notification"""
        query = "DELETE FROM notifications WHERE notification_id = %s"
        Database.execute_query(query, (notification_id,))


class FileAttachment:
    """File Attachments model"""

    @staticmethod
    def create(task_id, user_id, filename, file_path, file_size, file_type):
        """Create a new file attachment"""
        query = """
            INSERT INTO file_attachments (task_id, user_id, filename, file_path, file_size, file_type)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING attachment_id, filename, file_path, file_size, file_type, uploaded_at
        """
        return Database.fetch_one(query, (task_id, user_id, filename, file_path, file_size, file_type))

    @staticmethod
    def get_by_task(task_id):
        """Get attachments for a task"""
        query = """
            SELECT * FROM file_attachments
            WHERE task_id = %s
            ORDER BY uploaded_at DESC
        """
        return Database.fetch_all(query, (task_id,))

    @staticmethod
    def get_by_id(attachment_id):
        """Get attachment by ID"""
        query = "SELECT * FROM file_attachments WHERE attachment_id = %s"
        return Database.fetch_one(query, (attachment_id,))

    @staticmethod
    def delete(attachment_id):
        """Delete a file attachment"""
        query = "DELETE FROM file_attachments WHERE attachment_id = %s"
        Database.execute_query(query, (attachment_id,))

    @staticmethod
    def get_by_user(user_id):
        """Get all attachments for a user"""
        query = """
            SELECT * FROM file_attachments
            WHERE user_id = %s
            ORDER BY uploaded_at DESC
        """
        return Database.fetch_all(query, (user_id,))


class ChatMessage:
    """Chat Messages model for AI agent conversations"""

    @staticmethod
    def create(user_id, role, content):
        """Create a new chat message"""
        query = """
            INSERT INTO chat_messages (user_id, role, content)
            VALUES (%s, %s, %s)
            RETURNING message_id, user_id, role, content, created_at
        """
        return Database.fetch_one(query, (user_id, role, content))

    @staticmethod
    def get_by_user(user_id, limit=50):
        """Get chat history for a user"""
        query = """
            SELECT * FROM chat_messages
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """
        messages = Database.fetch_all(query, (user_id, limit))
        # Reverse to get chronological order
        return list(reversed(messages)) if messages else []

    @staticmethod
    def get_recent(user_id, limit=10):
        """Get recent chat messages for context"""
        query = """
            SELECT * FROM chat_messages
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """
        messages = Database.fetch_all(query, (user_id, limit))
        return list(reversed(messages)) if messages else []

    @staticmethod
    def delete_all(user_id):
        """Delete all chat messages for a user"""
        query = "DELETE FROM chat_messages WHERE user_id = %s"
        Database.execute_query(query, (user_id,))

    @staticmethod
    def delete_old(user_id, days=30):
        """Delete messages older than specified days"""
        query = """
            DELETE FROM chat_messages
            WHERE user_id = %s AND created_at < NOW() - INTERVAL '%s days'
        """
        Database.execute_query(query, (user_id, days))

