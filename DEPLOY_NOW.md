# 🎯 Quick Deploy Instructions

## ✅ What's Been Fixed

1. **Double Slash Bug** - Fixed in `frontend/src/services/api.ts`
2. **Production Build** - Built successfully in `frontend/dist/`
3. **Deployment Scripts** - Created `deploy-frontend.sh`

## 🚀 Deploy in 3 Steps

### Step 1: Push to Git (Auto-deploy)
```bash
cd /Users/rrs/Desktop/Port/Portalyze
git add .
git commit -m "fix: Production deployment with CORS fix"
git push origin main
```

Netlify will auto-build and deploy in ~2 minutes.

---

### Step 2: Update Render Environment Variables

Go to: https://dashboard.render.com → Your Service → Environment

**Add/Update:**
```
ALLOWED_ORIGINS=https://portalyze.netlify.app
ENVIRONMENT=production
```

Click **Save** (auto-redeploys in ~2-3 min)

---

### Step 3: Update Netlify Environment Variables

Go to: Netlify Dashboard → Site Settings → Environment Variables

**Add/Update:**
```
VITE_API_BASE_URL=https://portalyze.onrender.com
```

⚠️ **No trailing slash!**

Then: **Deploys** → **Trigger deploy** → **Deploy site**

---

## ✨ That's It!

Your app will be live at:
- **Frontend:** https://portalyze.netlify.app
- **Backend:** https://portalyze.onrender.com

---

## 🧪 Quick Test

```bash
# Test backend
curl https://portalyze.onrender.com/health

# Test CORS
curl -I -X OPTIONS https://portalyze.onrender.com/batch-grade \
  -H "Origin: https://portalyze.netlify.app" \
  -H "Access-Control-Request-Method: POST"
```

Expected: `200 OK` with CORS headers

---

## 📖 Need More Details?

See `PRODUCTION_DEPLOYMENT.md` for:
- Detailed troubleshooting
- Performance tuning
- Security checklist
- Monitoring setup

---

**Total Deploy Time:** ~5-7 minutes
**Status:** ✅ PRODUCTION READY
