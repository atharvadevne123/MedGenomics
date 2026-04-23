import os

# Must be set before importing src.main so the module-level DATABASE_URL picks it up
os.environ["DATABASE_URL"] = "sqlite:///./test_medgenomics.db"

import pytest
from fastapi.testclient import TestClient

from src.main import Base, SessionLocal, app, engine, seed_data


@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test_medgenomics.db"):
        os.remove("test_medgenomics.db")
