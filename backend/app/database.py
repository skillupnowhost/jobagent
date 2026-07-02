from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import get_settings

settings = get_settings()

connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    _migrate_add_missing_columns()


def _migrate_add_missing_columns():
    """Lightweight auto-migration for pre-existing databases (no Alembic in use)."""
    inspector = inspect(engine)
    if "user_profiles" not in inspector.get_table_names():
        return
    existing_columns = {col["name"] for col in inspector.get_columns("user_profiles")}
    if "hashed_password" not in existing_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE user_profiles ADD COLUMN hashed_password VARCHAR(255)"))
