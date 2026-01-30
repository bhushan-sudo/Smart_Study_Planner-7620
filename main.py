"""
Smart Study Planner - Main Flask Application
RESTful API for study planning and progress tracking
"""

from flask import Flask, request, jsonify, send_from_directory, g
from flask_cors import CORS
from datetime import datetime, date, time, timedelta, timezone
import json
import os
import jwt
import bcrypt
from functools import wraps

from db_config import AppConfig, DatabaseConfig
from database import Database
from models import User, Subject, Task, StudySession, TaskProgress, WeeklySummary, StudyGoal, StudyStreak, Notification, FileAttachment, ChatMessage
from planner_logic import SmartPlanner
from rescheduler import TaskRescheduler
from progress_tracker import ProgressTracker
from weekly_summary import WeeklySummaryGenerator
from agent_service import agent_service
from agent_background import background_agent

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.config['SECRET_KEY'] = AppConfig.SECRET_KEY
CORS(app, origins=AppConfig.CORS_ORIGINS)

# Custom JSON encoder for date/time objects
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        if isinstance(obj, time):
            return obj.isoformat()
        return super().default(obj)

app.json_encoder = CustomJSONEncoder

# JWT Secret Key
JWT_SECRET = AppConfig.SECRET_KEY
JWT_ALGORITHM = 'HS256'

# ============= AUTHENTICATION MIDDLEWARE =============
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        try:
            if token.startswith('Bearer '):
                token = token[7:]
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            g.user_id = payload['user_id']
            g.username = payload['username']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        return f(*args, **kwargs)
    return decorated

def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    """Check a password against its hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except (ValueError, AttributeError) as e:
        # Invalid hash format or None value
        logger.error(f'Password check error: {e} - Hash: {hashed[:30] if hashed else "None"}...')
        return False

def generate_token(user_id, username):
    """Generate JWT token"""
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.now(timezone.utc) + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

# ============= AUTHENTICATION ENDPOINTS =============
@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.json
        full_name = data.get('fullName')
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not all([username, email, password]):
            return jsonify({'error': 'Username, email, and password are required'}), 400

        # Check if user already exists
        existing_user = User.get_by_username(username) or User.get_by_email(email)
        if existing_user:
            return jsonify({'error': 'Username or email already exists'}), 409

        # Hash password
        password_hash = hash_password(password)

        # Create user
        user = User.create(
            username=username,
            email=email,
            password_hash=password_hash,
            full_name=full_name
        )

        if user:
            # Generate token
            token = generate_token(user['user_id'], user['username'])
            return jsonify({
                'message': 'User registered successfully',
                'user': {
                    'user_id': user['user_id'],
                    'username': user['username'],
                    'email': user['email'],
                    'username': user['username'],
                    'email': user['email'],
                    'full_name': user['full_name'],
                    'profile_image_url': user.get('profile_image_url')
                },
                'token': token
            }), 201
        else:
            return jsonify({'error': 'Failed to create user'}), 500

    except Exception as e:
        logger.error(f'Registration error: {e}')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Authenticate user and return token"""
    try:
        data = request.json
        identifier = data.get('identifier')  # Can be username or email
        password = data.get('password')

        if not identifier or not password:
            return jsonify({'error': 'Username/email and password are required'}), 400

        # Find user by username or email
        user = User.get_by_username(identifier)
        if not user:
            user = User.get_by_email(identifier)

        if not user:
            logger.warning(f'Login attempt for non-existent user: {identifier}')
            return jsonify({'error': 'Invalid credentials'}), 401

        # Check password
        password_valid = check_password(password, user['password_hash'])
        
        if not password_valid:
            logger.warning(f'Failed login attempt for user: {user["username"]}')
            return jsonify({'error': 'Invalid credentials'}), 401

        # Generate token
        token = generate_token(user['user_id'], user['username'])
        
        logger.info(f'Successful login for user: {user["username"]}')

        return jsonify({
            'message': 'Login successful',
            'user': {
                'user_id': user['user_id'],
                'username': user['username'],
                'email': user['email'],
                'email': user['email'],
                'full_name': user['full_name'],
                'profile_image_url': user.get('profile_image_url')
            },
            'token': token
        }), 200

    except Exception as e:
        logger.error(f'Login error: {e}', exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

# ============= HEALTH CHECK =============
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    db_status = Database.test_connection()
    return jsonify({
        'status': 'healthy' if db_status else 'unhealthy',
        'database': 'connected' if db_status else 'disconnected',
        'timestamp': datetime.now().isoformat()
    })

# ============= USER ENDPOINTS =============
@app.route('/api/users', methods=['GET', 'POST'])
def users():
    """Get all users or create a new user"""
    if request.method == 'GET':
        all_users = User.get_all()
        return jsonify({'users': all_users})
    
    elif request.method == 'POST':
        data = request.json
        user = User.create(
            username=data['username'],
            email=data['email'],
            password_hash=data.get('password_hash', 'demo_hash'),
            full_name=data.get('full_name')
        )
        return jsonify({'user': user}), 201

@app.route('/api/users/<int:user_id>', methods=['GET', 'PUT'])
def user_detail(user_id):
    """Get or update user by ID"""
    if request.method == 'GET':
        user = User.get_by_id(user_id)
        if user:
            return jsonify({'user': user})
        return jsonify({'error': 'User not found'}), 404

    elif request.method == 'PUT':
        # Verify authorization
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Unauthorized'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload['user_id'] != user_id:
                return jsonify({'error': 'Unauthorized'}), 403
        except:
            return jsonify({'error': 'Invalid token'}), 401

        data = request.json
        updates = {}
        
        if 'full_name' in data:
            updates['full_name'] = data['full_name']
        if 'email' in data:
            updates['email'] = data['email']
        if 'profile_image_url' in data:
            updates['profile_image_url'] = data['profile_image_url']
        if 'password' in data and data['password']:
            updates['password_hash'] = hash_password(data['password'])
            
        if not updates:
            return jsonify({'message': 'No changes made'}), 200
            
        # Perform update (using direct SQL for simplicity as User model might not have update method exposed)
        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values())
        values.append(user_id)
        
        query = f"UPDATE users SET {set_clause} WHERE user_id = %s RETURNING user_id, username, email, full_name, profile_image_url, created_at"
        updated_user = Database.fetch_one(query, tuple(values))
        
        if updated_user:
            return jsonify({'user': updated_user, 'message': 'Profile updated successfully'})
        return jsonify({'error': 'Failed to update endpoint'}), 500

# ============= SUBJECT ENDPOINTS =============
@app.route('/api/users/<int:user_id>/subjects', methods=['GET', 'POST'])
def subjects(user_id):
    """Get subjects or create a new subject"""
    if request.method == 'GET':
        user_subjects = Subject.get_by_user(user_id)
        return jsonify({'subjects': user_subjects})
    
    elif request.method == 'POST':
        data = request.json
        subject = Subject.create(
            user_id=user_id,
            subject_name=data['subject_name'],
            color_code=data.get('color_code', '#3B82F6'),
            priority=data.get('priority', 1),
            level=data.get('level'),
            target_grade=data.get('target_grade'),
            current_topic=data.get('current_topic'),
            sub_topics=data.get('sub_topics')
        )
        return jsonify({'subject': subject}), 201

@app.route('/api/subjects/<int:subject_id>', methods=['GET', 'PUT', 'DELETE'])
def subject_detail(subject_id):
    """Get, update, or delete a subject"""
    if request.method == 'GET':
        subject = Subject.get_by_id(subject_id)
        if subject:
            return jsonify({'subject': subject})
        return jsonify({'error': 'Subject not found'}), 404
    
    elif request.method == 'PUT':
        data = request.json
        subject = Subject.update(subject_id, **data)
        if subject:
            return jsonify({'subject': subject})
        return jsonify({'error': 'Subject not found'}), 404
    
    elif request.method == 'DELETE':
        Subject.delete(subject_id)
        return jsonify({'message': 'Subject deleted'}), 200


@app.route('/api/tasks/<int:task_id>', methods=['GET', 'PUT', 'DELETE'])
def task_detail(task_id):
    """Get, update, or delete a task"""
    if request.method == 'GET':
        task = Task.get_by_id(task_id)
        if task:
            return jsonify({'task': task})
        return jsonify({'error': 'Task not found'}), 404
    
    elif request.method == 'PUT':
        data = request.json
        task = Task.update(task_id, **data)
        if task:
            # Background agent integration - check if task was completed
            if data.get('status') == 'completed':
                # Get user_id from task
                task_info = Task.get_by_id(task_id)
                if task_info:
                    agent_suggestion = background_agent.on_task_completed(task_info['user_id'], task)
                    if agent_suggestion:
                        Notification.create(
                            user_id=task_info['user_id'],
                            title="AI Assistant",
                            message=agent_suggestion,
                            notification_type='success'
                        )
            return jsonify({'task': task})
        return jsonify({'error': 'Task not found'}), 404
    
    elif request.method == 'DELETE':
        Task.delete(task_id)
        return jsonify({'message': 'Task deleted'}), 200

@app.route('/api/users/<int:user_id>/tasks/overdue', methods=['GET'])
def overdue_tasks(user_id):
    """Get overdue tasks"""
    tasks = Task.get_overdue_tasks(user_id)
    return jsonify({'tasks': tasks})

# ============= PLANNER ENDPOINTS =============
@app.route('/api/users/<int:user_id>/planner/schedule', methods=['GET'])
def suggest_schedule(user_id):
    """Get suggested schedule"""
    hours_per_day = request.args.get('hours_per_day', 4, type=int)
    days_ahead = request.args.get('days_ahead', 7, type=int)
    
    schedule = SmartPlanner.suggest_schedule(user_id, hours_per_day, days_ahead)
    return jsonify({'schedule': schedule})

@app.route('/api/users/<int:user_id>/planner/recommendations', methods=['GET'])
def daily_recommendations(user_id):
    """Get daily recommendations"""
    target_date_str = request.args.get('date')
    target_date = date.fromisoformat(target_date_str) if target_date_str else None
    
    recommendations = SmartPlanner.get_daily_recommendations(user_id, target_date)
    return jsonify(recommendations)

@app.route('/api/users/<int:user_id>/planner/workload', methods=['GET'])
def workload_analysis(user_id):
    """Analyze workload"""
    days_ahead = request.args.get('days_ahead', 7, type=int)
    analysis = SmartPlanner.analyze_workload(user_id, days_ahead)
    return jsonify(analysis)

# ============= RESCHEDULER ENDPOINTS =============
@app.route('/api/users/<int:user_id>/reschedule/auto', methods=['POST'])
def auto_reschedule(user_id):
    """Run automatic rescheduling"""
    results = TaskRescheduler.auto_reschedule_all(user_id)
    return jsonify(results)

@app.route('/api/users/<int:user_id>/reschedule/balance', methods=['POST'])
def balance_workload(user_id):
    """Balance workload"""
    days_ahead = request.args.get('days_ahead', 7, type=int)
    max_hours = request.args.get('max_hours', 6, type=int)
    
    results = TaskRescheduler.balance_workload(user_id, days_ahead, max_hours)
    return jsonify({'rebalanced': results})

# ============= PROGRESS TRACKING ENDPOINTS =============
@app.route('/api/tasks/<int:task_id>/progress', methods=['POST'])
def update_progress(task_id):
    """Update task progress"""
    data = request.json
    result = ProgressTracker.update_task_progress(
        task_id=task_id,
        user_id=data['user_id'],
        hours_spent=data['hours_spent'],
        completion_percentage=data['completion_percentage'],
        notes=data.get('notes')
    )
    if result:
        return jsonify(result)
    return jsonify({'error': 'Failed to update progress'}), 400

@app.route('/api/tasks/<int:task_id>/analytics', methods=['GET'])
def task_analytics(task_id):
    """Get task analytics"""
    analytics = ProgressTracker.get_task_analytics(task_id)
    if analytics:
        return jsonify(analytics)
    return jsonify({'error': 'Task not found'}), 404

# ============= WEEKLY SUMMARY ENDPOINTS =============
@app.route('/api/users/<int:user_id>/summary/weekly', methods=['GET', 'POST'])
def weekly_summary(user_id):
    """Get or generate weekly summary"""
    if request.method == 'POST':
        week_start_str = request.args.get('week_start')
        week_start = date.fromisoformat(week_start_str) if week_start_str else None
        summary = WeeklySummaryGenerator.generate_summary(user_id, week_start)
        return jsonify({'summary': summary}), 201
    
    else:
        summaries = WeeklySummary.get_by_user(user_id)
        return jsonify({'summaries': summaries})

@app.route('/api/users/<int:user_id>/summary/comparison', methods=['GET'])
def summary_comparison(user_id):
    """Get weekly summary comparison"""
    weeks_back = request.args.get('weeks', 4, type=int)
    comparison = WeeklySummaryGenerator.get_summary_comparison(user_id, weeks_back)
    if comparison:
        return jsonify(comparison)
    return jsonify({'error': 'No summaries found'}), 404

# ============= POMODORO SESSIONS ENDPOINTS =============
@app.route('/api/sessions', methods=['POST'])
@token_required
def create_session():
    """Create a new pomodoro session (not tied to a specific task)"""
    try:
        data = request.json
        user_id = g.user_id
        session_type = data.get('session_type', 'work')
        duration = data.get('duration', 25)  # duration in minutes
        completed_at = data.get('completed_at')

        if not completed_at:
            return jsonify({'error': 'completed_at is required'}), 400

        # Convert duration from minutes to seconds for consistency
        duration_seconds = duration * 60

        session = StudySession.create_pomodoro_session(
            user_id=user_id,
            session_type=session_type,
            duration_minutes=duration,
            completed_at=completed_at
        )

        if session:
            return jsonify({'session': session}), 201
        else:
            return jsonify({'error': 'Failed to create session'}), 500

    except Exception as e:
        logger.error(f'Session creation error: {e}')
        return jsonify({'error': 'Internal server error'}), 500

# ============= FILE UPLOAD ENDPOINTS =============
@app.route('/api/files/upload', methods=['POST'])
@token_required
def upload_file():
    """Upload a file"""
    try:
        user_id = g.user_id

        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Validate file size (10MB limit)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Seek back to beginning

        if file_size > 10 * 1024 * 1024:  # 10MB
            return jsonify({'error': 'File too large (max 10MB)'}), 400

        # Validate file type
        allowed_types = [
            'application/pdf', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain', 'image/jpeg', 'image/png'
        ]

        if file.content_type not in allowed_types:
            return jsonify({'error': 'File type not allowed'}), 400

        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)

        # Generate unique filename
        import uuid
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(upload_dir, unique_filename)

        # Save file
        file.save(file_path)

        # Create database record
        attachment = FileAttachment.create(
            task_id=None,  # Not tied to a specific task
            user_id=user_id,
            filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file.content_type
        )

        if attachment:
            return jsonify({
                'attachment': attachment,
                'message': 'File uploaded successfully'
            }), 201
        else:
            # Clean up file if database insert failed
            os.remove(file_path)
            return jsonify({'error': 'Failed to save file record'}), 500

    except Exception as e:
        logger.error(f'File upload error: {e}')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/files/<int:attachment_id>', methods=['DELETE'])
@token_required
def delete_file(attachment_id):
    """Delete a file"""
    try:
        user_id = g.user_id

        # Get file info
        attachment = FileAttachment.get_by_id(attachment_id)
        if not attachment or attachment['user_id'] != user_id:
            return jsonify({'error': 'File not found'}), 404

        # Delete file from filesystem
        if os.path.exists(attachment['file_path']):
            os.remove(attachment['file_path'])

        # Delete from database
        FileAttachment.delete(attachment_id)

        return jsonify({'message': 'File deleted successfully'})

    except Exception as e:
        logger.error(f'File deletion error: {e}')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/users/<int:user_id>/files', methods=['GET'])
@token_required
def get_user_files(user_id):
    """Get all files uploaded by a user"""
    try:
        files = FileAttachment.get_by_user(user_id)
        return jsonify({'files': files})

    except Exception as e:
        logger.error(f'Get user files error: {e}')
        return jsonify({'error': 'Internal server error'}), 500

# ============= ENHANCED TASKS ENDPOINT =============
@app.route('/api/users/<int:user_id>/tasks', methods=['GET', 'POST'])
@token_required
def tasks(user_id):
    """Get tasks with advanced filtering or create a new task"""
    if request.method == 'GET':
        # Get query parameters
        search = request.args.get('search')
        status = request.args.get('status')
        priority = request.args.get('priority', type=int)
        subject_id = request.args.get('subject_id', type=int)
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        limit = request.args.get('limit', type=int)

        # Build query with filters
        query = """
            SELECT t.*, s.subject_name, s.color_code as subject_color
            FROM tasks t
            LEFT JOIN subjects s ON t.subject_id = s.subject_id
            WHERE t.user_id = %s
        """
        params = [user_id]

        if search:
            query += " AND (t.title ILIKE %s OR t.description ILIKE %s)"
            params.extend([f'%{search}%', f'%{search}%'])

        if status:
            query += " AND t.status = %s"
            params.append(status)

        if priority:
            query += " AND t.priority = %s"
            params.append(priority)

        if subject_id:
            query += " AND t.subject_id = %s"
            params.append(subject_id)

        if date_from:
            query += " AND t.scheduled_date >= %s"
            params.append(date_from)

        if date_to:
            query += " AND t.scheduled_date <= %s"
            params.append(date_to)

        query += " ORDER BY t.created_at DESC"

        if limit:
            query += " LIMIT %s"
            params.append(limit)

        user_tasks = Database.fetch_all(query, params)
        return jsonify({'tasks': user_tasks})

    elif request.method == 'POST':
        data = request.json
        
        # Enhanced Task Creation logic
        # If user provides a NEW subject name, create it on the fly
        if data.get('new_subject_name'):
            # Check if subject already exists
            existing_subject_query = "SELECT * FROM subjects WHERE user_id = %s AND subject_name = %s"
            existing_subject = Database.fetch_one(existing_subject_query, (user_id, data['new_subject_name']))
            
            if existing_subject:
                new_subject = existing_subject
            else:
                new_subject = Subject.create(
                    user_id=user_id,
                    subject_name=data['new_subject_name'],
                    color_code=data.get('new_subject_color', '#3B82F6'),
                    priority=3 # Default priority
                )
            
            if new_subject:
                data['subject_id'] = new_subject['subject_id']
                # Remove temp fields so Task.create doesn't complain
                del data['new_subject_name']
                if 'new_subject_color' in data:
                    del data['new_subject_color']
        
        task = Task.create(user_id=user_id, **data)
        
        # Background agent integration
        agent_suggestion = background_agent.on_task_created(user_id, task)
        if agent_suggestion:
            # Create notification with agent suggestion
            Notification.create(
                user_id=user_id,
                title="AI Assistant",
                message=agent_suggestion,
                notification_type='info'
            )
        
        return jsonify({'task': task, 'agent_suggestion': agent_suggestion}), 201

# ============= STATIC FILES =============
@app.route('/')
def serve_landing():
    """Serve the landing page"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/dashboard')
def serve_dashboard():
    """Serve the dashboard (requires authentication)"""
    return send_from_directory(app.static_folder, 'dashboard.html')

@app.route('/login')
def serve_login():
    """Serve the login page"""
    return send_from_directory(app.static_folder, 'login.html')

@app.route('/register')
def serve_register():
    """Serve the register page"""
    return send_from_directory(app.static_folder, 'register.html')

# ============= ADVANCED FEATURES API =============

# Study Goals API
@app.route('/api/goals', methods=['GET', 'POST'])
@token_required
def goals():
    """Get or create study goals"""
    user_id = g.user_id
    
    if request.method == 'GET':
        goals = StudyGoal.get_by_user(user_id)
        return jsonify({'goals': goals})
    
    elif request.method == 'POST':
        data = request.get_json()
        required_fields = ['title', 'target_value', 'goal_type', 'target_date']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        goal = StudyGoal.create(
            user_id=user_id,
            title=data['title'],
            description=data.get('description', ''),
            target_value=data['target_value'],
            goal_type=data['goal_type'],
            target_date=data['target_date']
        )
        
        if goal:
            return jsonify({'goal': goal}), 201
        else:
            return jsonify({'error': 'Failed to create goal'}), 500

@app.route('/api/goals/<int:goal_id>', methods=['GET', 'PUT', 'DELETE'])
@token_required
def goal_detail(goal_id):
    """Get, update, or delete a specific goal"""
    user_id = g.user_id
    
    goal = StudyGoal.get_by_id(goal_id)
    if not goal or goal['user_id'] != user_id:
        return jsonify({'error': 'Goal not found'}), 404
    
    if request.method == 'GET':
        return jsonify({'goal': goal})
    
    elif request.method == 'PUT':
        data = request.get_json()
        
        if 'current_value' in data:
            goal = StudyGoal.update_progress(goal_id, data['current_value'])
        elif 'status' in data:
            goal = StudyGoal.update_status(goal_id, data['status'])
        else:
            # Update other fields
            return jsonify({'error': 'Invalid update operation'}), 400
        
        if goal:
            return jsonify({'goal': goal})
        else:
            return jsonify({'error': 'Failed to update goal'}), 500
    
    elif request.method == 'DELETE':
        StudyGoal.delete(goal_id)
        return jsonify({'message': 'Goal deleted successfully'})

# Study Streaks API
@app.route('/api/streaks', methods=['GET'])
@token_required
def streaks():
    """Get study streaks for user"""
    user_id = g.user_id
    
    streaks = StudyStreak.get_by_user(user_id)
    current_streak = StudyStreak.get_current_streak(user_id)
    stats = StudyStreak.get_streak_stats(user_id)
    
    return jsonify({
        'streaks': streaks,
        'current_streak': current_streak,
        'stats': stats
    })

@app.route('/api/streaks/log', methods=['POST'])
@token_required
def log_streak():
    """Log study activity for streak tracking"""
    user_id = g.user_id
    data = request.get_json()
    
    streak_date = data.get('date', date.today().isoformat())
    study_hours = data.get('study_hours', 0)
    tasks_completed = data.get('tasks_completed', 0)
    
    streak = StudyStreak.create_or_update(user_id, streak_date, study_hours, tasks_completed)
    
    if streak:
        return jsonify({'streak': streak}), 201
    else:
        return jsonify({'error': 'Failed to log streak'}), 500

# Notifications API
@app.route('/api/notifications', methods=['GET', 'POST'])
@token_required
def notifications():
    """Get or create notifications"""
    user_id = g.user_id
    
    if request.method == 'GET':
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        notifications_list = Notification.get_by_user(user_id, unread_only)
        return jsonify({'notifications': notifications_list})
    
    elif request.method == 'POST':
        data = request.get_json()
        required_fields = ['title', 'message']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        notification = Notification.create(
            user_id=user_id,
            title=data['title'],
            message=data['message'],
            notification_type=data.get('notification_type', 'info'),
            scheduled_for=data.get('scheduled_for')
        )
        
        if notification:
            return jsonify({'notification': notification}), 201
        else:
            return jsonify({'error': 'Failed to create notification'}), 500

@app.route('/api/notifications/<int:notification_id>/read', methods=['PUT'])
@token_required
def mark_notification_read(notification_id):
    """Mark notification as read"""
    user_id = g.user_id
    
    # Verify notification belongs to user
    notifications_list = Notification.get_by_user(user_id)
    notification_ids = [n['notification_id'] for n in notifications_list]
    
    if notification_id not in notification_ids:
        return jsonify({'error': 'Notification not found'}), 404
    
    Notification.mark_as_read(notification_id)
    return jsonify({'message': 'Notification marked as read'})

@app.route('/api/notifications/mark-all-read', methods=['PUT'])
@token_required
def mark_all_notifications_read():
    """Mark all notifications as read"""
    user_id = g.user_id
    Notification.mark_all_read(user_id)
    return jsonify({'message': 'All notifications marked as read'})

# Analytics API
@app.route('/api/analytics/overview', methods=['GET'])
@token_required
def analytics_overview():
    """Get comprehensive analytics overview"""
    user_id = g.user_id
    
    # Get current week data
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    # Weekly statistics
    weekly_tasks = Task.get_by_date_range(user_id, week_start, week_end)
    completed_tasks = [t for t in weekly_tasks if t['status'] == 'completed']
    weekly_sessions = StudySession.get_by_user_and_date_range(user_id, week_start, week_end)
    
    total_weekly_hours = sum(s['duration_hours'] for s in weekly_sessions)
    completion_rate = (len(completed_tasks) / len(weekly_tasks)) * 100 if weekly_tasks else 0
    
    # Monthly statistics
    month_start = today.replace(day=1)
    monthly_tasks = Task.get_by_date_range(user_id, month_start, today)
    monthly_completed = [t for t in monthly_tasks if t['status'] == 'completed']
    monthly_sessions = StudySession.get_by_user_and_date_range(user_id, month_start, today)
    total_monthly_hours = sum(s['duration_hours'] for s in monthly_sessions)
    
    # Subject performance
    subjects = Subject.get_by_user(user_id)
    subject_stats = []
    for subject in subjects:
        subject_tasks = Task.get_by_subject(subject['subject_id'])
        subject_completed = [t for t in subject_tasks if t['status'] == 'completed']
        subject_sessions = StudySession.get_by_subject(subject['subject_id'])
        subject_hours = sum(s['duration_hours'] for s in subject_sessions)
        
        subject_stats.append({
            'subject': subject['name'],
            'tasks_completed': len(subject_completed),
            'total_tasks': len(subject_tasks),
            'study_hours': subject_hours,
            'completion_rate': (len(subject_completed) / len(subject_tasks)) * 100 if subject_tasks else 0
        })
    
    # Goals progress
    goals = StudyGoal.get_by_user(user_id)
    active_goals = [g for g in goals if g['status'] == 'active']
    
    # Streaks
    current_streak = StudyStreak.get_current_streak(user_id)
    streak_stats = StudyStreak.get_streak_stats(user_id)
    
    return jsonify({
        'weekly': {
            'tasks_planned': len(weekly_tasks),
            'tasks_completed': len(completed_tasks),
            'completion_rate': round(completion_rate, 2),
            'study_hours': round(total_weekly_hours, 2)
        },
        'monthly': {
            'tasks_planned': len(monthly_tasks),
            'tasks_completed': len(monthly_completed),
            'study_hours': round(total_monthly_hours, 2)
        },
        'subjects': subject_stats,
        'goals': {
            'active': len(active_goals),
            'total': len(goals)
        },
        'streaks': {
            'current': current_streak,
            'stats': streak_stats
        }
    })

@app.route('/api/analytics/chart-data', methods=['GET'])
@token_required
def analytics_chart_data():
    """Get data for charts and visualizations"""
    user_id = g.user_id
    chart_type = request.args.get('type', 'weekly_progress')
    days = int(request.args.get('days', 30))
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    if chart_type == 'weekly_progress':
        # Daily study hours and task completion
        data = []
        current_date = start_date
        while current_date <= end_date:
            sessions = StudySession.get_by_user_and_date(user_id, current_date)
            tasks = Task.get_completed_by_date(user_id, current_date)
            
            daily_hours = sum(s['duration_hours'] for s in sessions)
            
            data.append({
                'date': current_date.isoformat(),
                'study_hours': round(daily_hours, 2),
                'tasks_completed': len(tasks)
            })
            current_date += timedelta(days=1)
        
        return jsonify({'data': data})
    
    elif chart_type == 'subject_distribution':
        subjects = Subject.get_by_user(user_id)
        data = []
        
        for subject in subjects:
            sessions = StudySession.get_by_subject_and_date_range(subject['subject_id'], start_date, end_date)
            hours = sum(s['duration_hours'] for s in sessions)
            
            if hours > 0:
                data.append({
                    'subject': subject['name'],
                    'hours': round(hours, 2)
                })
        
        return jsonify({'data': data})
    
    return jsonify({'error': 'Invalid chart type'}), 400

# File Attachments API
@app.route('/api/attachments/<int:task_id>', methods=['GET', 'POST'])
@token_required
def task_attachments(task_id):
    """Get or upload attachments for a task"""
    user_id = g.user_id
    
    # Verify task belongs to user
    task = Task.get_by_id(task_id)
    if not task or task['user_id'] != user_id:
        return jsonify({'error': 'Task not found'}), 404
    
    if request.method == 'GET':
        attachments = FileAttachment.get_by_task(task_id)
        return jsonify({'attachments': attachments})
    
    elif request.method == 'POST':
        # File upload handling would go here
        # For now, return not implemented
        return jsonify({'error': 'File upload not implemented yet'}), 501

# ============= CHAPTERS API =============
@app.route('/api/subjects/\u003cint:subject_id\u003e/chapters', methods=['GET', 'POST'])
@token_required
def subject_chapters(subject_id):
    """Get or create chapters for a subject"""
    user_id = g.user_id
    
    # Verify subject belongs to user
    subject = Subject.get_by_id(subject_id)
    if not subject or subject['user_id'] != user_id:
        return jsonify({'error': 'Subject not found'}), 404
    
    if request.method == 'GET':
        query = """
            SELECT * FROM chapters 
            WHERE subject_id = %s 
            ORDER BY chapter_number
        """
        chapters = Database.fetch_all(query, (subject_id,))
        
        # Calculate progress
        total = len(chapters)
        completed = sum(1 for ch in chapters if ch['status'] == 'completed')
        progress = round((completed / total * 100) if total > 0 else 0, 2)
        
        return jsonify({
            'chapters': chapters,
            'total': total,
            'completed': completed,
            'progress': progress
        })
    
    elif request.method == 'POST':
        data = request.json
        query = """
            INSERT INTO chapters (subject_id, chapter_name, chapter_number, difficulty, estimated_hours)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING chapter_id
        """
        chapter_id = Database.execute(query, (
            subject_id,
            data['chapter_name'],
            data['chapter_number'],
            data.get('difficulty', 'MEDIUM'),
            data.get('estimated_hours', 2.0)
        ))
        return jsonify({'chapter_id': chapter_id, 'message': 'Chapter created'}), 201

@app.route('/api/chapters/\u003cint:chapter_id\u003e', methods=['GET', 'PUT', 'DELETE'])
@token_required
def chapter_detail(chapter_id):
    """Get, update, or delete a chapter"""
    user_id = g.user_id
    
    # Get chapter and verify ownership
    query = """
        SELECT c.*, s.user_id 
        FROM chapters c
        JOIN subjects s ON c.subject_id = s.subject_id
        WHERE c.chapter_id = %s
    """
    chapter = Database.fetch_one(query, (chapter_id,))
    
    if not chapter or chapter['user_id'] != user_id:
        return jsonify({'error': 'Chapter not found'}), 404
    
    if request.method == 'GET':
        return jsonify(chapter)
    
    elif request.method == 'PUT':
        data = request.json
        updates = []
        values = []
        
        if 'chapter_name' in data:
            updates.append('chapter_name = %s')
            values.append(data['chapter_name'])
        if 'difficulty' in data:
            updates.append('difficulty = %s')
            values.append(data['difficulty'])
        if 'status' in data:
            updates.append('status = %s')
            values.append(data['status'])
            if data['status'] == 'completed':
                updates.append('completed_date = CURRENT_TIMESTAMP')
        if 'estimated_hours' in data:
            updates.append('estimated_hours = %s')
            values.append(data['estimated_hours'])
        
        if updates:
            values.append(chapter_id)
            query = f"UPDATE chapters SET {', '.join(updates)} WHERE chapter_id = %s"
            Database.execute(query, tuple(values))
        
        return jsonify({'message': 'Chapter updated'})
    
    elif request.method == 'DELETE':
        Database.execute("DELETE FROM chapters WHERE chapter_id = %s", (chapter_id,))
        return jsonify({'message': 'Chapter deleted'})

# ============= BADGES API =============
@app.route('/api/badges', methods=['GET'])
def get_badges():
    """Get all available badges"""
    query = "SELECT * FROM badges ORDER BY badge_level, criteria_value"
    badges = Database.fetch_all(query)
    return jsonify({'badges': badges})

@app.route('/api/users/\u003cint:user_id\u003e/badges', methods=['GET'])
@token_required
def user_badges(user_id):
    """Get badges earned by user"""
    if g.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    query = """
        SELECT b.*, ub.earned_date
        FROM user_badges ub
        JOIN badges b ON ub.badge_id = b.badge_id
        WHERE ub.user_id = %s
        ORDER BY ub.earned_date DESC
    """
    earned_badges = Database.fetch_all(query, (user_id,))
    
    # Get all badges to show locked ones
    all_badges = Database.fetch_all("SELECT * FROM badges ORDER BY badge_level, criteria_value")
    earned_ids = {b['badge_id'] for b in earned_badges}
    locked_badges = [b for b in all_badges if b['badge_id'] not in earned_ids]
    
    return jsonify({
        'earned': earned_badges,
        'locked': locked_badges,
        'total_earned': len(earned_badges)
    })

@app.route('/api/users/\u003cint:user_id\u003e/badges/check', methods=['POST'])
@token_required
def check_and_award_badges(user_id):
    """Check if user has earned any new badges"""
    if g.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    newly_earned = []
    
    # Get all badges
    badges = Database.fetch_all("SELECT * FROM badges")
    
    for badge in badges:
        # Check if already earned
        check_query = "SELECT 1 FROM user_badges WHERE user_id = %s AND badge_id = %s"
        if Database.fetch_one(check_query, (user_id, badge['badge_id'])):
            continue
        
        earned = False
        
        # Check criteria
        if badge['criteria_type'] == 'streak_days':
            # Get current streak
            streak_query = """
                SELECT COUNT(*) as streak FROM study_streaks
                WHERE user_id = %s AND streak_date >= CURRENT_DATE - INTERVAL '%s days'
            """
            result = Database.fetch_one(streak_query, (user_id, badge['criteria_value']))
            if result and result['streak'] >= badge['criteria_value']:
                earned = True
        
        elif badge['criteria_type'] == 'study_hours':
            # Get total study hours
            hours_query = """
                SELECT COALESCE(SUM(duration_minutes), 0) / 60.0 as total_hours
                FROM study_sessions WHERE user_id = %s
            """
            result = Database.fetch_one(hours_query, (user_id,))
            if result and result['total_hours'] >= badge['criteria_value']:
                earned = True
        
        elif badge['criteria_type'] == 'subjects_completed':
            # Count completed subjects (all chapters done)
            completed_query = """
                SELECT COUNT(DISTINCT s.subject_id) as completed
                FROM subjects s
                WHERE s.user_id = %s
                AND NOT EXISTS (
                    SELECT 1 FROM chapters c 
                    WHERE c.subject_id = s.subject_id AND c.status != 'completed'
                )
            """
            result = Database.fetch_one(completed_query, (user_id,))
            if result and result['completed'] >= badge['criteria_value']:
                earned = True
        
        if earned:
            # Award badge
            insert_query = "INSERT INTO user_badges (user_id, badge_id) VALUES (%s, %s)"
            Database.execute(insert_query, (user_id, badge['badge_id']))
            newly_earned.append(badge)
    
    return jsonify({
        'newly_earned': newly_earned,
        'count': len(newly_earned)
    })

# ============= LIVE STATISTICS API =============
@app.route('/api/stats/live', methods=['GET'])
def live_statistics():
    """Get live platform statistics"""
    stats = {}
    
    # Active students (users who studied in last 7 days)
    active_query = """
        SELECT COUNT(DISTINCT user_id) as count
        FROM study_sessions
        WHERE start_time >= CURRENT_DATE - INTERVAL '7 days'
    """
    result = Database.fetch_one(active_query)
    stats['active_students'] = result['count'] if result else 0
    
    # Total study sessions
    sessions_query = "SELECT COUNT(*) as count FROM study_sessions"
    result = Database.fetch_one(sessions_query)
    stats['study_sessions'] = result['count'] if result else 0
    
    # Goal achievement rate
    goals_query = """
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
        FROM study_goals
        WHERE target_date >= CURRENT_DATE - INTERVAL '30 days'
    """
    result = Database.fetch_one(goals_query)
    if result and result['total'] > 0:
        stats['goal_achievement'] = round((result['completed'] / result['total']) * 100, 1)
    else:
        stats['goal_achievement'] = 95.0  # Default
    
    # Average user rating (simulated for now)
    stats['user_rating'] = 4.8
    
    return jsonify(stats)

# ============= USER PREFERENCES API =============
@app.route('/api/users/\u003cint:user_id\u003e/preferences', methods=['GET', 'PUT'])
@token_required
def user_preferences(user_id):
    """Get or update user preferences"""
    if g.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'GET':
        query = "SELECT * FROM user_preferences WHERE user_id = %s"
        prefs = Database.fetch_one(query, (user_id,))
        
        if not prefs:
            # Create default preferences
            insert_query = "INSERT INTO user_preferences (user_id) VALUES (%s) RETURNING *"
            prefs = Database.fetch_one(insert_query, (user_id,))
        
        return jsonify(prefs)
    
    elif request.method == 'PUT':
        data = request.json
        updates = []
        values = []
        
        allowed_fields = [
            'pomodoro_work_duration', 'pomodoro_break_duration', 
            'pomodoro_long_break_duration', 'daily_study_goal_hours',
            'notifications_enabled', 'theme'
        ]
        
        for field in allowed_fields:
            if field in data:
                updates.append(f'{field} = %s')
                values.append(data[field])
        
        if updates:
            updates.append('updated_at = CURRENT_TIMESTAMP')
            values.append(user_id)
            query = f"""
                INSERT INTO user_preferences (user_id, {', '.join([f.split(' = ')[0] for f in updates if 'updated_at' not in f])})
                VALUES (%s, {', '.join(['%s'] * (len(values) - 1))})
                ON CONFLICT (user_id) DO UPDATE SET {', '.join(updates)}
            """
            Database.execute(query, tuple([user_id] + values[:-1] + [user_id]))
        
        return jsonify({'message': 'Preferences updated'})

# ============= CALENDAR & TASKS API =============
@app.route('/api/users/\u003cint:user_id\u003e/calendar', methods=['GET'])
@token_required
def calendar_tasks(user_id):
    """Get tasks for calendar view"""
    if g.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    month = request.args.get('month')  # Format: YYYY-MM
    
    if month:
        query = """
            SELECT t.*, s.subject_name, s.color_code
            FROM tasks t
            LEFT JOIN subjects s ON t.subject_id = s.subject_id
            WHERE t.user_id = %s 
            AND DATE_TRUNC('month', t.scheduled_date) = DATE_TRUNC('month', %s::date)
            ORDER BY t.scheduled_date, t.scheduled_time
        """
        tasks = Database.fetch_all(query, (user_id, f"{month}-01"))
    else:
        # Get current month
        query = """
            SELECT t.*, s.subject_name, s.color_code
            FROM tasks t
            LEFT JOIN subjects s ON t.subject_id = s.subject_id
            WHERE t.user_id = %s 
            AND DATE_TRUNC('month', t.scheduled_date) = DATE_TRUNC('month', CURRENT_DATE)
            ORDER BY t.scheduled_date, t.scheduled_time
        """
        tasks = Database.fetch_all(query, (user_id,))
    
    return jsonify({'tasks': tasks})

@app.route('/api/tasks/\u003cint:task_id\u003e/reschedule', methods=['PUT'])
@token_required
def reschedule_task(task_id):
    """Reschedule a task"""
    user_id = g.user_id
    
    task = Task.get_by_id(task_id)
    if not task or task['user_id'] != user_id:
        return jsonify({'error': 'Task not found'}), 404
    
    data = request.json
    new_date = data.get('scheduled_date')
    new_time = data.get('scheduled_time')
    
    if not new_date:
        return jsonify({'error': 'scheduled_date required'}), 400
    
    query = """
        UPDATE tasks 
        SET scheduled_date = %s, scheduled_time = %s, status = 'rescheduled', updated_at = CURRENT_TIMESTAMP
        WHERE task_id = %s
    """
    Database.execute(query, (new_date, new_time, task_id))
    
    return jsonify({'message': 'Task rescheduled'})

# ============= ERROR HANDLERS =============
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

# ============= AI AGENT ENDPOINTS =============
@app.route('/api/agent/chat', methods=['POST'])
@token_required
def agent_chat():
    """Send a message to the AI study assistant"""
    try:
        user_id = g.user_id
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        user_message = data['message'].strip()
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Get recent chat history for context
        chat_history = ChatMessage.get_recent(user_id, limit=10)
        
        # Save user message
        ChatMessage.create(user_id, 'user', user_message)
        
        # Get AI response
        response_data = agent_service.chat(user_id, user_message, chat_history)
        
        # Save assistant response if successful
        if not response_data.get('error'):
            ChatMessage.create(user_id, 'assistant', response_data['response'])
        
        return jsonify({
            'response': response_data['response'],
            'context_used': response_data.get('context_used', {}),
            'error': response_data.get('error', False)
        }), 200
        
    except Exception as e:
        logger.error(f'Agent chat error: {e}', exc_info=True)
        return jsonify({'error': 'Failed to process message'}), 500

@app.route('/api/agent/history', methods=['GET'])
@token_required
def agent_history():
    """Get chat history for the current user"""
    try:
        user_id = g.user_id
        limit = request.args.get('limit', 50, type=int)
        
        # Limit max to 100 messages
        limit = min(limit, 100)
        
        messages = ChatMessage.get_by_user(user_id, limit=limit)
        
        return jsonify({
            'messages': messages,
            'count': len(messages)
        }), 200
        
    except Exception as e:
        logger.error(f'Get agent history error: {e}')
        return jsonify({'error': 'Failed to retrieve chat history'}), 500

@app.route('/api/agent/history', methods=['DELETE'])
@token_required
def clear_agent_history():
    """Clear chat history for the current user"""
    try:
        user_id = g.user_id
        ChatMessage.delete_all(user_id)
        
        return jsonify({'message': 'Chat history cleared successfully'}), 200
        
    except Exception as e:
        logger.error(f'Clear agent history error: {e}')
        return jsonify({'error': 'Failed to clear chat history'}), 500

@app.route('/api/agent/suggestions', methods=['GET'])
@token_required
def agent_suggestions():
    """Get proactive study suggestions from the AI agent"""
    try:
        user_id = g.user_id
        suggestions = agent_service.get_proactive_suggestions(user_id)
        
        return jsonify({
            'suggestions': suggestions,
            'count': len(suggestions)
        }), 200
        
    except Exception as e:
        logger.error(f'Get agent suggestions error: {e}')
        return jsonify({'error': 'Failed to get suggestions'}), 500

@app.route('/api/agent/insights', methods=['GET'])
@token_required
def agent_daily_insights():
    """Get daily insights and smart recommendations from AI agent"""
    try:
        user_id = g.user_id
        
        # Get daily status insights
        daily_insights = background_agent.check_daily_status(user_id)
        
        # Get smart recommendations based on patterns
        recommendations = background_agent.get_smart_recommendations(user_id)
        
        return jsonify({
            'insights': daily_insights,
            'recommendations': recommendations,
            'total_count': len(daily_insights) + len(recommendations)
        }), 200
        
    except Exception as e:
        logger.error(f'Get agent insights error: {e}')
        return jsonify({'error': 'Failed to get insights'}), 500

@app.route('/api/agent/generate-plan', methods=['POST'])
@token_required
def generate_study_plan():
    """Generate a study plan using AI"""
    try:
        user_id = g.user_id
        data = request.get_json()
        
        goal = data.get('goal')
        timeframe = data.get('timeframe_days', 7)
        auto_create = data.get('auto_create_tasks', False)
        
        if not goal:
            return jsonify({'error': 'Goal description is required'}), 400
            
        result = agent_service.generate_study_plan(user_id, goal, timeframe)
        
        if result.get('error'):
            return jsonify({'error': result['response']}), 500
            
        # Optional: Automated task creation
        created_tasks = []
        if auto_create and result.get('tasks_to_create'):
            for task_data in result['tasks_to_create']:
                # Basic validation and creation
                new_task = Task.create(
                    user_id=user_id,
                    title=task_data.get('title', 'AI Suggested Task'),
                    estimated_hours=task_data.get('estimated_hours', 1.0),
                    task_type=task_data.get('task_type', 'study'),
                    priority=task_data.get('priority', 3),
                    status='pending'
                )
                created_tasks.append(new_task)
                
        return jsonify({
            'response': result['response'],
            'tasks_created': len(created_tasks),
            'tasks': created_tasks
        }), 200
        
    except Exception as e:
        logger.error(f'Generate study plan error: {e}', exc_info=True)
        return jsonify({'error': 'Failed to generate study plan'}), 500



# ============= MAIN =============
if __name__ == '__main__':
    logger.info("Starting Smart Study Planner API")
    logger.info(f"Database: {DatabaseConfig.DB_NAME} at {DatabaseConfig.DB_HOST}:{DatabaseConfig.DB_PORT}")
    
    # Test database connection
    if Database.test_connection():
        logger.info("Database connection successful")
    else:
        logger.error("Database connection failed")
    
    app.run(
        host=AppConfig.HOST,
        port=AppConfig.PORT,
        debug=AppConfig.DEBUG
    )
