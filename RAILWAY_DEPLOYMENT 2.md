# 🚂 Railway Deployment Guide for PathAI Django Backend

Complete step-by-step guide to deploy your Django backend to Railway with PostgreSQL, Redis, and Celery.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Railway Account Setup](#railway-account-setup)
3. [Repository Preparation](#repository-preparation)
4. [Deploy Main Web Service](#deploy-main-web-service)
5. [Add PostgreSQL Database](#add-postgresql-database)
6. [Add Redis for Celery](#add-redis-for-celery)
7. [Deploy Celery Worker](#deploy-celery-worker)
8. [Deploy Celery Beat](#deploy-celery-beat)
9. [Environment Variables Configuration](#environment-variables-configuration)
10. [First Deployment & Testing](#first-deployment--testing)
11. [Custom Domain Setup](#custom-domain-setup)
12. [Monitoring & Logs](#monitoring--logs)
13. [Troubleshooting](#troubleshooting)
14. [Cost Optimization](#cost-optimization)

---

## Prerequisites

Before starting, ensure you have:

- ✅ GitHub account with your code pushed to a repository
- ✅ Railway account (sign up at [railway.app](https://railway.app))
- ✅ API keys ready:
  - OpenAI API key
  - Anthropic API key
  - Tavily API key
- ✅ All deployment files in your backend folder:
  - `Dockerfile`
  - `railway.toml`
  - `Procfile`
  - `requirements.txt` (with production dependencies)
  - `.dockerignore`
  - `.env.railway.example`

---

## Railway Account Setup

### Step 1: Sign Up for Railway

1. Go to [railway.app](https://railway.app)
2. Click "Start a New Project"
3. Sign up with GitHub (recommended) or email
4. You'll receive **$5 free credit** (no credit card required initially)

### Step 2: Install Railway CLI (Optional but Recommended)

```bash
# macOS/Linux
brew install railway

# Or via npm
npm install -g @railway/cli

# Login
railway login
```

---

## Repository Preparation

### Step 1: Push Code to GitHub

If not already done:

```bash
cd /Users/diasoralbekov/Desktop/desk/pathAi/backend

# Initialize git if needed
git init

# Add all files
git add .

# Commit
git commit -m "Prepare for Railway deployment"

# Add remote and push
git remote add origin https://github.com/YOUR_USERNAME/pathai-backend.git
git branch -M main
git push -u origin main
```

### Step 2: Verify Deployment Files

Ensure these files exist in your backend folder:
```bash
ls -la | grep -E "(Dockerfile|railway.toml|Procfile|requirements.txt)"
```

---

## Deploy Main Web Service

### Step 1: Create New Project

1. Go to Railway dashboard: https://railway.app/dashboard
2. Click "**New Project**"
3. Select "**Deploy from GitHub repo**"
4. Authorize Railway to access your GitHub account
5. Select your `pathai-backend` repository
6. Railway will detect the Dockerfile automatically

### Step 2: Configure Build

Railway should automatically detect:
- ✅ Dockerfile exists
- ✅ Build command: Uses Dockerfile
- ✅ Start command: From Procfile or railway.toml

If not, manually set:
- **Build Command**: (leave empty, Docker handles it)
- **Start Command**:
  ```bash
  python manage.py migrate --noinput && gunicorn pathaibackend.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
  ```

### Step 3: Initial Deploy

1. Click "**Deploy**"
2. Railway will start building your Docker image
3. Wait 3-5 minutes for first build
4. ⚠️ It will fail initially (expected - missing database!)

---

## Add PostgreSQL Database

### Step 1: Add PostgreSQL Service

1. In your Railway project dashboard
2. Click "**+ New**" → "**Database**" → "**Add PostgreSQL**"
3. Railway automatically:
   - Creates PostgreSQL instance
   - Sets `DATABASE_URL` environment variable
   - Links it to your web service

### Step 2: Verify Database Connection

1. Click on PostgreSQL service
2. Go to "**Variables**" tab
3. You should see:
   ```
   DATABASE_URL=postgresql://postgres:***@containers-us-west-***.railway.app:5432/railway
   ```
4. This is automatically available to your Django app!

---

## Add Redis for Celery

### Step 1: Add Redis Service

1. Click "**+ New**" → "**Database**" → "**Add Redis**"
2. Railway automatically:
   - Creates Redis instance
   - Sets `REDIS_URL` environment variable
   - Links it to your services

### Step 2: Verify Redis Connection

1. Click on Redis service
2. Go to "**Variables**" tab
3. You should see:
   ```
   REDIS_URL=redis://default:***@containers-us-west-***.railway.app:6379
   ```

---

## Deploy Celery Worker

Your app uses Celery for background tasks. Deploy it as a separate service.

### Step 1: Create Celery Worker Service

1. Click "**+ New**" → "**GitHub Repo**"
2. Select the **same repository** (pathai-backend)
3. Rename service to "**celery-worker**"

### Step 2: Configure Worker

1. Click on the celery-worker service
2. Go to "**Settings**" → "**Deploy**"
3. Change **Start Command** to:
   ```bash
   celery -A pathaibackend worker --loglevel=info --concurrency=2
   ```
4. Go to "**Variables**" tab
5. Ensure it shares environment variables with main service

### Step 3: Deploy Worker

1. Click "**Deploy**"
2. Worker will start processing background tasks

---

## Deploy Celery Beat

Celery Beat handles scheduled tasks (like reminder checks).

### Step 1: Create Celery Beat Service

1. Click "**+ New**" → "**GitHub Repo**"
2. Select the **same repository** again
3. Rename service to "**celery-beat**"

### Step 2: Configure Beat

1. Click on the celery-beat service
2. Go to "**Settings**" → "**Deploy**"
3. Change **Start Command** to:
   ```bash
   celery -A pathaibackend beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
   ```
4. Go to "**Variables**" tab
5. Ensure it shares environment variables with main service

### Step 3: Deploy Beat

1. Click "**Deploy**"
2. Beat scheduler will start running periodic tasks

---

## Environment Variables Configuration

### Step 1: Configure Main Web Service Variables

1. Click on your main web service
2. Go to "**Variables**" tab
3. Click "**+ New Variable**"
4. Add these one by one:

#### Required Variables

```bash
# Django Settings
DJANGO_SETTINGS_MODULE=pathaibackend.production
SECRET_KEY=<generate-new-secret-key>
DEBUG=False
ALLOWED_HOSTS=.railway.app

# CORS (add your frontend URL)
CORS_ALLOWED_ORIGINS=https://your-frontend-url.com
CSRF_TRUSTED_ORIGINS=https://your-backend.railway.app

# AI API Keys
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
TAVILY_API_KEY=tvly-your-tavily-key
```

#### Generate SECRET_KEY

Run this locally:
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Copy the output and paste as `SECRET_KEY` value in Railway.

#### Auto-Set Variables (Railway provides these)

These are automatically set - **don't manually add**:
- `DATABASE_URL` (from PostgreSQL service)
- `REDIS_URL` (from Redis service)
- `PORT` (Railway sets this automatically)
- `RAILWAY_ENVIRONMENT`
- `RAILWAY_PUBLIC_DOMAIN`

### Step 2: Verify Variable Sharing

Ensure Celery worker and beat services have access to all variables:

1. Go to each service (worker, beat)
2. Click "**Variables**" tab
3. Check if they see `DATABASE_URL`, `REDIS_URL`, etc.
4. If not, click "**+ New Variable**" → "**Reference**" → Select main service variables

---

## First Deployment & Testing

### Step 1: Redeploy All Services

1. Go to main web service → Click "**Deploy**"
2. Go to celery-worker → Click "**Deploy**"
3. Go to celery-beat → Click "**Deploy**"

### Step 2: Check Deployment Logs

1. Click on each service
2. Go to "**Deployments**" tab
3. Click latest deployment
4. Check logs for errors

**Success indicators:**
```
✓ Migrations applied successfully
✓ Starting gunicorn
✓ Listening at: http://0.0.0.0:8000
✓ Celery worker ready
✓ Celery beat started
```

### Step 3: Get Your Backend URL

1. Click on main web service
2. Go to "**Settings**" → "**Networking**"
3. Your URL: `https://your-app-name.railway.app`

### Step 4: Test API

```bash
# Health check (if you added this endpoint)
curl https://your-app-name.railway.app/api/health/

# Test authentication endpoint
curl https://your-app-name.railway.app/api/auth/login/
```

---

## Custom Domain Setup

### Step 1: Add Custom Domain

1. Click on main web service
2. Go to "**Settings**" → "**Networking**"
3. Click "**Custom Domain**"
4. Enter your domain: `api.pathai.app`

### Step 2: Configure DNS

Railway will show DNS records. Add these to your domain registrar:

**Option A: CNAME Record (Recommended)**
```
Type: CNAME
Name: api
Value: <railway-provided-cname>
```

**Option B: A Record**
```
Type: A
Name: api
Value: <railway-provided-ip>
```

### Step 3: Update Environment Variables

After domain is connected:

1. Update `ALLOWED_HOSTS`:
   ```
   ALLOWED_HOSTS=.railway.app,api.pathai.app
   ```

2. Update `CSRF_TRUSTED_ORIGINS`:
   ```
   CSRF_TRUSTED_ORIGINS=https://api.pathai.app,https://your-frontend-url.com
   ```

---

## Monitoring & Logs

### View Logs

**Real-time logs:**
1. Click on service
2. Go to "**Logs**" tab
3. See live application logs

**Or use Railway CLI:**
```bash
# View logs
railway logs

# Follow logs
railway logs --follow

# Filter by service
railway logs --service web
railway logs --service celery-worker
```

### Monitor Metrics

1. Click on service
2. Go to "**Metrics**" tab
3. View:
   - CPU usage
   - Memory usage
   - Network traffic
   - Build times

### Set Up Alerts

1. Go to project settings
2. Enable notifications for:
   - Deployment failures
   - Service crashes
   - High resource usage

---

## Troubleshooting

### Issue: Build Fails

**Error**: `Dockerfile not found`

**Solution**:
1. Ensure Dockerfile is in repository root
2. Check file is committed to git
3. Verify file path in railway.toml

---

### Issue: Migration Fails

**Error**: `relation "users_user" does not exist`

**Solution**:
```bash
# Connect to Railway with CLI
railway link

# Run migrations manually
railway run python manage.py migrate

# Or via Railway dashboard
# Settings → Deploy → Add to start command:
python manage.py migrate --noinput && <your-existing-command>
```

---

### Issue: Celery Can't Connect to Redis

**Error**: `Error connecting to Redis`

**Solution**:
1. Verify Redis service is running
2. Check `REDIS_URL` is set in environment variables
3. Ensure worker/beat services can access Redis service
4. Check if Redis is in same Railway project

---

### Issue: CORS Errors from Frontend

**Error**: `Access-Control-Allow-Origin missing`

**Solution**:
1. Add frontend URL to `CORS_ALLOWED_ORIGINS`:
   ```
   CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app,https://your-app.expo.dev
   ```
2. Verify CORS middleware in production.py
3. Restart service

---

### Issue: Static Files Not Loading

**Error**: `404 for /static/admin/css/base.css`

**Solution**:
1. Ensure WhiteNoise is in MIDDLEWARE (production.py)
2. Run collectstatic in build:
   ```bash
   # Add to Dockerfile or start command
   python manage.py collectstatic --noinput
   ```
3. Verify STATIC_ROOT setting

---

### Issue: Database Connection Refused

**Error**: `could not connect to server`

**Solution**:
1. Check PostgreSQL service is running
2. Verify `DATABASE_URL` is set
3. Check database isn't sleeping (free tier limitation)
4. Restart both database and web service

---

### Issue: Out of Memory

**Error**: `Process killed (OOM)`

**Solution**:
1. Reduce Celery concurrency:
   ```bash
   celery -A pathaibackend worker --loglevel=info --concurrency=1
   ```
2. Reduce gunicorn workers:
   ```bash
   gunicorn ... --workers 1 --threads 2
   ```
3. Upgrade Railway plan for more memory

---

## Cost Optimization

### Monitor Your Usage

1. Go to Railway dashboard
2. Click "**Usage**" in sidebar
3. Monitor:
   - Build minutes
   - Compute hours
   - Database storage
   - Bandwidth

### Free Tier Tips ($5 Credit)

**To make $5 last longer:**

1. **Scale down workers:**
   ```bash
   # Use 1 worker instead of 2
   gunicorn ... --workers 1
   ```

2. **Reduce Celery concurrency:**
   ```bash
   celery ... --concurrency=1
   ```

3. **Remove idle services:**
   - Only run Celery beat if you need scheduled tasks
   - Disable if not using background jobs

4. **Database optimization:**
   - Clean up old data regularly
   - Optimize queries
   - Use database indexes

### When to Upgrade

**$5 credit typically lasts:**
- Light usage: 3-4 weeks
- Medium usage: 2-3 weeks
- Heavy usage: 1-2 weeks

**Signs you should upgrade:**
- Approaching credit limit
- Services frequently sleeping
- Need better performance
- Want custom domains
- Need backups

**Pricing after free tier:**
- **Hobby Plan**: $5/month (pay-as-you-go)
- **Pro Plan**: $20/month (better resources)
- **PostgreSQL**: Included in plans
- **Redis**: Included in plans

---

## Production Checklist

Before launching to real users:

- [ ] Set `DEBUG=False`
- [ ] Use strong `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS` properly
- [ ] Set up CORS for frontend domain
- [ ] Add all required API keys
- [ ] Test all API endpoints
- [ ] Run database migrations
- [ ] Verify Celery tasks work
- [ ] Test push notifications
- [ ] Set up custom domain
- [ ] Configure SSL/HTTPS
- [ ] Set up error monitoring (Sentry)
- [ ] Create database backups
- [ ] Document deployment process
- [ ] Test with production data
- [ ] Load test your API

---

## Next Steps

1. **Deploy to Railway** following this guide
2. **Connect frontend** to your Railway backend URL
3. **Test thoroughly** with real data
4. **Set up monitoring** (Sentry, LogRocket, etc.)
5. **Plan for scaling** as users grow
6. **Backup database** regularly

---

## Support & Resources

- **Railway Docs**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway
- **Django Deployment**: https://docs.djangoproject.com/en/5.1/howto/deployment/
- **Celery Docs**: https://docs.celeryq.dev

---

## Your Deployment URLs

After deployment, your URLs will be:

```
Main Backend:    https://pathai-backend-production.up.railway.app
PostgreSQL:      Internal Railway network
Redis:           Internal Railway network
Celery Worker:   Background service (no URL)
Celery Beat:     Background service (no URL)
```

---

**Good luck with your deployment! 🚀**

If you encounter issues not covered here, check Railway logs first, then consult Railway Discord community.
