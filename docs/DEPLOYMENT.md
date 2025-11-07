# Portalyze 2.0 - Deployment Guide

Complete guide for deploying Portalyze in production environments.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Start with Docker](#quick-start-with-docker)
- [Manual Deployment](#manual-deployment)
- [Environment Configuration](#environment-configuration)
- [Platform-Specific Guides](#platform-specific-guides)
- [Post-Deployment](#post-deployment)

---

## Prerequisites

### System Requirements
- **Server**: 2GB RAM minimum, 4GB recommended
- **Storage**: 10GB free space
- **OS**: Linux (Ubuntu 20.04+ recommended), macOS, or Windows with WSL2

### Required Software
- Docker & Docker Compose (recommended)
  OR
- Python 3.12+
- Node.js 20+
- Nginx (for manual deployment)

### API Keys (At least one required)
- Google Gemini API key
- Groq API key

---

## Quick Start with Docker

### 1. Clone and Configure

```bash
git clone <your-repo-url>
cd Portalyze

# Create environment file
cat <<'EOF' > .env
ENVIRONMENT=production
API_BASE_URL=http://localhost:8000
ALLOWED_ORIGINS=http://localhost
GEMINI_API_KEY=
GROQ_API_KEY=
EOF

# Edit .env with your values
nano .env  # Add your API keys and deployment domains
```

### 2. Build and Run

```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 3. Access

- **Frontend**: http://localhost (port 80)
- **Backend API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health

### 4. Stop Services

```bash
# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

---

## Manual Deployment

### Backend Deployment

#### 1. Setup Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

#### 2. Configure Environment

Create a `.env` file (see sample below) and populate it with your keys and domain settings. At minimum set:

```env
ENVIRONMENT=production
API_BASE_URL=https://api.yourdomain.com
ALLOWED_ORIGINS=https://yourfrontend.com
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
```

#### 3. Run Backend

**Development:**
```bash
./dev.sh
```

**Production:**
```bash
# Using gunicorn with uvicorn workers
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

### Frontend Deployment

#### 1. Install Dependencies

```bash
cd portfolio-grader
npm install
```

#### 2. Build for Production

```bash
# Create production build
npm run build

# Preview build locally
npm run preview
```

#### 3. Serve with Nginx

```bash
# Copy build to nginx directory
sudo cp -r dist/* /var/www/html/

# Configure nginx (see nginx.conf in frontend directory)
sudo cp nginx.conf /etc/nginx/sites-available/portalyze
sudo ln -s /etc/nginx/sites-available/portalyze /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Environment Configuration

### Required Variables

```env
# Environment
ENVIRONMENT=production
API_BASE_URL=https://api.yourdomain.com
ALLOWED_ORIGINS=https://yourfrontend.com,https://www.yourfrontend.com
# Optional regex override (leave blank unless you need wildcard support)
# ALLOW_ORIGIN_REGEX=https://.*\.yourfrontend\.com

# AI Providers (at least one is required)
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key

# Database
DATABASE_URL=sqlite+aiosqlite:///./cache.db

# Performance tuning for production
MAX_CONCURRENT_ANALYSES=10
ANALYSIS_TIMEOUT_SECONDS=120
PAGE_LOAD_TIMEOUT=45
AI_REQUEST_TIMEOUT=30

# Caching
ENABLE_CACHING=true
CACHE_TTL_DAYS=30

# Rate limiting
RATE_LIMIT_PER_HOUR=20
RATE_LIMIT_PER_DAY=200

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/portalyze.log
```

### Frontend Build Variables

```env
# In portfolio-grader/.env or your hosting dashboard
VITE_API_BASE_URL=https://api.yourdomain.com
```

---

## Platform-Specific Guides

### Deploy to DigitalOcean

1. **Create Droplet**
   - Choose Ubuntu 22.04 LTS
   - Minimum 2GB RAM
   - Enable monitoring

2. **Install Docker**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

3. **Deploy**
```bash
# Clone repo
git clone <your-repo>
cd Portalyze

# Configure environment (see examples above)
nano .env

# Run
docker-compose up -d
```

4. **Setup Domain**
   - Point DNS to droplet IP
   - Install Certbot for SSL
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

### Deploy to AWS EC2

1. **Launch EC2 Instance**
   - AMI: Ubuntu 22.04
   - Instance type: t3.medium or larger
   - Security groups: Allow ports 80, 443, 8000

2. **Connect and Setup**
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Deploy application
git clone <your-repo>
cd Portalyze
nano .env  # Populate with production values
docker-compose up -d
```

3. **Setup Load Balancer (Optional)**
   - Create Application Load Balancer
   - Configure target group
   - Add SSL certificate

### Deploy to Railway/Render

1. **Backend on Railway**
   - Connect GitHub repo
   - Add environment variables described in [Environment Configuration](#environment-configuration)
   - Railway will auto-detect Dockerfile
   - Set custom start command if needed:
     ```
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```

2. **Frontend on Vercel/Netlify**
   - Connect GitHub repo (portfolio-grader folder)
   - Build command: `npm run build`
   - Publish directory: `dist`
   - Add environment variable for API URL

### Deploy to Vercel (Frontend) + Railway (Backend)

**Backend (Railway):**
1. New Project → Deploy from GitHub
2. Select the Portalyze repo
3. Add environment variables
4. Deploy

**Frontend (Vercel):**
1. New Project → Import Git
2. Root Directory: `portfolio-grader`
3. Environment variable: `VITE_API_BASE_URL=https://your-railway-url.railway.app`
4. Deploy

---

## Post-Deployment

### Health Checks

```bash
# Backend health
curl http://your-domain:8000/health

# Frontend health
curl http://your-domain/health
```

### Monitoring

```bash
# View Docker logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Check resource usage
docker stats

# Application logs
tail -f logs/portalyze.log
```

### Database Backup

```bash
# Backup SQLite database
cp cache.db cache.db.backup.$(date +%Y%m%d)

# Automated backup (add to crontab)
0 2 * * * cp /path/to/portalyze/cache.db /path/to/backup/cache.db.$(date +\%Y\%m\%d)
```

### SSL/TLS Setup

```bash
# Using Let's Encrypt
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### Performance Tuning

**Backend:**
- Increase `MAX_CONCURRENT_ANALYSES` for more throughput
- Adjust `ANALYSIS_TIMEOUT_SECONDS` based on your server
- Enable caching with longer `CACHE_TTL_DAYS`

**Frontend:**
- Enable gzip compression in nginx
- Configure CDN for static assets
- Use HTTP/2

---

## Troubleshooting

### Common Issues

**"No AI provider keys found"**
- Check .env file has at least one API key
- Restart the backend service

**"Port already in use"**
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
docker-compose -f docker-compose.yml -e PORT=8001 up
```

**"Database locked"**
- Stop all instances
- Delete cache.db.lock if exists
- Restart

**Frontend can't reach backend**
- Check CORS settings in backend
- Update `ALLOWED_ORIGINS` in .env
- Verify API_BASE_URL in frontend

### Logs

```bash
# Backend logs
tail -f logs/portalyze.log

# Docker logs
docker-compose logs -f

# Nginx logs
tail -f /var/log/nginx/error.log
```

---

## Security Checklist

- [ ] Change default ports in production
- [ ] Use HTTPS/SSL certificates
- [ ] Set strong API keys
- [ ] Configure firewall (only allow 80, 443)
- [ ] Regular security updates
- [ ] Backup database regularly
- [ ] Monitor logs for suspicious activity
- [ ] Use environment variables for secrets
- [ ] Enable rate limiting
- [ ] Set up monitoring and alerts

---

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      replicas: 3
    ports:
      - "8000-8002:8000"
```

### Load Balancer Configuration

```nginx
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}
```

---

## Support

For issues or questions:
- Check logs first
- Review this documentation
- Open an issue on GitHub
- Contact: [your-email@domain.com]
