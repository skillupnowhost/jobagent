import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.config import get_settings
from app.database import init_db
from app.api.routes import router
from app.services.scheduler import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing AI Job Application Agent...")
    init_db()
    logger.info("Database initialized")

    start_scheduler()
    logger.info("Scheduler started — automated job search is active")

    resumes_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resumes")
    os.makedirs(resumes_dir, exist_ok=True)

    yield

    logger.info("Shutting down AI Job Application Agent...")


app = FastAPI(
    title="AI Job Application Agent",
    description="Automated 24/7 job application agent with resume generation, job matching, and tracking",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# Serve React frontend from /static if it exists (production single-container mode)
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        file_path = STATIC_DIR / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(STATIC_DIR / "index.html"))
else:
    @app.get("/")
    def root():
        return {
            "name": "AI Job Application Agent",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs",
            "note": "Frontend not bundled. Run frontend separately: cd frontend && npm run dev",
        }
