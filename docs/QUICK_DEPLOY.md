# 🚀 Quick Deploy - Portalyze 2.0

**Repository:** https://github.com/RANJAN-ritesh/Portalyze

---

## ⚡ Fastest Path to Deploy (30 minutes total)

### Step 1: Get API Keys (5 min)

**Gemini (Recommended)**
1. Visit: https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key

**Groq (Optional backup)**
1. Visit: https://console.groq.com
2. Create account → "API Keys"
3. Copy the key

---

### Step 2: Deploy Backend on Railway (15 min)

1. Go to https://railway.app
2. "Start a New Project" → "Deploy from GitHub"
3. Select: `RANJAN-ritesh/Portalyze`
4. Settings:
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add Variables (click "Variables"):
   ```
   GEMINI_API_KEY=your_key_here
   GROQ_API_KEY=your_key_here
   DATABASE_URL=sqlite+aiosqlite:///./cache.db
   ENABLE_AI_ANALYSIS=true
   ENABLE_CACHING=true
   ```
6. Click "Deploy"
7. **Copy your backend URL** (e.g., `https://portalyze-backend.up.railway.app`)

---

### Step 3: Deploy Frontend on Vercel (10 min)

1. Go to https://vercel.com
2. "New Project" → Import `RANJAN-ritesh/Portalyze`
3. Settings:
   - **Root Directory:** `portfolio-grader`
   - Framework: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`
4. Add Environment Variable:
   ```
   VITE_API_BASE_URL=https://your-railway-backend-url.railway.app
   ```
5. Click "Deploy"
6. **Copy your frontend URL**

---

### Step 4: Update CORS (2 min)

1. Go back to Railway backend
2. Add to Variables:
   ```
   ALLOWED_ORIGINS=https://your-vercel-url.vercel.app
   ```
3. Click "Redeploy"

---

## ✅ Verify Deployment

Test your backend:
```bash
curl https://your-backend-url.railway.app/health
```

Should return:
```json
{"status":"healthy","version":"2.0.0","ai_providers":["gemini","groq"]}
```

Test your frontend:
- Visit: `https://your-vercel-url.vercel.app`
- Try analyzing a portfolio
- Test batch upload

---

## 🔧 Quick Troubleshooting

**Backend not responding?**
- Check API keys are correct
- View logs in Railway dashboard

**Frontend can't connect?**
- Verify `VITE_API_BASE_URL` matches Railway URL
- Check CORS is updated with Vercel URL

**AI analysis failing?**
- Verify Gemini API key is valid
- Check rate limits: https://aistudio.google.com

---

## 📚 Full Documentation

- **Detailed Guide:** `DEPLOYMENT_STEPS.md`
- **Project Docs:** `DEPLOYMENT.md`
- **Checklist:** `portfolio-grader/DEPLOY_CHECKLIST.md`

---

## 💰 Cost

**Free Tier** (perfect for testing):
- Railway: 500 hours/month
- Vercel: Unlimited
- **Total: $0/month**

**Production** (if you outgrow free tier):
- Railway Pro: $5/month
- Vercel Pro: $20/month

---

## 🎯 Alternative: One-Click Deploy with Docker

If you have a VPS (DigitalOcean, AWS EC2, etc.):

```bash
# Clone repo
git clone https://github.com/RANJAN-ritesh/Portalyze.git
cd Portalyze

# Setup environment
cp .env.example .env
nano .env  # Add API keys

# Deploy
docker-compose up -d

# Done! Visit http://your-server-ip
```

---

## 🆘 Need Help?

- Full deployment guide: See `DEPLOYMENT_STEPS.md`
- GitHub Issues: https://github.com/RANJAN-ritesh/Portalyze/issues
- Check logs in Railway/Vercel dashboards

---

**Ready to deploy?** Start with Railway + Vercel (steps above) - it's the easiest! 🚀
