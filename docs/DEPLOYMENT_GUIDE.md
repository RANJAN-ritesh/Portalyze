# Deployment Guide - Portalyze 2.0

Complete guide for deploying Portalyze to Render (backend) and Netlify (frontend).

## Table of Contents

- [Prerequisites](#prerequisites)
- [Backend Deployment (Render)](#backend-deployment-render)
- [Frontend Deployment (Netlify)](#frontend-deployment-netlify)
- [Post-Deployment Configuration](#post-deployment-configuration)
- [Troubleshooting](#troubleshooting)

## Prerequisites

1. GitHub account with your code pushed
2. [Render account](https://dashboard.render.com/) (free tier available)
3. [Netlify account](https://app.netlify.com/) (free tier available)
4. API Keys:
   - Google Gemini API key (get from [Google AI Studio](https://makersuite.google.com/app/apikey))
   - Groq API key (get from [Groq Console](https://console.groq.com/))

## Backend Deployment (Render)

### Step 1: Prepare Your Repository

Ensure your code is pushed to GitHub with this structure:
```
your-repo/
├── backend/
│   ├── app/
│   ├── requirements.txt
│   ├── render.yaml
│   └── .env.example
├── frontend/
└── README.md
```

### Step 2: Create Web Service on Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub account and select your repository
4. Configure the service:

   **Basic Settings:**
   - **Name**: `portalyze-backend` (or your preferred name)
   - **Region**: Choose closest to your users (e.g., Oregon)
   - **Branch**: `main` (or your default branch)
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`

   **Build & Deploy:**
   - **Build Command**:
     ```bash
     pip install --upgrade pip && pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```

### Step 3: Configure Environment Variables

In the Render dashboard, go to **Environment** section and add these variables:

**Required:**
```
GEMINI_API_KEY=your_actual_gemini_api_key_here
GROQ_API_KEY=your_actual_groq_api_key_here
```

**Optional (recommended for production):**
```
ALLOWED_ORIGINS=https://your-app.netlify.app
DATABASE_URL=sqlite+aiosqlite:///./cache.db
MAX_CONCURRENT_ANALYSES=5
ANALYSIS_TIMEOUT_SECONDS=90
PAGE_LOAD_TIMEOUT=30
AI_REQUEST_TIMEOUT=20
CACHE_TTL_DAYS=7
ENABLE_CACHING=true
RATE_LIMIT_PER_HOUR=100
RATE_LIMIT_PER_DAY=1000
ENABLE_FACE_DETECTION=true
ENABLE_AI_ANALYSIS=true
ENABLE_SCREENSHOT_CAPTURE=false
ENABLE_SHAREABLE_LINKS=true
LOG_LEVEL=INFO
USE_PLAYWRIGHT=false
```

### Step 4: Deploy

1. Click **"Create Web Service"**
2. Wait for the build to complete (5-10 minutes)
3. Once deployed, you'll get a URL like: `https://portalyze-backend.onrender.com`
4. Test the health endpoint: `https://your-backend.onrender.com/health`

### Important Notes for Render:

- ✅ **Playwright is disabled by default** - Uses aiohttp fallback (no system dependencies needed)
- ✅ **Free tier limitations**:
  - Service spins down after 15 minutes of inactivity
  - First request after spin-down takes ~30 seconds
  - 750 hours/month free (sufficient for most projects)
- ✅ **Database**: SQLite is stored in ephemeral storage (resets on redeploy)
  - For persistent storage, consider upgrading to a PostgreSQL database
- ✅ **Custom Domain**: Available on paid plans

## Frontend Deployment (Netlify)

### Step 1: Prepare Frontend

Ensure your `frontend/.env.example` looks like:
```env
VITE_API_BASE_URL=https://your-backend.onrender.com
```

### Step 2: Create Site on Netlify

1. Go to [Netlify Dashboard](https://app.netlify.com/)
2. Click **"Add new site"** → **"Import an existing project"**
3. Connect to GitHub and select your repository
4. Configure build settings:

   **Basic Settings:**
   - **Site name**: `portalyze` (or your preferred subdomain)
   - **Branch to deploy**: `main`
   - **Base directory**: `frontend`
   - **Build command**: `npm install && npm run build`
   - **Publish directory**: `frontend/dist`

### Step 3: Environment Variables

In Netlify dashboard, go to **Site settings** → **Environment variables**:

Add:
```
VITE_API_BASE_URL=https://your-backend.onrender.com
```

Replace `your-backend.onrender.com` with your actual Render backend URL.

### Step 4: Deploy

1. Click **"Deploy site"**
2. Wait for build to complete (2-5 minutes)
3. Your site will be available at: `https://portalyze.netlify.app`

### Configure Netlify Settings

After deployment, update these settings:

**1. Update CORS on Backend**

Go back to Render and update the `ALLOWED_ORIGINS` environment variable:
```
ALLOWED_ORIGINS=https://your-app.netlify.app,https://portalyze.netlify.app
```

**2. Custom Domain (Optional)**

In Netlify:
- Go to **Domain settings**
- Click **Add custom domain**
- Follow DNS configuration instructions

## Post-Deployment Configuration

### 1. Test the Connection

Visit your Netlify URL and try grading a portfolio:
```
https://your-app.netlify.app
```

Try a test portfolio URL like: `https://example-portfolio.com`

### 2. Monitor Performance

**Render Logs:**
- Dashboard → Your Service → Logs
- Check for errors or warnings

**Netlify Logs:**
- Site dashboard → Deploys → Deploy log
- Functions → Function logs (if using Netlify Functions)

### 3. Update Frontend .env if Backend Changes

If your backend URL changes:
1. Update `VITE_API_BASE_URL` in Netlify environment variables
2. Trigger a new deployment: **Deploys** → **Trigger deploy** → **Deploy site**

## Troubleshooting

### Backend Issues

**Issue: 502 Bad Gateway**
- **Cause**: Backend is starting up or crashed
- **Solution**: Wait 30-60 seconds for Render free tier to spin up
- **Check**: Visit `/health` endpoint directly

**Issue: CORS Errors in Browser Console**
- **Cause**: Frontend URL not in `ALLOWED_ORIGINS`
- **Solution**: Add your Netlify URL to `ALLOWED_ORIGINS` in Render environment variables
- **Example**: `ALLOWED_ORIGINS=https://your-app.netlify.app`

**Issue: "Playwright not available" warnings**
- **Cause**: Expected behavior on Render (uses aiohttp fallback)
- **Solution**: No action needed - this is intentional

**Issue: Analysis taking too long**
- **Cause**: Cold start on Render free tier
- **Solution**: Consider upgrading to paid plan or keep service warm with periodic pings

### Frontend Issues

**Issue: "Network Error" when grading**
- **Cause**: Wrong `VITE_API_BASE_URL` or backend is down
- **Solution**:
  1. Check Netlify environment variables
  2. Verify backend is running: `curl https://your-backend.onrender.com/health`
  3. Check browser console for exact error

**Issue: Build fails on Netlify**
- **Cause**: Node version mismatch or missing dependencies
- **Solution**:
  1. Add `NODE_VERSION=18` to Netlify environment variables
  2. Check build logs for specific errors
  3. Ensure `package.json` is up to date

**Issue: 404 on page refresh**
- **Cause**: Missing SPA redirect configuration
- **Solution**: Verify `netlify.toml` has proper redirects (should be already configured)

### Database Issues

**Issue: Cache not persisting between deployments**
- **Cause**: Render uses ephemeral storage on free tier
- **Solution**:
  1. For production: Use Render PostgreSQL database
  2. For development: Expected behavior on free tier

**Issue: "Database is locked" errors**
- **Cause**: Multiple instances trying to write simultaneously
- **Solution**: Reduce `MAX_CONCURRENT_ANALYSES` in environment variables

## Performance Optimization

### Backend

1. **Reduce Cold Starts**: Use a service like UptimeRobot to ping your backend every 5-10 minutes
2. **Optimize Caching**: Increase `CACHE_TTL_DAYS` to reduce AI API calls
3. **Rate Limiting**: Adjust `RATE_LIMIT_PER_HOUR` based on your needs

### Frontend

1. **Enable Netlify CDN**: Automatically enabled for assets
2. **Optimize Images**: Use WebP format for images
3. **Lazy Loading**: Already implemented in the React components

## Cost Considerations

### Free Tier Limits

**Render Free Tier:**
- 750 hours/month
- 512 MB RAM
- Shared CPU
- Sleeps after 15 minutes of inactivity

**Netlify Free Tier:**
- 100 GB bandwidth/month
- 300 build minutes/month
- Unlimited sites

### Recommended Upgrades

If you exceed free tier:
- **Render**: $7/month for always-on service
- **Netlify**: $19/month for pro features

## Security Checklist

- [ ] API keys are stored in environment variables (not in code)
- [ ] `ALLOWED_ORIGINS` is set to specific domains (not `*`)
- [ ] Rate limiting is enabled (`RATE_LIMIT_PER_HOUR` set)
- [ ] HTTPS is enforced (automatic on Render & Netlify)
- [ ] `.env` files are in `.gitignore`

## Next Steps

1. ✅ Backend deployed to Render
2. ✅ Frontend deployed to Netlify
3. ✅ Environment variables configured
4. ✅ CORS configured
5. ⬜ Set up monitoring (optional)
6. ⬜ Configure custom domain (optional)
7. ⬜ Set up automated backups (for production)

## Support

For issues:
- Check logs first (Render dashboard and Netlify deploy logs)
- Review error messages carefully
- Consult documentation
- Open an issue on GitHub

---

Happy deploying! 🚀
