import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.config import settings
from app.limiter import limiter
from app.main import app

TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture(autouse=True)
def test_runtime_settings():
    original_limiter_enabled = limiter.enabled
    original_anthropic_api_key = settings.anthropic_api_key
    original_anthropic_auth_token = settings.anthropic_auth_token
    limiter.enabled = False
    settings.anthropic_api_key = ""
    settings.anthropic_auth_token = ""
    yield
    limiter.enabled = original_limiter_enabled
    settings.anthropic_api_key = original_anthropic_api_key
    settings.anthropic_auth_token = original_anthropic_auth_token


@pytest.fixture
def db_session():
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
