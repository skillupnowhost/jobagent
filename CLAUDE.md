# AI Job Application Agent

Full-stack automated job application system.

## Architecture

- **Backend**: Python FastAPI (`backend/app/`)
- **Frontend**: React + Vite + Tailwind CSS (`frontend/src/`)
- **Database**: SQLAlchemy (SQLite dev / PostgreSQL prod)
- **Deployment**: Docker Compose, AWS ECS Fargate

## Commands

### Local Development
```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev
```

### Docker
```bash
docker-compose up --build
```

### Cloud Deploy
```bash
bash infrastructure/deploy.sh aws
```

## Key Directories

- `backend/app/models/` — SQLAlchemy database models
- `backend/app/services/` — Core business logic (resume, search, matcher, email, calendar, skills)
- `backend/app/api/routes.py` — All API endpoints
- `frontend/src/pages/` — React dashboard pages
- `infrastructure/` — Cloud deployment configs
