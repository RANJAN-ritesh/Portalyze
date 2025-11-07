# Portalyze 2.0

**AI-Powered Portfolio Grading Platform**

Portalyze is a comprehensive portfolio analysis tool that grades student portfolios against 27 quality parameters, provides AI-powered feedback, and supports batch processing via CSV uploads.

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.12+-green)
![Node](https://img.shields.io/badge/node-20+-green)
![License](https://img.shields.io/badge/license-MIT-blue)

---

## Features

### Core Features
- **27-Point Analysis**: Comprehensive checklist covering structure, content, design, and technical aspects
- **AI-Powered Feedback**: Contextual feedback from Google Gemini or Groq
- **Batch Processing**: Grade multiple portfolios via CSV upload
- **Professional Photo Detection**: OpenCV/MediaPipe face detection (70-95% accuracy)
- **Responsive Design Check**: Multi-device viewport testing
- **Smart Caching**: 7-day cache with force refresh option
- **Shareable Results**: Generate shareable links for grading results
- **CSV Export**: Export detailed results with all parameters

### Advanced Features
- Rate limiting and request throttling
- Real-time progress tracking for batch jobs
- Expandable accordion view for detailed analysis
- Dark theme UI with Tailwind CSS
- Concurrent analysis with configurable limits
- Health monitoring endpoints

---

## Quick Start

### Using Docker (Recommended)

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd Portalyze

# 2. Configure environment
cp .env.example .env
nano .env  # Add your API keys

# 3. Start services
docker-compose up -d

# 4. Access the application
# Frontend: http://localhost
# Backend: http://localhost:8000
```

### Manual Setup

**Backend:**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run backend
./dev.sh
```

**Frontend:**
```bash
cd portfolio-grader

# Install dependencies
npm install

# Run frontend
npm run dev
```

---

## Tech Stack

### Backend
- **Framework**: FastAPI
- **Python**: 3.12+
- **AI**: Google Gemini, Groq
- **Browser Automation**: Playwright
- **Face Detection**: MediaPipe / OpenCV
- **Database**: SQLite (with async support)
- **Validation**: Pydantic
- **Rate Limiting**: SlowAPI

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **Icons**: Lucide React
- **State Management**: React Hooks

---

## Project Structure

```
Portalyze/
├── app/                        # Backend application
│   ├── main.py                # FastAPI entry point
│   ├── config.py              # Configuration management
│   ├── database/              # Database and caching
│   │   └── cache.py           # SQLite cache service
│   └── services/              # Core services
│       ├── analyzer.py        # Portfolio analyzer
│       ├── ai_analyzer.py     # AI feedback service
│       ├── scraper.py         # Web scraping service
│       └── image_validator.py # Face detection service
├── portfolio-grader/          # Frontend application
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── Landing.tsx    # Landing page
│   │   │   ├── Result.tsx     # Single result view
│   │   │   ├── BatchUpload.tsx # CSV upload
│   │   │   └── BatchResults.tsx # Batch results
│   │   ├── services/          # API services
│   │   │   └── api.ts         # API client
│   │   └── App.tsx            # Main app component
│   ├── Dockerfile             # Frontend Docker config
│   └── nginx.conf             # Nginx configuration
├── Dockerfile                 # Backend Docker config
├── docker-compose.yml         # Docker orchestration
├── .env.example               # Environment template
├── DEPLOYMENT.md              # Deployment guide
├── requirements.txt           # Python dependencies
├── dev.sh                     # Backend dev script
├── frontend.sh                # Frontend dev script
├── start.sh                   # Start both services
└── stop.sh                    # Stop all services
```

---

## Configuration

### Environment Variables

```env
# Required: At least one AI provider
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key

# Server configuration
API_BASE_URL=http://localhost:8000
ALLOWED_ORIGINS=http://localhost:5173

# Performance tuning
MAX_CONCURRENT_ANALYSES=5
ANALYSIS_TIMEOUT_SECONDS=90
PAGE_LOAD_TIMEOUT=30

# Features
ENABLE_FACE_DETECTION=true
ENABLE_AI_ANALYSIS=true
ENABLE_CACHING=true
CACHE_TTL_DAYS=7

# Rate limiting
RATE_LIMIT_PER_HOUR=10
RATE_LIMIT_PER_DAY=100
```

See `.env.example` for complete configuration options.

---

## API Documentation

### Health Check
```bash
GET /health
```
Returns service status and available AI providers.

### Grade Single Portfolio
```bash
POST /grade
Content-Type: application/json

{
  "portfolio_url": "https://github.com/username",
  "force_refresh": false
}
```

### Batch Upload CSV
```bash
POST /batch-upload-csv
Content-Type: multipart/form-data

file: <CSV file>
```

CSV Format:
```csv
id,name,portfolio_url
fw16_001,John Doe,https://johndoe.dev
fw16_002,Jane Smith,https://janesmith.com
```

### Batch Grade Portfolios
```bash
POST /batch-grade
Content-Type: application/json

{
  "portfolios": [
    {
      "id": "fw16_001",
      "name": "John Doe",
      "portfolio_url": "https://johndoe.dev"
    }
  ]
}
```

### Export Results as CSV
```bash
POST /batch-export-csv
Content-Type: application/json

{
  "total": 5,
  "successful": 5,
  "failed": 0,
  "avg_score": 75.5,
  "total_time": 45.2,
  "results": [...]
}
```

---

## Development

### Quick Development Commands

```bash
# Start backend only
./dev.sh

# Start frontend only
./frontend.sh

# Start both services
./start.sh

# Stop all services
./stop.sh
```

### Testing

```bash
# Backend tests
pytest

# Frontend tests
cd portfolio-grader
npm test

# E2E tests
playwright test
```

### Code Quality

```bash
# Python linting
flake8 app/
black app/

# TypeScript linting
cd portfolio-grader
npm run lint
```

---

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive deployment guides including:
- Docker deployment
- Manual deployment
- Platform-specific guides (AWS, DigitalOcean, Railway, Vercel)
- SSL setup
- Monitoring and scaling

---

## Grading Criteria (27 Parameters)

### Structure & Content (9 parameters)
- About section
- Skills section
- Projects section
- Contact section
- Resume/CV link
- Social links (GitHub, LinkedIn)
- Professional photo
- Clear navigation
- Footer information

### Projects (6 parameters)
- Multiple projects (3+)
- Project descriptions
- Technology stack display
- Live demo links
- Source code links
- Project images/screenshots

### Design & UX (7 parameters)
- Professional design
- Consistent styling
- Good color scheme
- Readable typography
- Responsive design (mobile/tablet/desktop)
- Fast load times
- No broken images/links

### Technical (5 parameters)
- Custom domain
- HTTPS enabled
- Clean URL structure
- Meta tags (SEO)
- No console errors

---

## Architecture

### Backend Flow
```
Request → FastAPI → Analyzer → Scraper → AI Service → Response
                         ↓
                      Cache DB
```

### Frontend Flow
```
User → React Component → API Service → Backend API
  ↓                           ↓
UI Update ← Process Response ← JSON Data
```

### Batch Processing
```
CSV Upload → Parse → Queue → Concurrent Analysis → Aggregate Results
                                    ↓
                              Cache Individual Results
```

---

## Performance

- **Single Analysis**: 15-25 seconds
- **Batch Analysis**: ~20 seconds per portfolio (with concurrency)
- **Cache Hit**: < 1 second
- **Concurrent Limit**: Configurable (default: 5)

---

## Troubleshooting

### Common Issues

**Backend won't start**
```bash
# Check Python version
python --version  # Should be 3.12+

# Reinstall dependencies
pip install -r requirements.txt

# Check logs
tail -f logs/portalyze.log
```

**Frontend build fails**
```bash
# Clear cache and rebuild
rm -rf node_modules/.vite dist
npm install
npm run build
```

**Port already in use**
```bash
# Kill process on port
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:5173 | xargs kill -9  # Frontend
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Support

- **Documentation**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Issues**: Open an issue on GitHub
- **Contact**: [your-email@domain.com]

---

## Acknowledgments

- Google Gemini for AI analysis
- Groq for fast inference
- Playwright for browser automation
- MediaPipe for face detection
- FastAPI for the backend framework
- React for the frontend framework

---

Made with ❤️ by Masai School
