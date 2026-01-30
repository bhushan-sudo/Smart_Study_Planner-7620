# 🚀 Supabase Setup Guide

This guide will help you deploy the Smart Study Planner using **Supabase** as your PostgreSQL database.

## ✅ Why Supabase?

- **Free PostgreSQL Database** (up to 500MB)
- **Automatic API Generation**
- **Real-time Subscriptions**
- **Built-in Authentication**
- **No Server Management**
- **Global CDN**

## 📋 Prerequisites

- Supabase account ([Sign up free](https://supabase.com))
- Python 3.8+
- Git (optional)

## 🎯 Step-by-Step Setup

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign in
2. Click **"New Project"**
3. Fill in project details:
   - **Name**: `smart-study-planner`
   - **Database Password**: Choose a strong password (save this!)
   - **Region**: Choose closest to you
4. Click **"Create new project"**
5. Wait 2-3 minutes for setup to complete

### 2. Run Database Schema

#### Option A: Using Supabase SQL Editor (Recommended)

1. In your Supabase project, go to **SQL Editor** (left sidebar)
2. Click **"New Query"**
3. Copy the entire contents of `database/schema.sql`
4. Paste into the SQL editor
5. Click **"Run"** (or press Ctrl+Enter)
6. You should see: ✅ Success. No rows returned

#### Option B: Using Local psql

```bash
# Get connection string from Supabase Dashboard > Settings > Database
psql "postgresql://postgres:[YOUR-PASSWORD]@[YOUR-PROJECT-REF].supabase.co:5432/postgres" -f database/schema.sql
```

### 3. Get Supabase Connection Details

1. Go to **Settings** → **Database** in Supabase dashboard
2. Scroll to **Connection String** section
3. Select **"URI"** tab
4. Copy the connection string (it looks like):

   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
   ```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Supabase Database Configuration
DB_HOST=db.[YOUR-PROJECT-REF].supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=[YOUR-DATABASE-PASSWORD]

# Connection Pool Settings
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10

# Application Configuration
SECRET_KEY=your-secret-key-change-in-production
DEBUG=True
HOST=0.0.0.0
PORT=5000

# CORS Settings
CORS_ORIGINS=http://localhost:5000,http://127.0.0.1:5000

# Session Settings
SESSION_COOKIE_SECURE=False
```

**Replace:**

- `[YOUR-PROJECT-REF]` - Found in your Supabase project URL
- `[YOUR-DATABASE-PASSWORD]` - The password you set when creating the project

### 5. Install Dependencies

```bash
# Run setup script
setup.bat

# Or manually:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 6. Test Database Connection

```bash
cd backend
python -c "from database import Database; print('Connected!' if Database.test_connection() else 'Failed')"
```

You should see: `Connected!`

### 7. Start the Application

```bash
# Using run script
run.bat

# Or manually:
cd backend
python main.py
```

### 8. Access Your App

Open browser: **<http://localhost:5000>**

## 🔐 Supabase Security Settings

### Enable Row Level Security (RLS)

For production, enable RLS on all tables:

```sql
-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE subjects ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE study_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE weekly_summaries ENABLE ROW LEVEL SECURITY;

-- Create policies (example for tasks table)
CREATE POLICY "Users can view their own tasks"
  ON tasks FOR SELECT
  USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can insert their own tasks"
  ON tasks FOR INSERT
  WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update their own tasks"
  ON tasks FOR UPDATE
  USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can delete their own tasks"
  ON tasks FOR DELETE
  USING (auth.uid()::text = user_id::text);
```

## 📊 Verify Database Setup

### Check Tables

In Supabase SQL Editor, run:

```sql
-- List all tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';

-- Count records in each table
SELECT 'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'subjects', COUNT(*) FROM subjects
UNION ALL
SELECT 'tasks', COUNT(*) FROM tasks;
```

Expected output:

- users: 1
- subjects: 5
- tasks: 3

### View Sample Data

```sql
-- View demo user
SELECT * FROM users;

-- View subjects
SELECT * FROM subjects;

-- View tasks
SELECT * FROM tasks;
```

## 🌐 Using Supabase Client (Optional)

You can also use Supabase's JavaScript client for direct database access:

```javascript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://[YOUR-PROJECT-REF].supabase.co'
const supabaseKey = '[YOUR-ANON-KEY]'
const supabase = createClient(supabaseUrl, supabaseKey)

// Query tasks
const { data, error } = await supabase
  .from('tasks')
  .select('*')
  .eq('user_id', 1)
```

## 🚀 Production Deployment

### Update Environment Variables

```bash
# Production settings
DEBUG=False
SECRET_KEY=[generate-random-32-char-string]
SESSION_COOKIE_SECURE=True
CORS_ORIGINS=https://yourdomain.com

# Supabase connection (same as development)
DB_HOST=db.[YOUR-PROJECT-REF].supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=[YOUR-DATABASE-PASSWORD]
```

### Deploy Backend

You can deploy the Flask backend to:

1. **Heroku**

   ```bash
   heroku create smart-study-planner
   heroku config:set DB_HOST=... DB_PASSWORD=...
   git push heroku main
   ```

2. **Railway**
   - Connect GitHub repo
   - Add environment variables
   - Deploy automatically

3. **Render**
   - Create new Web Service
   - Connect repository
   - Add environment variables

4. **PythonAnywhere**
   - Upload code
   - Configure WSGI
   - Set environment variables

### Deploy Frontend

Deploy to:

- **Vercel**: Drag & drop `frontend` folder
- **Netlify**: Connect GitHub repo
- **GitHub Pages**: Static hosting
- **Cloudflare Pages**: Fast global CDN

## 📈 Supabase Features You Can Use

### 1. Database Backups

- Automatic daily backups (Pro plan)
- Point-in-time recovery
- Manual backups anytime

### 2. Real-time Subscriptions

```javascript
// Listen to task changes
supabase
  .from('tasks')
  .on('*', payload => {
    console.log('Task changed:', payload)
  })
  .subscribe()
```

### 3. Built-in Authentication

```javascript
// Sign up user
const { user, error } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'password123'
})
```

### 4. Storage (for file uploads)

```javascript
// Upload study materials
const { data, error } = await supabase.storage
  .from('study-materials')
  .upload('notes.pdf', file)
```

## 🔍 Monitoring & Analytics

### Supabase Dashboard

Monitor your database:

- **Database**: View tables, run queries
- **API**: Auto-generated REST API
- **Authentication**: User management
- **Storage**: File management
- **Logs**: Query logs and errors

### Performance Monitoring

```sql
-- Check slow queries
SELECT * FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;

-- Check table sizes
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## 💰 Supabase Pricing

**Free Tier** (Perfect for this project):

- 500 MB database space
- 1 GB file storage
- 2 GB bandwidth
- 50,000 monthly active users
- 500,000 Edge Function invocations

**Pro Tier** ($25/month):

- 8 GB database space
- 100 GB file storage
- 250 GB bandwidth
- Daily backups
- No pausing

## 🐛 Troubleshooting

### Connection Timeout

- Check if your IP is allowed in Supabase
- Verify connection string is correct
- Ensure database password is correct

### SSL Connection Error

Add to connection string:

```python
# In db_config.py
@classmethod
def get_connection_string(cls):
    return f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}?sslmode=require"
```

### Too Many Connections

- Reduce `DB_POOL_SIZE` in `.env`
- Close unused connections
- Upgrade to Pro plan for more connections

## ✅ Checklist

- [ ] Created Supabase project
- [ ] Ran `schema.sql` in SQL Editor
- [ ] Copied connection details to `.env`
- [ ] Installed Python dependencies
- [ ] Tested database connection
- [ ] Started Flask application
- [ ] Accessed app in browser
- [ ] Created first task successfully

## 📚 Additional Resources

- [Supabase Documentation](https://supabase.com/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Supabase Python Client](https://github.com/supabase-community/supabase-py)

## 🎉 You're Done

Your Smart Study Planner is now running on Supabase!

**Advantages of using Supabase:**

- ✅ No local PostgreSQL installation needed
- ✅ Automatic backups
- ✅ Global availability
- ✅ Real-time capabilities
- ✅ Built-in authentication ready
- ✅ Free tier is generous

---

**Happy Studying with Supabase! 🚀📚**
