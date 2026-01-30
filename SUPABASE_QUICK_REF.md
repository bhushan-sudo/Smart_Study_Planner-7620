# 🎯 Supabase Quick Reference

## 📝 Connection String Format

```
postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

## 🔑 .env Configuration for Supabase

```bash
# Supabase Database
DB_HOST=db.[YOUR-PROJECT-REF].supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=[YOUR-DATABASE-PASSWORD]

# Pool Settings
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10

# App Config
SECRET_KEY=your-secret-key
DEBUG=True
HOST=0.0.0.0
PORT=5000
CORS_ORIGINS=http://localhost:5000
SESSION_COOKIE_SECURE=False
```

## 🚀 Quick Setup Steps

### 1. Create Project

- Go to [supabase.com](https://supabase.com)
- Click "New Project"
- Save your database password!

### 2. Run Schema

- Open SQL Editor in Supabase
- Paste contents of `database/schema.sql`
- Click "Run"

### 3. Get Connection Info

- Settings → Database → Connection String
- Copy URI format
- Extract host, password, and project ref

### 4. Update .env

- Replace `[YOUR-PROJECT-REF]` with your project reference
- Replace `[YOUR-DATABASE-PASSWORD]` with your password

### 5. Test & Run

```bash
setup.bat
run.bat
```

## 📍 Where to Find Info

| Info Needed | Location in Supabase Dashboard |
|-------------|-------------------------------|
| **Project Ref** | URL: `https://app.supabase.com/project/[PROJECT-REF]` |
| **Database Password** | You set this when creating project |
| **Connection String** | Settings → Database → Connection String |
| **API Keys** | Settings → API |
| **Database Host** | Settings → Database → Host |

## 🔍 Common Connection Strings

### Python (psycopg2) - Current Setup

```python
postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

### Python (SQLAlchemy)

```python
postgresql+psycopg2://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

### Node.js (pg)

```javascript
{
  host: 'db.[PROJECT-REF].supabase.co',
  port: 5432,
  database: 'postgres',
  user: 'postgres',
  password: '[PASSWORD]',
  ssl: { rejectUnauthorized: false }
}
```

### Connection Pooler (Recommended for serverless)

```
postgresql://postgres:[PASSWORD]@[PROJECT-REF].pooler.supabase.com:6543/postgres
```

## ✅ Verification Queries

### Check Tables Exist

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;
```

### Count Records

```sql
SELECT 
  (SELECT COUNT(*) FROM users) as users,
  (SELECT COUNT(*) FROM subjects) as subjects,
  (SELECT COUNT(*) FROM tasks) as tasks;
```

### View Sample Data

```sql
SELECT u.username, COUNT(t.task_id) as task_count
FROM users u
LEFT JOIN tasks t ON u.user_id = t.user_id
GROUP BY u.username;
```

## 🛠️ Troubleshooting

### ❌ Connection Timeout

**Solution:** Check if IP is whitelisted

- Settings → Database → Connection Pooling
- Add your IP or use `0.0.0.0/0` for development

### ❌ SSL Error

**Solution:** Add SSL mode to connection

```python
# In db_config.py
connection_string += "?sslmode=require"
```

### ❌ Too Many Connections

**Solution:** Use connection pooler

```bash
DB_HOST=[PROJECT-REF].pooler.supabase.com
DB_PORT=6543
```

### ❌ Password Authentication Failed

**Solution:** Reset database password

- Settings → Database → Database Password
- Click "Reset database password"
- Update `.env` file

## 📊 Free Tier Limits

| Resource | Free Tier Limit |
|----------|----------------|
| Database Size | 500 MB |
| Bandwidth | 2 GB/month |
| API Requests | Unlimited |
| Storage | 1 GB |
| Monthly Active Users | 50,000 |

## 🔐 Security Best Practices

### Development

```bash
# .env
DEBUG=True
SESSION_COOKIE_SECURE=False
CORS_ORIGINS=http://localhost:5000
```

### Production

```bash
# .env
DEBUG=False
SESSION_COOKIE_SECURE=True
CORS_ORIGINS=https://yourdomain.com
SECRET_KEY=[generate-random-32-char-string]
```

### Enable Row Level Security (RLS)

```sql
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can only see their tasks"
ON tasks FOR SELECT
USING (auth.uid()::text = user_id::text);
```

## 🎯 Performance Tips

### 1. Use Connection Pooling

Already configured in `database.py`!

### 2. Use Indexes

Already created in `schema.sql`!

### 3. Use Connection Pooler for Serverless

```bash
DB_HOST=[PROJECT-REF].pooler.supabase.com
DB_PORT=6543  # Note: Different port!
```

### 4. Monitor Query Performance

```sql
-- Enable pg_stat_statements
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- View slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;
```

## 📱 Supabase Dashboard Shortcuts

| Feature | Path |
|---------|------|
| SQL Editor | Left sidebar → SQL Editor |
| Table Editor | Left sidebar → Table Editor |
| API Docs | Left sidebar → API |
| Database Settings | Settings → Database |
| Logs | Left sidebar → Logs |
| Backups | Settings → Database → Backups |

## 🔗 Useful Links

- **Dashboard**: <https://app.supabase.com>
- **Documentation**: <https://supabase.com/docs>
- **Status Page**: <https://status.supabase.com>
- **Community**: <https://github.com/supabase/supabase/discussions>
- **Discord**: <https://discord.supabase.com>

## 💡 Pro Tips

1. **Save your password** - You can't retrieve it later!
2. **Use connection pooler** for serverless deployments
3. **Enable RLS** before going to production
4. **Set up backups** (Pro plan) for important data
5. **Monitor usage** in dashboard to avoid limits
6. **Use environment variables** - never commit credentials!

## 🆘 Need Help?

1. Check [SUPABASE_SETUP.md](SUPABASE_SETUP.md) for detailed guide
2. Visit [Supabase Docs](https://supabase.com/docs)
3. Ask in [Supabase Discord](https://discord.supabase.com)
4. Check [GitHub Discussions](https://github.com/supabase/supabase/discussions)

---

**Quick Start**: Create project → Run schema → Update .env → Run app! 🚀
