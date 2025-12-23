import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_DB_PATH = Path(__file__).resolve().parent / "test.db"

os.environ.setdefault("POSTGRES_URL", f"sqlite:///{TEST_DB_PATH}")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")

from main import app  # noqa: E402
from database import Base, engine  # noqa: E402


@pytest.fixture()
def client():
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    Base.metadata.create_all(bind=engine)

    with TestClient(app) as test_client:
        yield test_client

    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
