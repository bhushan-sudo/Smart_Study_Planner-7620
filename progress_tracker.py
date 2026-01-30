"""
Progress Tracking Module
Track and analyze study progress
"""

from datetime import datetime, date, timedelta
from models import Task, TaskProgress, StudySession
import logging

logger = logging.getLogger(__name__)

class ProgressTracker:
    """Track and analyze study progress"""
    
    @staticmethod
    def update_task_progress(task_id, user_id, hours_spent, completion_percentage, notes=None):
        """Update progress for a task"""
        try:
            task = Task.get_by_id(task_id)
            if not task:
                return None
            
            old_completion = task.get('completion_percentage', 0)
            completion_delta = completion_percentage - old_completion
            
            updated_task = Task.update(
                task_id,
                completion_percentage=completion_percentage,
                actual_hours=float(task.get('actual_hours', 0)) + hours_spent
            )
            
            if completion_percentage >= 100:
                updated_task = Task.update(task_id, status='completed', completed_at=datetime.now())
            elif task.get('status') == 'pending':
                updated_task = Task.update(task_id, status='in_progress')
            
            progress_entry = TaskProgress.create(
                task_id=task_id, user_id=user_id, progress_date=date.today(),
                hours_spent=hours_spent, completion_delta=completion_delta, notes=notes
            )
            
            logger.info(f"Updated progress for task {task_id}: {completion_percentage}%")
            return {'task': updated_task, 'progress_entry': progress_entry, 'completion_delta': completion_delta}
            
        except Exception as e:
            logger.error(f"Error updating task progress: {e}")
            return None
    
    @staticmethod
    def log_study_session(task_id, user_id, start_time, end_time, notes=None, focus_score=None):
        """Log a study session"""
        try:
            session = StudySession.create(task_id, user_id, start_time, end_time, notes, focus_score)
            
            if start_time and end_time:
                duration = end_time - start_time
                hours_spent = duration.total_seconds() / 3600
                task = Task.get_by_id(task_id)
                if task:
                    new_actual_hours = float(task.get('actual_hours', 0)) + hours_spent
                    Task.update(task_id, actual_hours=new_actual_hours)
            
            logger.info(f"Logged study session for task {task_id}")
            return session
        except Exception as e:
            logger.error(f"Error logging study session: {e}")
            return None
    
    @staticmethod
    def get_task_analytics(task_id):
        """Get detailed analytics for a task"""
        task = Task.get_by_id(task_id)
        if not task:
            return None
        
        progress_history = TaskProgress.get_by_task(task_id)
        study_sessions = StudySession.get_by_task(task_id)
        
        estimated_hours = float(task.get('estimated_hours', 0))
        actual_hours = float(task.get('actual_hours', 0))
        completion = task.get('completion_percentage', 0)
        
        efficiency = 0
        if actual_hours > 0 and completion > 0 and estimated_hours > 0:
            efficiency = (completion / 100) / (actual_hours / estimated_hours)
        
        focus_scores = [s.get('focus_score') for s in study_sessions if s.get('focus_score')]
        avg_focus = sum(focus_scores) / len(focus_scores) if focus_scores else None
        
        return {
            'task': task,
            'progress_history': progress_history,
            'study_sessions': study_sessions,
            'metrics': {
                'estimated_hours': estimated_hours,
                'actual_hours': actual_hours,
                'completion_percentage': completion,
                'hours_remaining': max(0, estimated_hours - actual_hours),
                'efficiency_score': round(efficiency, 2),
                'average_focus_score': round(avg_focus, 1) if avg_focus else None,
                'total_sessions': len(study_sessions),
                'is_on_track': actual_hours <= estimated_hours if completion < 100 else True
            }
        }
