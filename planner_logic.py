"""
Smart Planner Logic
Intelligent task scheduling and planning algorithms
"""

from datetime import datetime, date, timedelta
from models import Task, Subject
import logging

logger = logging.getLogger(__name__)

class SmartPlanner:
    """Smart planning and scheduling logic"""
    
    @staticmethod
    def calculate_priority_score(task):
        """
        Calculate a priority score for task scheduling
        Considers: deadline urgency, task priority, estimated hours
        """
        score = 0
        
        # Base priority (1-5)
        score += task.get('priority', 1) * 20
        
        # Deadline urgency
        if task.get('deadline'):
            deadline = task['deadline']
            if isinstance(deadline, str):
                deadline = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
            
            days_until_deadline = (deadline - datetime.now()).days
            
            if days_until_deadline < 0:
                score += 100  # Overdue - highest priority
            elif days_until_deadline == 0:
                score += 80  # Due today
            elif days_until_deadline == 1:
                score += 60  # Due tomorrow
            elif days_until_deadline <= 3:
                score += 40  # Due within 3 days
            elif days_until_deadline <= 7:
                score += 20  # Due within a week
            else:
                score += 10  # Due later
        
        # Task type importance
        task_type_weights = {
            'exam': 30,
            'assignment': 25,
            'revision': 15,
            'study': 10
        }
        score += task_type_weights.get(task.get('task_type', 'study'), 10)
        
        # Completion percentage (prioritize incomplete tasks)
        completion = task.get('completion_percentage', 0)
        if completion < 25:
            score += 15
        elif completion < 50:
            score += 10
        elif completion < 75:
            score += 5
        
        return score
    
    @staticmethod
    def suggest_schedule(user_id, available_hours_per_day=4, days_ahead=7):
        """
        Suggest an optimal schedule for upcoming tasks
        Returns a dictionary with date -> list of tasks
        """
        # Get pending tasks
        pending_tasks = Task.get_by_user(user_id, status='pending')
        
        if not pending_tasks:
            return {}
        
        # Calculate priority scores
        tasks_with_scores = []
        for task in pending_tasks:
            score = SmartPlanner.calculate_priority_score(task)
            tasks_with_scores.append({
                'task': task,
                'score': score
            })
        
        # Sort by priority score (descending)
        tasks_with_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Create schedule
        schedule = {}
        current_date = date.today()
        
        for i in range(days_ahead):
            schedule_date = current_date + timedelta(days=i)
            schedule[schedule_date.isoformat()] = []
        
        # Distribute tasks across days
        current_day_index = 0
        remaining_hours = {day: available_hours_per_day for day in schedule.keys()}
        
        for item in tasks_with_scores:
            task = item['task']
            estimated_hours = float(task.get('estimated_hours', 1.0))
            
            # Find a day with enough hours
            scheduled = False
            attempts = 0
            
            while not scheduled and attempts < days_ahead:
                day_key = list(schedule.keys())[current_day_index]
                
                if remaining_hours[day_key] >= estimated_hours:
                    schedule[day_key].append({
                        'task_id': task['task_id'],
                        'title': task['title'],
                        'subject_name': task.get('subject_name'),
                        'estimated_hours': estimated_hours,
                        'priority': task.get('priority'),
                        'deadline': task.get('deadline').isoformat() if task.get('deadline') else None
                    })
                    remaining_hours[day_key] -= estimated_hours
                    scheduled = True
                else:
                    current_day_index = (current_day_index + 1) % days_ahead
                    attempts += 1
            
            if not scheduled:
                logger.warning(f"Could not schedule task {task['task_id']} - insufficient time")
        
        return schedule
    
    @staticmethod
    def optimize_study_time(tasks, total_hours_available):
        """
        Optimize study time allocation using a greedy algorithm
        Returns recommended hours for each task
        """
        if not tasks or total_hours_available <= 0:
            return {}
        
        # Calculate priority scores
        tasks_with_scores = []
        for task in tasks:
            score = SmartPlanner.calculate_priority_score(task)
            estimated_hours = float(task.get('estimated_hours', 1.0))
            completion = task.get('completion_percentage', 0)
            remaining_hours = estimated_hours * (100 - completion) / 100
            
            tasks_with_scores.append({
                'task_id': task['task_id'],
                'score': score,
                'remaining_hours': remaining_hours,
                'title': task['title']
            })
        
        # Sort by score
        tasks_with_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Allocate time
        allocation = {}
        remaining_time = total_hours_available
        
        for task_info in tasks_with_scores:
            if remaining_time <= 0:
                break
            
            task_id = task_info['task_id']
            needed_hours = task_info['remaining_hours']
            
            # Allocate minimum of needed hours or remaining time
            allocated_hours = min(needed_hours, remaining_time)
            
            if allocated_hours > 0:
                allocation[task_id] = {
                    'allocated_hours': round(allocated_hours, 2),
                    'title': task_info['title'],
                    'priority_score': task_info['score']
                }
                remaining_time -= allocated_hours
        
        return allocation
    
    @staticmethod
    def get_daily_recommendations(user_id, target_date=None):
        """
        Get daily task recommendations
        """
        if target_date is None:
            target_date = date.today()
        
        # Get tasks scheduled for this date
        scheduled_tasks = Task.get_by_date_range(user_id, target_date, target_date)
        
        # Get high-priority pending tasks
        pending_tasks = Task.get_by_user(user_id, status='pending', limit=10)
        
        # Get overdue tasks
        overdue_tasks = Task.get_overdue_tasks(user_id)
        
        recommendations = {
            'date': target_date.isoformat(),
            'scheduled_tasks': scheduled_tasks,
            'high_priority_tasks': [],
            'overdue_tasks': overdue_tasks,
            'suggested_focus': None
        }
        
        # Add high-priority tasks not already scheduled
        scheduled_ids = {t['task_id'] for t in scheduled_tasks}
        for task in pending_tasks:
            if task['task_id'] not in scheduled_ids:
                score = SmartPlanner.calculate_priority_score(task)
                if score >= 50:  # High priority threshold
                    recommendations['high_priority_tasks'].append(task)
        
        # Suggest focus area
        if scheduled_tasks:
            # Most common subject in scheduled tasks
            subject_counts = {}
            for task in scheduled_tasks:
                subject = task.get('subject_name', 'General')
                subject_counts[subject] = subject_counts.get(subject, 0) + 1
            
            recommendations['suggested_focus'] = max(subject_counts, key=subject_counts.get)
        
        return recommendations
    
    @staticmethod
    def analyze_workload(user_id, days_ahead=7):
        """
        Analyze upcoming workload
        """
        start_date = date.today()
        end_date = start_date + timedelta(days=days_ahead)
        
        tasks = Task.get_by_date_range(user_id, start_date, end_date)
        
        # Group by date
        workload_by_date = {}
        for task in tasks:
            task_date = task.get('scheduled_date')
            if task_date:
                date_str = task_date.isoformat() if hasattr(task_date, 'isoformat') else str(task_date)
                if date_str not in workload_by_date:
                    workload_by_date[date_str] = {
                        'tasks': [],
                        'total_hours': 0,
                        'task_count': 0
                    }
                
                workload_by_date[date_str]['tasks'].append(task)
                workload_by_date[date_str]['total_hours'] += float(task.get('estimated_hours', 0))
                workload_by_date[date_str]['task_count'] += 1
        
        # Identify heavy days
        heavy_days = []
        for date_str, data in workload_by_date.items():
            if data['total_hours'] > 6:  # More than 6 hours
                heavy_days.append(date_str)
        
        return {
            'workload_by_date': workload_by_date,
            'heavy_days': heavy_days,
            'total_tasks': len(tasks),
            'total_hours': sum(float(t.get('estimated_hours', 0)) for t in tasks)
        }
