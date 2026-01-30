"""
Automatic Task Rescheduler
Handles automatic rescheduling of overdue and incomplete tasks
"""

from datetime import datetime, date, timedelta
from models import Task
from planner_logic import SmartPlanner
import logging

logger = logging.getLogger(__name__)

class TaskRescheduler:
    """Automatic task rescheduling logic"""
    
    @staticmethod
    def reschedule_overdue_tasks(user_id):
        """
        Automatically reschedule overdue tasks
        Returns list of rescheduled tasks
        """
        overdue_tasks = Task.get_overdue_tasks(user_id)
        rescheduled = []
        
        for task in overdue_tasks:
            try:
                # Calculate new deadline based on priority and remaining work
                new_deadline = TaskRescheduler._calculate_new_deadline(task)
                new_scheduled_date = TaskRescheduler._calculate_new_scheduled_date(task)
                
                # Update task
                updated_task = Task.update(
                    task['task_id'],
                    deadline=new_deadline,
                    scheduled_date=new_scheduled_date,
                    status='rescheduled'
                )
                
                if updated_task:
                    rescheduled.append({
                        'task_id': task['task_id'],
                        'title': task['title'],
                        'old_deadline': task.get('deadline'),
                        'new_deadline': new_deadline,
                        'new_scheduled_date': new_scheduled_date
                    })
                    logger.info(f"Rescheduled task {task['task_id']}: {task['title']}")
                
            except Exception as e:
                logger.error(f"Error rescheduling task {task['task_id']}: {e}")
        
        return rescheduled
    
    @staticmethod
    def _calculate_new_deadline(task):
        """Calculate new deadline based on task properties"""
        priority = task.get('priority', 1)
        completion = task.get('completion_percentage', 0)
        estimated_hours = float(task.get('estimated_hours', 1.0))
        
        # Calculate remaining work
        remaining_work = estimated_hours * (100 - completion) / 100
        
        # Base days to add based on priority (higher priority = sooner deadline)
        priority_days = {
            5: 2,  # Highest priority - 2 days
            4: 3,
            3: 5,
            2: 7,
            1: 10
        }
        
        base_days = priority_days.get(priority, 7)
        
        # Adjust based on remaining work
        if remaining_work > 5:
            base_days += 3
        elif remaining_work > 3:
            base_days += 2
        elif remaining_work > 1:
            base_days += 1
        
        new_deadline = datetime.now() + timedelta(days=base_days)
        return new_deadline
    
    @staticmethod
    def _calculate_new_scheduled_date(task):
        """Calculate new scheduled date"""
        priority = task.get('priority', 1)
        
        # High priority tasks scheduled sooner
        if priority >= 4:
            days_ahead = 1
        elif priority >= 3:
            days_ahead = 2
        else:
            days_ahead = 3
        
        new_date = date.today() + timedelta(days=days_ahead)
        return new_date
    
    @staticmethod
    def reschedule_incomplete_tasks(user_id, target_date=None):
        """
        Reschedule incomplete tasks from a specific date
        Useful for end-of-day rescheduling
        """
        if target_date is None:
            target_date = date.today()
        
        # Get tasks scheduled for target date that are not completed
        tasks = Task.get_by_date_range(user_id, target_date, target_date)
        incomplete_tasks = [t for t in tasks if t.get('status') not in ['completed']]
        
        rescheduled = []
        
        for task in incomplete_tasks:
            try:
                # Move to next available day
                new_scheduled_date = target_date + timedelta(days=1)
                
                updated_task = Task.update(
                    task['task_id'],
                    scheduled_date=new_scheduled_date,
                    status='rescheduled'
                )
                
                if updated_task:
                    rescheduled.append({
                        'task_id': task['task_id'],
                        'title': task['title'],
                        'old_date': target_date.isoformat(),
                        'new_date': new_scheduled_date.isoformat()
                    })
                    logger.info(f"Rescheduled incomplete task {task['task_id']}")
                
            except Exception as e:
                logger.error(f"Error rescheduling incomplete task {task['task_id']}: {e}")
        
        return rescheduled
    
    @staticmethod
    def balance_workload(user_id, days_ahead=7, max_hours_per_day=6):
        """
        Balance workload across upcoming days
        Redistribute tasks if any day is overloaded
        """
        start_date = date.today()
        end_date = start_date + timedelta(days=days_ahead)
        
        tasks = Task.get_by_date_range(user_id, start_date, end_date)
        
        # Group tasks by date
        tasks_by_date = {}
        for task in tasks:
            task_date = task.get('scheduled_date')
            if task_date:
                date_str = task_date.isoformat() if hasattr(task_date, 'isoformat') else str(task_date)
                if date_str not in tasks_by_date:
                    tasks_by_date[date_str] = []
                tasks_by_date[date_str].append(task)
        
        rebalanced = []
        
        # Check each day for overload
        for date_str, day_tasks in tasks_by_date.items():
            total_hours = sum(float(t.get('estimated_hours', 0)) for t in day_tasks)
            
            if total_hours > max_hours_per_day:
                # Sort tasks by priority (lower priority tasks moved first)
                day_tasks.sort(key=lambda t: t.get('priority', 1))
                
                hours_to_move = total_hours - max_hours_per_day
                current_hours_moved = 0
                
                for task in day_tasks:
                    if current_hours_moved >= hours_to_move:
                        break
                    
                    task_hours = float(task.get('estimated_hours', 0))
                    
                    # Find next available day
                    current_date = datetime.fromisoformat(date_str).date()
                    new_date = current_date + timedelta(days=1)
                    
                    # Update task
                    updated_task = Task.update(
                        task['task_id'],
                        scheduled_date=new_date
                    )
                    
                    if updated_task:
                        rebalanced.append({
                            'task_id': task['task_id'],
                            'title': task['title'],
                            'moved_from': date_str,
                            'moved_to': new_date.isoformat(),
                            'reason': 'workload_balancing'
                        })
                        current_hours_moved += task_hours
                        logger.info(f"Moved task {task['task_id']} for workload balancing")
        
        return rebalanced
    
    @staticmethod
    def auto_reschedule_all(user_id):
        """
        Run all automatic rescheduling operations
        """
        results = {
            'overdue_rescheduled': [],
            'incomplete_rescheduled': [],
            'workload_balanced': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Reschedule overdue tasks
            results['overdue_rescheduled'] = TaskRescheduler.reschedule_overdue_tasks(user_id)
            
            # Reschedule yesterday's incomplete tasks
            yesterday = date.today() - timedelta(days=1)
            results['incomplete_rescheduled'] = TaskRescheduler.reschedule_incomplete_tasks(user_id, yesterday)
            
            # Balance workload
            results['workload_balanced'] = TaskRescheduler.balance_workload(user_id)
            
            logger.info(f"Auto-rescheduling completed for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error in auto-rescheduling: {e}")
            results['error'] = str(e)
        
        return results
