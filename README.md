# AI Job Application Agent

A fully automated, 24/7 AI-powered job application system that searches for jobs, generates tailored resumes, applies to positions, and tracks everything through a responsive dashboard.

## Features

### 1. ATS-Friendly Resume Generation
- Generates perfectly aligned, professional PDF resumes
- Tailors content to each job description using NLP
- Built-in spell checker and error detection
- Supports 1-2 page layouts with no spacing gaps
- Highlights matching skills for each application

### 2. Multi-Portal Job Search
- Searches across Adzuna, Remotive, JSearch (LinkedIn, Glassdoor, Indeed aggregator)
- NLP-powered job matching using TF-IDF cosine similarity
- Filters by experience level, salary, location, and company type
- Prioritizes MNC companies and top employers
- Runs automatically every 4 hours

### 3. Automated Application Pipeline
- Generates tailored resume + cover letter per job
- Tracks application status through full lifecycle
- Automated follow-up emails with scheduling
- Error detection before submission
- Daily application reports

### 4. Responsive Dashboard
- Real-time statistics and charts
- Application tracking with status management
- Resume preview and download
- Job search with filters
- Mobile and desktop optimized

### 5. Google Calendar Integration
- Follow-up reminders synced to Google Calendar
- Interview scheduling alerts
- Daily report reminders
- Email notifications for all events

### 6. AI Skill Gap Analysis
- Analyzes skill gaps across all applications
- Tracks learning progress with proficiency scores
- Personalized learning paths with resource recommendations
- Refines job targeting based on skill improvements
- Demand tracking across job market

### 7. Salary & Job Security Matching
- Minimum 10 LPA salary filtering
- Applies to MNCs even with undisclosed salary
- Experience-level matching (2.6 years)
- Company type classification (MNC, startup, etc.)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI |
| Frontend | React 18, Vite, Tailwind CSS |
| Database | SQLAlchemy (SQLite / PostgreSQL) |
| PDF Generation | ReportLab |
| NLP | scikit-learn (TF-IDF), NLTK |
| Job Search | Adzuna API, Remotive API, JSearch API |
| Email | SMTP (Gmail) |
| Calendar | Google Calendar API |
| Scheduler | APScheduler |
| Deployment | Docker, AWS ECS Fargate |
| Charts | Recharts |

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Redis (optional, for task queue)

### 1. Clone and Configure
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

### 2. Start Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Start Frontend
```bash
cd frontend
npm install
npm run dev
```

### 4. Open Dashboard
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs

### Docker Deployment
```bash
docker-compose up --build -d
# Frontend: http://localhost
# Backend: http://localhost:8000
```

### AWS Deployment
```bash
# Set environment variables
export AWS_ACCOUNT_ID=your-account-id
export AWS_REGION=ap-south-1

# Deploy to ECS Fargate
bash infrastructure/deploy.sh aws
```

## Configuration

### Required API Keys
| Service | Purpose | Get Key |
|---------|---------|---------|
| Adzuna | Job search API | https://developer.adzuna.com |
| RapidAPI (JSearch) | Multi-portal aggregator | https://rapidapi.com |
| Gmail App Password | Email automation | Google Account > Security |
| Google Calendar | Follow-up reminders | Google Cloud Console |

### Setting Up Google Calendar
1. Create a project at https://console.cloud.google.com
2. Enable Google Calendar API
3. Create OAuth 2.0 credentials
4. Download as `credentials.json` in backend directory
5. Run the app — it will prompt for authorization on first use

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard` | Dashboard data |
| GET/POST | `/api/profile` | User profile |
| POST | `/api/resume/generate` | Generate resume PDF |
| GET | `/api/jobs/search` | Search jobs |
| POST | `/api/jobs/trigger-search` | Trigger automated search |
| GET | `/api/applications` | List applications |
| GET | `/api/applications/stats` | Application statistics |
| GET | `/api/skills/gaps` | Skill gap analysis |
| POST | `/api/skills/progress` | Log learning progress |
| GET | `/api/reports/daily` | Daily report |

## Automated Schedule

| Task | Frequency | Description |
|------|-----------|-------------|
| Job Search | Every 4 hours | Searches all portals for matching jobs |
| Follow-up Emails | Daily at 10 AM | Sends follow-ups for pending applications |
| Daily Report | Daily at 9 AM | Generates daily application report |
| Skill Demand Update | Weekly (Monday 6 AM) | Updates skill demand data |

## Project Structure

```
Resume Agent/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Settings
│   │   ├── database.py          # DB setup
│   │   ├── models/              # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── job.py
│   │   │   ├── application.py
│   │   │   └── skill.py
│   │   ├── services/            # Business logic
│   │   │   ├── resume_builder.py    # ATS PDF generation
│   │   │   ├── job_search.py        # Multi-portal search
│   │   │   ├── job_matcher.py       # NLP matching
│   │   │   ├── application_tracker.py
│   │   │   ├── email_service.py     # SMTP emails
│   │   │   ├── calendar_service.py  # Google Calendar
│   │   │   ├── skill_analyzer.py    # Gap analysis
│   │   │   └── scheduler.py        # APScheduler jobs
│   │   └── api/
│   │       └── routes.py           # All API routes
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 # Layout + routing
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx       # Stats overview
│   │   │   ├── Applications.jsx    # Application tracker
│   │   │   ├── Jobs.jsx            # Job search
│   │   │   ├── Resume.jsx          # Resume generator
│   │   │   ├── Skills.jsx          # Skill analysis
│   │   │   ├── Reports.jsx         # Daily reports
│   │   │   └── Profile.jsx         # User profile
│   │   └── services/
│   │       └── api.js              # API client
│   ├── package.json
│   └── Dockerfile
├── infrastructure/
│   ├── aws-ecs-task-definition.json
│   └── deploy.sh
├── docker-compose.yml
├── .env.example
└── README.md
```
