# tests/conftest.py
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from fastapi.testclient import TestClient
from database import Base
from api.api import app
from api.dependencies import get_db

TEST_DB = "test.db"

engine = create_async_engine(
    f"sqlite+aiosqlite:///{TEST_DB}",
    connect_args={"check_same_thread": False}
)

AsyncTestingSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def client():
    async def override_get_db():
        async with AsyncTestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def admin_client(client):
    client.post("/auth/register", json={
        "username": "admin",
        "email": "admin@test.com",
        "password": "12345"
    })
    response = client.post("/auth/login", data={
        "username": "admin",
        "password": "12345"
    })
    token = response.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client