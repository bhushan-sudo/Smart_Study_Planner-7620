# Smart Study Planner: Logical Architecture & Flow

This document explains the internal logic of the Smart Study Planner, specifically focusing on how the AI integration works with the existing backend and database.

## 1. System Architecture High-Level Overview

The system is built as a standard 3-tier web application with an added AI layer.

```mermaid
graph TD
    User[User (Browser)] <-->|HTTPS/JSON| Frontend[Frontend (HTML/JS)]
    Frontend <-->|API Calls| Backend[Backend (Flask/Python)]
    Backend <-->|SQL Queries| Database[(PostgreSQL/Supabase)]
    Backend <-->|Prompt + Context| AI[Gemini API]
```

## 2. Core Logic Flows

### A. The "Context Injection" Mechanism (The Brain)

When you chat with the AI, it isn't just a generic chatbot. The system "injects" your personal study data into the conversation invisible to you. This happens in `backend/agent_service.py`.

1. **User sends message**: "What should I study next?"
2. **Backend Intercept**:
    * The `AgentService` class wakes up.
    * It calls `_get_user_context(user_id)`.
3. **Data Gathering (SQL)**:
    * The system queries the database for your specific data:
        * **Tasks**: What is pending? What is high priority? (`SELECT * FROM tasks...`)
        * **Subjects**: What are your hard subjects?
        * **Goals**: Are you behind on your goals?
        * **History**: How did you do in your last session?
4. **Prompt Construction**:
    * The backend combines the **System Prompt** (instructions on how to be a tutor) + **User Context** (your data) + **User's Message**.
    * *Example Hidden Prompt sent to Google:*
        > "You are a helpful study tutor. The user has a Math exam on Friday and hasn't studied Calculus yet. The user just asked: 'What should I do?'"
5. **AI Response**: The AI sees the hidden context and replies: "Since you have a Math exam Friday, prioritize Calculus now."

### B. Proactive Intelligence (Background Agent)

The `agent_background.py` handles logic that happens *without* you asking.

* **Triggers**: Hooks in `main.py` update the AI when events happen (e.g., `on_task_completed`).
* **Logic**:
  * If you complete 5 tasks in a row -> "Celebration" logic triggers.
  * If you start a session -> "Focus" logic triggers.
  * Daily Insight: Every time you load the dashboard, it calculates a daily summary.

### C. Database Security Logic (Row Level Security)

The database uses **Row Level Security (RLS)** to protect data.

* **Logic**: Even if a hacker compromised the database connection, the rules inside the database engine say: "If User ID is X, they can ONLY see rows where `user_id = X`".
* This was applied via the `secure_database.sql` script.

## 3. Directory Structure & Key Files

| File | Purpose | Logic Contained |
| :--- | :--- | :--- |
| `backend/main.py` | API Router | Receives requests, routes them, handles auth tokens. |
| `backend/agent_service.py` | **The Brain** | Builds the prompts, talks to Gemini, manages chat history. |
| `backend/agent_background.py` | **The Observer** | Watches for events (task completion) to give proactive tips. |
| `backend/models.py` | Data Structure | Defines how Users, Tasks, and Chats look in python. |
| `database/schema.sql` | The Memory | Defines the actual tables where data lives. |

## 4. How the "Fix" Worked

When you had the "API Key Invalid" error:

1. **Issue**: The backend tried to send a request to Google, but the "Password" (API Key) was the default "placeholder" text.
2. **Symptom**: Google rejected the request, Flask caught the crash, and sent a generic "Error" JSON to the frontend.
3. **Fix**: Updating `.env` gave the backend the correct password to talk to Google's servers.

---
*This logic ensures the AI isn't just guessing—it actually "knows" what you are working on based on your database records.*
