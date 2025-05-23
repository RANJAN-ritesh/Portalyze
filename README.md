# Portfolio Grader

An automated tool for grading developer portfolios based on best practices and common requirements.

## Features

- Static code analysis of GitHub repositories
- Dynamic analysis of deployed websites
- Comprehensive grading based on multiple criteria
- Detailed feedback and scoring
- Responsive design testing
- Link validation
- Design issue detection

## Grading Criteria

The portfolio is graded based on the following criteria:

### Required Sections (20%)
- About Me
- Skills
- Projects
- Contact

### About Section (15%)
- Professional photo
- Name
- Catchy introduction

### Projects Section (25%)
- At least 3 projects
- Project summary
- Hero image
- Tech stack information
- Deployed link

### Skills Section (10%)
- Visual presentation (icons/cards)
- Tech stack highlighting

### Contact Section (15%)
- LinkedIn link
- GitHub link
- Contact form

### Links (5%)
- All external links open in new tab
- No broken links

### Responsiveness (5%)
- Works on mobile, tablet, and desktop
- No horizontal scrollbars
- Proper media queries

### Design Issues (5%)
- No JavaScript errors
- No broken images
- Clean design

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/portfolio-grader.git
cd portfolio-grader
```

2. Create a virtual environment:
```bash
python -m venv venv  ||  python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
playwright install
```

## Usage

1. Start the server:
```bash
uvicorn app.main:app --reload
```

2. Send a POST request to `/grade` with the following JSON body:
```json
{
    "github_url": "https://github.com/username/portfolio",
    "deployed_url": "https://your-portfolio.com",
    "name": "Your Name"  // Optional
}
```

3. The response will include:
- Overall score
- Detailed feedback
- Section-by-section analysis
- Design issues
- Link status

## API Documentation

Once the server is running, visit `http://localhost:8000/docs` for interactive API documentation.

## Development

### Project Structure
```
portfolio-grader/
├── app/
│   ├── main.py              # FastAPI application
│   ├── services/
│   │   ├── github_analyzer.py    # GitHub repository analysis
│   │   └── website_analyzer.py   # Deployed website analysis
│   └── models/
│       └── grading_result.py     # Grading result model
├── requirements.txt
└── README.md
```

### Running Tests
```bash
pytest
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details 