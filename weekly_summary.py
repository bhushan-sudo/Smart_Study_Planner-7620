"""
Weekly Summary Generator
Generate comprehensive weekly study summaries
"""

from datetime import datetime, date, timedelta
from models import Task, WeeklySummary
from database import Database
import logging

logger = logging.getLogger(__name__)

class WeeklySummaryGenerator:
    """Generate weekly study summaries"""
    
    @staticmethod
    def generate_summary(user_id, week_start_date=None):
        """Generate weekly summary"""
        if week_start_date is None:
            today = date.today()
            week_start_date = today - timedelta(days=today.weekday())
        
        week_end_date = week_start_date + timedelta(days=6)
        
        tasks = Task.get_by_date_range(user_id, week_start_date, week_end_date)
        
        total_tasks_planned = len(tasks)
        completed_tasks = [t for t in tasks if t.get('status') == 'completed']
        total_tasks_completed = len(completed_tasks)
        
        total_hours_planned = sum(float(t.get('estimated_hours', 0)) for t in tasks)
        total_hours_actual = sum(float(t.get('actual_hours', 0)) for t in tasks)
        
        completion_rate = (total_tasks_completed / total_tasks_planned * 100) if total_tasks_planned > 0 else 0
        
        productivity_score = 0
        if total_hours_planned > 0:
            time_efficiency = min(100, (total_hours_actual / total_hours_planned) * 100)
            productivity_score = (completion_rate + time_efficiency) / 2
        
        subject_breakdown = {}
        for task in tasks:
            subject = task.get('subject_name', 'No Subject')
            if subject not in subject_breakdown:
                subject_breakdown[subject] = {'total': 0, 'completed': 0, 'hours': 0}
            subject_breakdown[subject]['total'] += 1
            subject_breakdown[subject]['hours'] += float(task.get('actual_hours', 0))
            if task.get('status') == 'completed':
                subject_breakdown[subject]['completed'] += 1
        
        summary_data = {
            'total_tasks_planned': total_tasks_planned,
            'total_tasks_completed': total_tasks_completed,
            'total_hours_planned': round(total_hours_planned, 2),
            'total_hours_actual': round(total_hours_actual, 2),
            'completion_rate': round(completion_rate, 2),
            'productivity_score': round(productivity_score, 2),
            'subject_breakdown': subject_breakdown,
            'tasks_by_status': {
                'completed': total_tasks_completed,
                'in_progress': len([t for t in tasks if t.get('status') == 'in_progress']),
                'pending': len([t for t in tasks if t.get('status') == 'pending']),
                'overdue': len([t for t in tasks if t.get('status') == 'overdue'])
            }
        }
        
        summary = WeeklySummary.create(user_id, week_start_date, week_end_date, summary_data)
        logger.info(f"Generated weekly summary for user {user_id}")
        
        return summary
    
    @staticmethod
    def get_summary_comparison(user_id, weeks_back=4):
        """Compare recent weekly summaries"""
        summaries = WeeklySummary.get_by_user(user_id, limit=weeks_back)
        
        if not summaries:
            return None
        
        comparison = {
            'summaries': summaries,
            'trends': {
                'completion_rate_trend': [],
                'productivity_trend': [],
                'hours_trend': []
            }
        }
        
        for summary in summaries:
            comparison['trends']['completion_rate_trend'].append({
                'week': summary['week_start_date'].isoformat() if hasattr(summary['week_start_date'], 'isoformat') else str(summary['week_start_date']),
                'value': float(summary.get('completion_rate', 0))
            })
            comparison['trends']['productivity_trend'].append({
                'week': summary['week_start_date'].isoformat() if hasattr(summary['week_start_date'], 'isoformat') else str(summary['week_start_date']),
                'value': float(summary.get('productivity_score', 0))
            })
            comparison['trends']['hours_trend'].append({
                'week': summary['week_start_date'].isoformat() if hasattr(summary['week_start_date'], 'isoformat') else str(summary['week_start_date']),
                'value': float(summary.get('total_hours_actual', 0))
            })
        
        return comparison
