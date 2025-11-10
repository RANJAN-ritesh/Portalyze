# 🚀 Production Deployment Guide - Portalyze 2.0

## Current Status: ✅ PRODUCTION READY

Your app has been built and is ready for deployment!

**Frontend:** Built successfully → `frontend/dist/` (ready to deploy)
**Backend:** Already deployed on Render
**Frontend URL:** https://portalyze.netlify.app
**Backend URL:** https://portalyze.onrender.com

---

## 🔧 Critical Fix Applied

### Fixed: Double Slash in API URLs
**Location:** `frontend/src/services/api.ts:4`

The API base URL now automatically strips trailing slashes to prevent double-slash errors like `//batch-grade`.

```typescript
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
```

---

## 📋 Deployment Checklist

### Step 1: Deploy Frontend to Netlify ✅

Your frontend is already built! Now deploy it:

#### Option A: Drag & Drop (Fastest)
1. Go to https://app.netlify.com/drop
2. Drag the `frontend/dist` folder
3. Your site will be live in seconds!

#### Option B: Git-based Deployment (Recommended)
1. Commit and push your changes:
   ```bash
   cd /Users/rrs/Desktop/Port/Portalyze
   git add .
   git commit -m "fix: Strip trailing slash from API base URL to fix CORS"
   git push origin main
   ```

2. Netlify will automatically rebuild and deploy

#### Option C: CLI Deployment
```bash
cd /Users/rrs/Desktop/Port/Portalyze/frontend
npm install -g netlify-cli
netlify deploy --prod --dir=dist
```

---

### Step 2: Configure Netlify Environment Variables ⚙️

Go to: **Netlify Dashboard → Site Settings → Environment Variables**

Add/Update:
```
VITE_API_BASE_URL=https://portalyze.onrender.com
```

**IMPORTANT:** No trailing slash!

✅ Correct: `https://portalyze.onrender.com`
❌ Wrong: `https://portalyze.onrender.com/`

After updating, trigger a redeploy:
- Go to **Deploys** tab
- Click **Trigger deploy** → **Deploy site**

---

### Step 3: Update Backend CORS Settings 🔐

Go to: **Render Dashboard → portalyze → Environment**

Add/Update this environment variable:
```
ALLOWED_ORIGINS=https://portalyze.netlify.app
```

If you have a custom domain, add both:
```
ALLOWED_ORIGINS=https://portalyze.netlify.app,https://your-custom-domain.com
```

**After updating:** Render will automatically redeploy (takes ~2-3 minutes)

---

### Step 4: Set Backend to Production Mode 🏭

In Render environment variables, ensure:
```
ENVIRONMENT=production
```

This enables production CORS settings and optimizations.

---

## 🧪 Testing Your Deployment

### 1. Test Backend Health
```bash
curl https://portalyze.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "ai_providers": ["gemini", "groq"]
}
```

### 2. Test CORS Preflight
```bash
curl -I -X OPTIONS https://portalyze.onrender.com/batch-grade \
  -H "Origin: https://portalyze.netlify.app" \
  -H "Access-Control-Request-Method: POST"
```

Expected: `HTTP/1.1 200 OK` with these headers:
```
Access-Control-Allow-Origin: https://portalyze.netlify.app
Access-Control-Allow-Methods: *
Access-Control-Allow-Headers: *
```

### 3. Test Frontend
Open: https://portalyze.netlify.app

Try these:
- ✅ Single portfolio grading
- ✅ Batch CSV upload
- ✅ Batch grading
- ✅ Export results

**Check browser console** - should have NO CORS errors!

---

## 🛠️ Current Configuration Summary

### Frontend (Netlify)
```yaml
Build Command: npm install && npm run build
Publish Directory: dist
Node Version: 18

Environment Variables:
  VITE_API_BASE_URL: https://portalyze.onrender.com
```

### Backend (Render)
```yaml
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT

Required Environment Variables:
  GEMINI_API_KEY: <your-key>
  GROQ_API_KEY: <your-key>
  ALLOWED_ORIGINS: https://portalyze.netlify.app
  ENVIRONMENT: production

Optional (for tuning):
  MAX_CONCURRENT_ANALYSES: 10
  RATE_LIMIT_PER_HOUR: 20
  CACHE_TTL_DAYS: 7
```

---

## 🐛 Troubleshooting

### CORS Error: "No 'Access-Control-Allow-Origin' header"

**Cause:** Backend `ALLOWED_ORIGINS` doesn't include your frontend URL

**Fix:**
1. Go to Render → Environment
2. Update `ALLOWED_ORIGINS=https://portalyze.netlify.app`
3. Wait for redeploy (~2-3 min)

### Error: "net::ERR_FAILED" or 400 Bad Request

**Cause:** Double slash in URL (already fixed!)

**Verify:** Check that `VITE_API_BASE_URL` has no trailing slash

### Frontend shows "localhost:8000" error

**Cause:** Environment variable not set on Netlify

**Fix:**
1. Netlify → Site Settings → Environment Variables
2. Add `VITE_API_BASE_URL=https://portalyze.onrender.com`
3. Redeploy site

### Backend: "No AI provider available"

**Cause:** Missing API keys

**Fix:** Add at least one:
```
GEMINI_API_KEY=your_key
GROQ_API_KEY=your_key
```

---

## 🎯 Performance Optimization

### For High Traffic
Update these in Render environment:
```
MAX_CONCURRENT_ANALYSES=15
RATE_LIMIT_PER_HOUR=50
CACHE_TTL_DAYS=14
```

### For Cost Savings
```
MAX_CONCURRENT_ANALYSES=5
RATE_LIMIT_PER_HOUR=10
CACHE_TTL_DAYS=30
```

---

## 🔒 Security Checklist

- ✅ API keys stored in environment variables (not in code)
- ✅ `ALLOWED_ORIGINS` set to specific domains (not `*`)
- ✅ Rate limiting enabled
- ✅ HTTPS enforced (automatic on Render & Netlify)
- ✅ Security headers configured in `netlify.toml`
- ✅ Environment set to `production`

---

## 📊 Monitoring

### Backend Logs
View in Render Dashboard:
- Go to **Logs** tab
- Monitor for errors, rate limits, cache hits

### Frontend Analytics
Check Netlify Analytics:
- Site performance
- Bandwidth usage
- Deploy history

### Health Check Endpoint
Monitor: https://portalyze.onrender.com/health

Set up UptimeRobot or similar to ping this every 5 minutes.

---

## 🚀 Quick Deploy Commands

```bash
# From project root
cd /Users/rrs/Desktop/Port/Portalyze

# Commit and push changes
git add .
git commit -m "fix: Production deployment ready with CORS fix"
git push origin main

# Or manually deploy frontend
cd frontend
npm run build
netlify deploy --prod --dir=dist
```

---

## 📞 Post-Deployment

After everything is deployed:

1. ✅ Test all features on production URLs
2. ✅ Share your app: https://portalyze.netlify.app
3. ✅ Monitor logs for first 24 hours
4. ✅ Set up uptime monitoring
5. ✅ Configure custom domain (optional)

---

## 🎉 You're Live!

Your Portalyze app is now production-ready and deployed!

**Frontend:** https://portalyze.netlify.app
**Backend:** https://portalyze.onrender.com
**API Docs:** https://portalyze.onrender.com/docs

**Need help?** Check the docs in `/docs` or create an issue.

---

**Last Updated:** 2025-11-10
**Version:** 2.0.0 (Production)
