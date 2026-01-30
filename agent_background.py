"""
Background AI Agent Service
Monitors user activity and provides proactive assistance
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from database import Database

logger = logging.getLogger(__name__)

class BackgroundAgent:
    """Background agent that monitors and assists proactively"""
    
    @staticmethod
    def on_task_created(user_id: int, task_data: Dict) -> Optional[str]:
        """
        Called when a task is created
        Returns suggestion message if applicable
        """
        try:
            # Check if task has no scheduled date or time - ASK AI FOR PLAN
            if not task_data.get('scheduled_date'):
                # Call AI service to suggest a plan
                from agent_service import agent_service
                
                # Get user context for better suggestion
                user_context = agent_service._get_user_context(user_id)
                prompt = f"I just added a new task: '{task_data.get('title')}'. Based on my current schedule and workload, when should I do this? Provide a specific date and time suggestion and a brief reason."
                
                response = agent_service.chat(user_id, prompt)
                if not response.get('error'):
                    return f"🤖 AI Suggestion: {response['response']}"
                
                return "💡 I noticed you created a task without a due date. Would you like me to suggest an optimal schedule?"
            
            # Check if user has many tasks on same day
            same_day_query = """
                SELECT COUNT(*) as count FROM tasks 
                WHERE user_id = %s AND scheduled_date = %s AND status != 'completed'
            """
            result = Database.fetch_one(same_day_query, [user_id, task_data.get('scheduled_date')])
            
            if result and result['count'] > 5:
                return f"⚠️ You now have {result['count']} tasks on {task_data.get('scheduled_date')}. Consider spreading them out for better focus!"
            
            return None
        except Exception as e:
            logger.error(f"Error in on_task_created: {e}")
            return None
    
    @staticmethod
    def on_task_completed(user_id: int, task_data: Dict) -> Optional[str]:
        """Called when a task is completed"""
        try:
            # Check completion streak
            today_completed_query = """
                SELECT COUNT(*) as count FROM tasks 
                WHERE user_id = %s AND status = 'completed' 
                AND DATE(updated_at) = CURRENT_DATE
            """
            result = Database.fetch_one(today_completed_query, [user_id])
            
            if result and result['count'] >= 5:
                return f"🎉 Amazing! You've completed {result['count']} tasks today! You're on fire!"
            elif result and result['count'] == 1:
                return "✅ Great start! First task of the day completed!"
            
            return None
        except Exception as e:
            logger.error(f"Error in on_task_completed: {e}")
            return None
    
    @staticmethod
    def on_session_started(user_id: int, task_id: Optional[int] = None) -> Optional[str]:
        """Called when a study session starts"""
        try:
            # Get recent session performance
            recent_sessions_query = """
                SELECT AVG(focus_score) as avg_focus 
                FROM study_sessions 
                WHERE user_id = %s AND focus_score IS NOT NULL
                AND start_time >= NOW() - INTERVAL '7 days'
            """
            result = Database.fetch_one(recent_sessions_query, [user_id])
            
            if result and result['avg_focus'] and result['avg_focus'] < 6:
                return "💪 Your focus has been lower lately. Try the Pomodoro technique: 25 min focus, 5 min break!"
            
            # Check if it's their first session today
            today_session_query = """
                SELECT COUNT(*) as count FROM study_sessions 
                WHERE user_id = %s AND DATE(start_time) = CURRENT_DATE
            """
            today_result = Database.fetch_one(today_session_query, [user_id])
            
            if today_result and today_result['count'] == 0:
                return "🌟 Starting your first study session of the day! Let's make it count!"
            
            return None
        except Exception as e:
            logger.error(f"Error in on_session_started: {e}")
            return None
    
    @staticmethod
    def on_session_completed(user_id: int, session_data: Dict) -> Optional[str]:
        """Called when a study session ends"""
        try:
            duration_minutes = session_data.get('duration_minutes', 0)
            focus_score = session_data.get('focus_score')
            
            messages = []
            
            # Celebrate duration milestones
            if duration_minutes >= 120:
                messages.append("🏆 Incredible! 2+ hours of focused study!")
            elif duration_minutes >= 60:
                messages.append("⭐ Excellent! You studied for over an hour!")
            elif duration_minutes >= 25:
                messages.append("✅ Great session! You completed a full Pomodoro!")
            
            # Comment on focus
            if focus_score:
                if focus_score >= 8:
                    messages.append(f"Your focus was outstanding ({focus_score}/10)!")
                elif focus_score < 5:
                    messages.append(f"Focus was low ({focus_score}/10). Try eliminating distractions next time.")
            
            # Check daily study time
            daily_time_query = """
                SELECT SUM(EXTRACT(EPOCH FROM (end_time - start_time))/60) as total_minutes
                FROM study_sessions 
                WHERE user_id = %s AND DATE(start_time) = CURRENT_DATE
            """
            result = Database.fetch_one(daily_time_query, [user_id])
            
            if result and result['total_minutes']:
                total_today = int(result['total_minutes'])
                messages.append(f"📊 Total study time today: {total_today} minutes")
            
            return " ".join(messages) if messages else None
        except Exception as e:
            logger.error(f"Error in on_session_completed: {e}")
            return None
    
    @staticmethod
    def on_goal_progress(user_id: int, goal_data: Dict) -> Optional[str]:
        """Called when goal progress is updated"""
        try:
            current = goal_data.get('current_value', 0)
            target = goal_data.get('target_value', 1)
            progress_pct = (current / target * 100) if target > 0 else 0
            
            # Milestone celebrations
            if progress_pct >= 100:
                return f"🎊 Goal achieved! You completed '{goal_data.get('title')}'! Time to set a new challenge!"
            elif progress_pct >= 75:
                return f"🔥 You're 75% there on '{goal_data.get('title')}'! Almost done!"
            elif progress_pct >= 50:
                return f"💪 Halfway point reached on '{goal_data.get('title')}'! Keep going!"
            elif progress_pct >= 25:
                return f"📈 25% progress on '{goal_data.get('title')}'! Great start!"
            
            return None
        except Exception as e:
            logger.error(f"Error in on_goal_progress: {e}")
            return None
    
    @staticmethod
    def check_daily_status(user_id: int) -> List[str]:
        """
        Check user's daily status and provide insights
        Called periodically or on dashboard load
        """
        insights = []
        
        try:
            # Check overdue tasks
            overdue_query = """
                SELECT COUNT(*) as count FROM tasks 
                WHERE user_id = %s AND status != 'completed' 
                AND scheduled_date < CURRENT_DATE
            """
            overdue = Database.fetch_one(overdue_query, [user_id])
            if overdue and overdue['count'] > 0:
                insights.append(f"⚠️ {overdue['count']} overdue task(s) need attention")
            
            # Check today's tasks
            today_query = """
                SELECT COUNT(*) as count FROM tasks 
                WHERE user_id = %s AND status != 'completed' 
                AND scheduled_date = CURRENT_DATE
            """
            today = Database.fetch_one(today_query, [user_id])
            if today and today['count'] > 0:
                insights.append(f"📅 {today['count']} task(s) due today")
            
            # Check if no study session today
            session_query = """
                SELECT COUNT(*) as count FROM study_sessions 
                WHERE user_id = %s AND DATE(start_time) = CURRENT_DATE
            """
            sessions = Database.fetch_one(session_query, [user_id])
            if sessions and sessions['count'] == 0:
                current_hour = datetime.now().hour
                if current_hour >= 9:  # After 9 AM
                    insights.append("💡 No study sessions yet today. Ready to start?")
            
            # Check study streak
            streak_query = """
                SELECT current_streak FROM study_streaks 
                WHERE user_id = %s 
                ORDER BY last_study_date DESC LIMIT 1
            """
            streak = Database.fetch_one(streak_query, [user_id])
            if streak and streak['current_streak'] >= 3:
                insights.append(f"🔥 {streak['current_streak']}-day study streak active!")
            
            # Check goal progress
            goals_query = """
                SELECT title, current_value, target_value 
                FROM study_goals 
                WHERE user_id = %s AND status = 'active'
                AND target_date >= CURRENT_DATE
                ORDER BY target_date LIMIT 3
            """
            goals = Database.fetch_all(goals_query, [user_id])
            for goal in goals:
                progress = (goal['current_value'] / goal['target_value'] * 100) if goal['target_value'] > 0 else 0
                if progress >= 90:
                    insights.append(f"🎯 Almost there! {goal['title']} at {progress:.0f}%")
            
        except Exception as e:
            logger.error(f"Error in check_daily_status: {e}")
        
        return insights[:5]  # Return max 5 insights
    
    @staticmethod
    def get_smart_recommendations(user_id: int) -> List[str]:
        """Get AI-powered recommendations based on patterns"""
        recommendations = []
        
        try:
            # Analyze study patterns
            pattern_query = """
                SELECT 
                    EXTRACT(HOUR FROM start_time) as hour,
                    AVG(focus_score) as avg_focus,
                    COUNT(*) as session_count
                FROM study_sessions 
                WHERE user_id = %s AND focus_score IS NOT NULL
                AND start_time >= NOW() - INTERVAL '30 days'
                GROUP BY EXTRACT(HOUR FROM start_time)
                ORDER BY avg_focus DESC
                LIMIT 1
            """
            best_time = Database.fetch_one(pattern_query, [user_id])
            
            if best_time and best_time['session_count'] >= 3:
                hour = int(best_time['hour'])
                recommendations.append(f"📊 You focus best around {hour}:00. Try scheduling important tasks then!")
            
            # Check subject performance
            subject_query = """
                SELECT s.subject_name, 
                       COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed,
                       COUNT(*) as total
                FROM subjects s
                LEFT JOIN tasks t ON s.subject_id = t.subject_id
                WHERE s.user_id = %s
                GROUP BY s.subject_id, s.subject_name
                HAVING COUNT(*) > 0
                ORDER BY (COUNT(CASE WHEN t.status = 'completed' THEN 1 END)::float / COUNT(*)) ASC
                LIMIT 1
            """
            weak_subject = Database.fetch_one(subject_query, [user_id])
            
            if weak_subject:
                completion_rate = (weak_subject['completed'] / weak_subject['total'] * 100) if weak_subject['total'] > 0 else 0
                if completion_rate < 50:
                    recommendations.append(f"📚 {weak_subject['subject_name']} needs more attention ({completion_rate:.0f}% completion rate)")
            
            # Check for long gaps
            last_session_query = """
                SELECT MAX(start_time) as last_session 
                FROM study_sessions 
                WHERE user_id = %s
            """
            last_session = Database.fetch_one(last_session_query, [user_id])
            
            if last_session and last_session['last_session']:
                days_since = (datetime.now() - last_session['last_session']).days
                if days_since >= 2:
                    recommendations.append(f"⏰ It's been {days_since} days since your last session. Let's get back on track!")
            
        except Exception as e:
            logger.error(f"Error in get_smart_recommendations: {e}")
        
        return recommendations[:3]  # Return max 3 recommendations

# Global instance
background_agent = BackgroundAgent()
