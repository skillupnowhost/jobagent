import os
import tempfile

import pytest

_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"
os.environ["SMTP_USER"] = ""
os.environ["SMTP_PASSWORD"] = ""

from fastapi.testclient import TestClient  # noqa: E402

from app.core.rate_limit import limiter  # noqa: E402
from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="session")
def client():
    limiter.enabled = False
    with TestClient(app) as test_client:
        yield test_client
