# 🚀 Portalyze 2.0 - Deployment Steps

**Repository:** https://github.com/RANJAN-ritesh/Portalyze

---

## 📋 Pre-Deployment Checklist

Before deploying, ensure you have:
- [ ] At least ONE AI API key (Gemini OR Groq)
- [ ] GitHub account with repository access
- [ ] Deployment platform account (choose one below)

---

## 🎯 Deployment Options

### **Option 1: Railway (Recommended - Easiest)**
**Best for:** Full-stack deployment with automatic builds
**Cost:** Free tier available (500 hours/month)
**Time:** ~15 minutes

#### Backend Deployment (Railway)

1. **Go to Railway**
   - Visit: https://railway.app
   - Click "Start a New Project"
   - Select "Deploy from GitHub repo"
   - Choose `RANJAN-ritesh/Portalyze`

2. **Configure Backend Service**
   - Railway will auto-detect Python
   - In Settings:
     - **Root Directory:** Leave blank (uses root)
     - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
     - **Build Command:** `pip install -r requirements.txt && playwright install chromium`

3. **Add Environment Variables** (click "Variables" tab)
   ```bash
   # AI Provider (add at least one)
   GEMINI_API_KEY=your_gemini_api_key_here
   GROQ_API_KEY=your_groq_api_key_here

   # Database
   DATABASE_URL=sqlite+aiosqlite:///./cache.db

   # Configuration
   ENABLE_AI_ANALYSIS=true
   ENABLE_CACHING=true
   CACHE_TTL_DAYS=7
   MAX_CONCURRENT_ANALYSES=5
   RATE_LIMIT_PER_HOUR=20

   # CORS (update after frontend deployment)
   ALLOWED_ORIGINS=http://localhost:5173,https://your-frontend-url.vercel.app
   ```

4. **Deploy**
   - Click "Deploy"
   - Wait for build (3-5 minutes)
   - Copy the public URL (e.g., `https://portalyze-backend.up.railway.app`)

#### Frontend Deployment (Vercel)

1. **Go to Vercel**
   - Visit: https://vercel.com
   - Click "New Project"
   - Import `RANJAN-ritesh/Portalyze`

2. **Configure Project**
   - **Root Directory:** `portfolio-grader`
   - **Framework Preset:** Vite
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`

3. **Add Environment Variable**
   ```bash
   VITE_API_BASE_URL=https://your-backend-url.railway.app
   ```
   (Replace with your Railway backend URL)

4. **Deploy**
   - Click "Deploy"
   - Wait for build (2-3 minutes)
   - Visit your live URL!

5. **Update Backend CORS**
   - Go back to Railway backend
   - Update `ALLOWED_ORIGINS` to include your Vercel URL
   - Redeploy backend

---

### **Option 2: Render (Free Tier)**
**Best for:** No credit card required
**Cost:** Completely free (with limitations)
**Time:** ~20 minutes

#### Backend Deployment (Render)

1. **Create New Web Service**
   - Visit: https://render.com
   - Dashboard → "New" → "Web Service"
   - Connect GitHub: `RANJAN-ritesh/Portalyze`

2. **Configure**
   - **Name:** portalyze-backend
   - **Environment:** Python 3
   - **Region:** Choose closest to you
   - **Branch:** main
   - **Root Directory:** Leave blank
   - **Build Command:**
     ```bash
     pip install -r requirements.txt && playwright install chromium
     ```
   - **Start Command:**
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```

3. **Add Environment Variables**
   (Same as Railway above)

4. **Select Plan**
   - Choose "Free" (spins down after 15 min of inactivity)

5. **Create Web Service**
   - Wait for deployment (5-10 minutes)
   - Copy your URL (e.g., `https://portalyze-backend.onrender.com`)

#### Frontend Deployment (Render)

1. **Create Static Site**
   - Dashboard → "New" → "Static Site"
   - Same repo: `RANJAN-ritesh/Portalyze`

2. **Configure**
   - **Name:** portalyze-frontend
   - **Root Directory:** `portfolio-grader`
   - **Build Command:** `npm install && npm run build`
   - **Publish Directory:** `dist`

3. **Add Environment Variable**
   ```bash
   VITE_API_BASE_URL=https://your-backend-url.onrender.com
   ```

4. **Create Static Site**
   - Wait for deployment
   - Update backend CORS with frontend URL

---

### **Option 3: Docker (VPS/Cloud)**
**Best for:** Full control, production-ready
**Requires:** Server with Docker installed (AWS EC2, DigitalOcean, etc.)
**Time:** ~30 minutes

#### Prerequisites

```bash
# Install Docker & Docker Compose on your server
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### Deployment Steps

1. **Clone Repository**
   ```bash
   git clone https://github.com/RANJAN-ritesh/Portalyze.git
   cd Portalyze
   ```

2. **Create .env File**
   ```bash
   cp .env.example .env
   nano .env  # Add your API keys
   ```

3. **Configure Environment**
   ```bash
   # Required
   GEMINI_API_KEY=your_key_here
   GROQ_API_KEY=your_key_here

   # Update for production
   API_BASE_URL=https://your-domain.com
   ALLOWED_ORIGINS=https://your-domain.com
   ```

4. **Build and Deploy**
   ```bash
   # Build images
   docker-compose build

   # Start services
   docker-compose up -d

   # Check status
   docker-compose ps
   docker-compose logs -f
   ```

5. **Verify Deployment**
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:80
   ```

6. **Setup Domain & SSL**
   - Point your domain to server IP
   - Use nginx-proxy or Caddy for SSL
   - Or use Cloudflare for free SSL

#### Useful Docker Commands

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart services
docker-compose restart

# Update after code changes
git pull
docker-compose build
docker-compose up -d

# Stop everything
docker-compose down

# Clean up
docker-compose down -v  # Also removes volumes
```

---

### **Option 4: Netlify (Frontend Only)**
**Best for:** Quick frontend deployment
**Note:** You'll still need to deploy backend separately

1. **Go to Netlify**
   - Visit: https://netlify.com
   - "Add new site" → "Import an existing project"

2. **Configure**
   - Repository: `RANJAN-ritesh/Portalyze`
   - **Base directory:** `portfolio-grader`
   - **Build command:** `npm run build`
   - **Publish directory:** `portfolio-grader/dist`

3. **Add Environment Variable**
   ```bash
   VITE_API_BASE_URL=https://your-backend-url
   ```

4. **Deploy**
   - Click "Deploy site"
   - Setup custom domain (optional)

---

## 🔐 Getting API Keys

### Gemini API Key (Recommended)

1. Go to: https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key
4. Add to environment variables

**Limits:**
- Free tier: 60 requests/minute
- Perfect for portfolio analysis

### Groq API Key (Fallback)

1. Go to: https://console.groq.com
2. Sign up with GitHub
3. Go to "API Keys" → "Create API Key"
4. Copy the key
5. Add to environment variables

**Limits:**
- Free tier: 30 requests/minute
- Good fallback option

---

## 🧪 Testing Your Deployment

After deployment, test these endpoints:

### Backend Tests

```bash
# Health check
curl https://your-backend-url/health

# Test single analysis (replace URL)
curl -X POST https://your-backend-url/grade \
  -H "Content-Type: application/json" \
  -d '{"portfolio_url": "https://example-portfolio.vercel.app"}'

# Check status
curl https://your-backend-url/status
```

### Frontend Test

1. Visit your frontend URL
2. Try single portfolio analysis
3. Test batch upload with CSV
4. Verify "Clear Cache" button works

---

## 🐛 Troubleshooting

### Backend Issues

**"AI analysis unavailable"**
- Check API keys are set correctly
- Verify API keys are not expired
- Check rate limits

**"Timeout errors"**
- Increase `ANALYSIS_TIMEOUT_SECONDS` in .env
- Check server resources
- Verify Playwright is installed

**"Database errors"**
- Ensure `cache.db` has write permissions
- For Docker: check volume mounts
- For cloud: use persistent storage

### Frontend Issues

**"Unable to connect to backend"**
- Check `VITE_API_BASE_URL` is correct
- Verify backend is running
- Check CORS settings in backend

**Build failures**
- Run `npm install` again
- Check Node.js version (requires 18+)
- Clear cache: `rm -rf node_modules/.vite dist`

---

## 📊 Monitoring

### Railway
- Built-in logs and metrics
- Set up alerts for crashes
- Check usage in dashboard

### Render
- View logs in dashboard
- Monitor cold start times
- Check service health

### Docker
```bash
# Monitor resources
docker stats

# Check logs
docker-compose logs -f

# Health checks
curl http://localhost:8000/health
```

---

## 🔄 Updating After Deployment

### For Railway/Render (Auto-deploy)

1. Make changes locally
2. Commit and push to GitHub
3. Platform auto-deploys

```bash
git add .
git commit -m "Update: description"
git push origin main
```

### For Docker (Manual)

```bash
# On your server
cd Portalyze
git pull origin main
docker-compose build
docker-compose up -d
```

---

## 💰 Cost Estimates

### Free Tier (Good for 1000+ users/month)
- Railway: 500 hours/month free
- Vercel: Unlimited bandwidth
- Render: Free tier (spins down)
- Netlify: 100GB bandwidth
- **Total: $0/month**

### Paid Tier (Production-ready)
- Railway Pro: $5/month
- Vercel Pro: $20/month
- DigitalOcean Droplet: $6/month
- **Total: ~$10-30/month**

---

## 🎉 Post-Deployment Checklist

- [ ] Backend health check returns 200
- [ ] Frontend loads correctly
- [ ] Single portfolio analysis works
- [ ] Batch CSV upload works
- [ ] AI feedback displays
- [ ] Cache system working
- [ ] Clear Cache button works
- [ ] CSV export downloads
- [ ] Results shareable
- [ ] CORS configured correctly
- [ ] API keys secure (not in git)
- [ ] Custom domain setup (optional)
- [ ] SSL certificate active
- [ ] Monitoring enabled

---

## 📞 Support

- **GitHub Issues:** https://github.com/RANJAN-ritesh/Portalyze/issues
- **Documentation:** See DEPLOYMENT.md for detailed guides
- **Verification:** Run `./verify-deployment.sh` locally

---

## 🎯 Quick Start (Recommended Path)

For fastest deployment:

1. **Deploy Backend on Railway** (15 min)
   - Connect GitHub
   - Add Gemini API key
   - Copy backend URL

2. **Deploy Frontend on Vercel** (10 min)
   - Set root directory: `portfolio-grader`
   - Add backend URL
   - Deploy

3. **Update CORS** (2 min)
   - Add Vercel URL to Railway backend
   - Redeploy backend

**Total time: ~30 minutes to fully deployed!**

---

**Need help?** Open an issue on GitHub or check the detailed DEPLOYMENT.md file.
