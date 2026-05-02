# tests/conftest.py
import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from database import Base
from api.api import app, get_db

TEST_DB = "test.db"

engine = create_engine(
    f"sqlite:///{TEST_DB}",
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(bind=engine)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture
def client():
    def override_get_db():
        with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def admin_client(client):
    # регистрируем первого пользователя — он станет админом
    client.post("/auth/register", json={
        "username": "admin",
        "email": "admin@test.com",
        "password": "12345"
    })
    # логинимся и получаем токен
    response = client.post("/auth/login", data={
        "username": "admin",
        "password": "12345"
    })
    token = response.json()["access_token"]

    # добавляем токен в заголовки клиента
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client