"""
AI Study Assistant Agent Service
Provides intelligent study planning assistance using Google Gemini API
"""

import os
import logging
from datetime import datetime, date
from typing import List, Dict, Optional
import google.generativeai as genai
from database import Database

logger = logging.getLogger(__name__)

class AgentService:
    """AI Agent service for study planning assistance"""
    
    def __init__(self):
        """Initialize the AI agent with Gemini API"""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            logger.warning('GEMINI_API_KEY not set. Agent will not function.')
            self.model = None
            return
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            logger.info('AI Agent initialized successfully with Gemini Pro')
        except Exception as e:
            logger.error(f'Failed to initialize AI agent: {e}')
            self.model = None
    
    def _get_user_context(self, user_id: int) -> str:
        """Get user's study context for the AI agent"""
        context_parts = []
        
        # Get user's tasks
        tasks_query = """
            SELECT t.title, t.description, t.status, t.priority, 
                   t.scheduled_date, t.estimated_hours, s.subject_name
            FROM tasks t
            LEFT JOIN subjects s ON t.subject_id = s.subject_id
            WHERE t.user_id = %s
            ORDER BY t.scheduled_date, t.priority DESC
            LIMIT 20
        """
        tasks = Database.fetch_all(tasks_query, [user_id])
        
        if tasks:
            context_parts.append("## Current Tasks:")
            for task in tasks:
                status_emoji = "✅" if task['status'] == 'completed' else "⏳" if task['status'] == 'in_progress' else "📋"
                context_parts.append(
                    f"{status_emoji} {task['title']} ({task['subject_name']}) - "
                    f"Priority: {task['priority']}, Due: {task['scheduled_date']}, "
                    f"Status: {task['status']}"
                )
        
        # Get subjects
        subjects_query = "SELECT subject_name, priority FROM subjects WHERE user_id = %s"
        subjects = Database.fetch_all(subjects_query, [user_id])
        
        if subjects:
            context_parts.append("\n## Subjects:")
            for subject in subjects:
                context_parts.append(f"- {subject['subject_name']} (Priority: {subject['priority']})")
        
        # Get recent study sessions
        sessions_query = """
            SELECT ss.start_time, ss.end_time, ss.focus_score, t.title
            FROM study_sessions ss
            LEFT JOIN tasks t ON ss.task_id = t.task_id
            WHERE ss.user_id = %s
            ORDER BY ss.start_time DESC
            LIMIT 5
        """
        sessions = Database.fetch_all(sessions_query, [user_id])
        
        if sessions:
            context_parts.append("\n## Recent Study Sessions:")
            for session in sessions:
                duration = "N/A"
                if session['start_time'] and session['end_time']:
                    delta = session['end_time'] - session['start_time']
                    duration = f"{delta.seconds // 60} minutes"
                
                task_name = session['title'] or 'General study'
                focus = session['focus_score'] or 'N/A'
                context_parts.append(f"- {task_name}: {duration}, Focus: {focus}/10")
        
        # Get study goals
        goals_query = """
            SELECT title, target_value, current_value, goal_type, target_date, status
            FROM study_goals
            WHERE user_id = %s AND status != 'completed'
            ORDER BY target_date
            LIMIT 5
        """
        goals = Database.fetch_all(goals_query, [user_id])
        
        if goals:
            context_parts.append("\n## Active Goals:")
            for goal in goals:
                progress = (goal['current_value'] / goal['target_value'] * 100) if goal['target_value'] > 0 else 0
                context_parts.append(
                    f"- {goal['title']}: {goal['current_value']}/{goal['target_value']} "
                    f"({progress:.0f}%) - Due: {goal['target_date']}"
                )
        
        return "\n".join(context_parts) if context_parts else "No study data available yet."
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the AI agent"""
        return """
        You are 'Antigravity Study Assistant', a highly intelligent, empathetic, and proactive AI study coach.
        Your goal is to help students achieve their academic goals through smart planning, motivation, and clear guidance.

        ## Your Personality:
        - Encouraging but disciplined.
        - Data-driven: Use the student's task and session data to provide specific advice.
        - Clear and concise: Use markdown for readability (bolding, lists, etc.).
        - Proactive: Don't just answer; suggest the next best step.

        ## Your Capabilities:
        1. Specialized Study Planning: Create structured plans for subjects, exams, or projects.
        2. Progress Analysis: Identify patterns in study habits and suggest improvements.
        3. Motivation: Provide context-aware encouragement based on streaks and accomplishments.
        4. Scheduling: Suggest optimal times for tasks based on workload.

        Always stay in character as a supportive coach. If you don't have enough data, ask clarifying questions.
        """

    
    def chat(self, user_id: int, message: str, chat_history: List[Dict] = None) -> Dict:
        """
        Send a message to the AI agent and get a response
        
        Args:
            user_id: User ID for context
            message: User's message
            chat_history: Previous conversation history
            
        Returns:
            Dict with response and metadata
        """
        if not self.model:
            return {
                'response': 'Sorry, the AI agent is not configured. Please add your GEMINI_API_KEY to the .env file.',
                'error': True
            }
        
        try:
            # Get user context
            user_context = self._get_user_context(user_id)
            
            # Build the full prompt
            system_prompt = self._get_system_prompt()
            context_prompt = f"\n\n## User's Current Study Data:\n{user_context}\n\n"
            
            # Format chat history for Gemini
            full_prompt = system_prompt + context_prompt
            
            if chat_history:
                full_prompt += "\n## Previous Conversation:\n"
                for msg in chat_history[-5:]:  # Last 5 messages for context
                    role = "User" if msg['role'] == 'user' else "Assistant"
                    full_prompt += f"{role}: {msg['content']}\n"
            
            full_prompt += f"\nUser: {message}\nAssistant:"
            
            # Generate response
            response = self.model.generate_content(full_prompt)
            
            return {
                'response': response.text,
                'context_used': {
                    'tasks_count': user_context.count('📋') + user_context.count('⏳') + user_context.count('✅'),
                    'has_context': len(user_context) > 50
                },
                'error': False
            }
            
        except Exception as e:
            logger.error(f'Agent chat error: {e}', exc_info=True)
            return {
                'response': 'Sorry, I encountered an error processing your message. Please try again.',
                'error': True,
                'error_message': str(e)
            }
    
    def get_proactive_suggestions(self, user_id: int) -> List[str]:
        """
        Get proactive study suggestions based on user's current state
        
        Returns:
            List of suggestion strings
        """
        suggestions = []
        
        try:
            # Check for overdue tasks
            overdue_query = """
                SELECT COUNT(*) as count FROM tasks 
                WHERE user_id = %s AND status != 'completed' 
                AND scheduled_date < CURRENT_DATE
            """
            overdue = Database.fetch_one(overdue_query, [user_id])
            if overdue and overdue['count'] > 0:
                suggestions.append(f"📌 You have {overdue['count']} overdue task(s). Would you like help prioritizing them?")
            
            # Check for tasks due today
            today_query = """
                SELECT COUNT(*) as count FROM tasks 
                WHERE user_id = %s AND status != 'completed' 
                AND scheduled_date = CURRENT_DATE
            """
            today = Database.fetch_one(today_query, [user_id])
            if today and today['count'] > 0:
                suggestions.append(f"📅 You have {today['count']} task(s) due today. Ready to tackle them?")
            
            # Check study streak
            streak_query = """
                SELECT current_streak FROM study_streaks 
                WHERE user_id = %s 
                ORDER BY last_study_date DESC LIMIT 1
            """
            streak = Database.fetch_one(streak_query, [user_id])
            if streak and streak['current_streak'] >= 3:
                suggestions.append(f"🔥 Great job! You're on a {streak['current_streak']}-day study streak!")
            
            # Check if no study session today
            session_today_query = """
                SELECT COUNT(*) as count FROM study_sessions 
                WHERE user_id = %s AND DATE(start_time) = CURRENT_DATE
            """
            session_today = Database.fetch_one(session_today_query, [user_id])
            if session_today and session_today['count'] == 0:
                suggestions.append("💡 Haven't started studying today? Let's create a plan!")
            
        except Exception as e:
            logger.error(f'Error getting proactive suggestions: {e}')
        
        return suggestions[:3]  # Return max 3 suggestions

    def generate_study_plan(self, user_id: int, goal_description: str, timeframe_days: int) -> Dict:
        """Generate a structured study plan using AI"""
        if not self.model:
             return {'error': True, 'response': 'AI agent not configured. Please add GEMINI_API_KEY to .env.'}

        try:
            user_context = self._get_user_context(user_id)
            prompt = f"""
            ## Request:
            The user wants a 'Readymade Study Plan'.
            Goal: {goal_description}
            Timeframe: {timeframe_days} days

            ## Current Context:
            {user_context}

            ## Instructions:
            1. Create a logical progression of tasks to achieve this goal.
            2. Suggest specific study sessions (durations, topics).
            3. Break it down day-by-day or in phases.
            4. Format your response as a clear, structured markdown plan.
            5. Include a 'JSON_Tasks' section exactly in triple backticks with a JSON array of tasks to be added. 
               Format: ```json [{"title": "...", "estimated_hours": ..., "task_type": "...", "priority": ...}] ```
            """
            
            response = self.model.generate_content(prompt)
            content = response.text
            
            # Simple JSON extraction
            tasks_to_create = []
            if "```json" in content:
                import json
                try:
                    json_part = content.split("```json")[1].split("```")[0].strip()
                    tasks_to_create = json.loads(json_part)
                except Exception as je:
                    logger.error(f"Failed to parse AI JSON tasks: {je}")

            return {
                'response': content,
                'tasks_to_create': tasks_to_create,
                'error': False
            }
        except Exception as e:
            logger.error(f"Error generating study plan: {e}")
            return {'error': True, 'response': f"Failed to generate study plan: {str(e)}"}


# Global agent instance
agent_service = AgentService()
