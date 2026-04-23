# tests/conftest.py
import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from database import Base
from api.api import app, get_db

# @pytest.fixture
# def db_session():
#     engine = create_engine("sqlite:///:memory:")
#     Base.metadata.create_all(engine)
#     with Session(engine) as session:
#         yield session
#     Base.metadata.drop_all(engine)

# tests/conftest.py

TEST_DB = "test.db" # Файл для тестовой базы данных

engine = create_engine( # создаём движок для SQLite
    f"sqlite:///{TEST_DB}",# используем файл, а не :memory: чтобы видеть его в процессе отладки
    connect_args={"check_same_thread": False} # нужно для SQLite, чтобы разрешить доступ из разных потоков (FastAPI может работать в многопоточном режиме
)

TestingSessionLocal = sessionmaker(bind=engine) # создаём фабрику сессий, которая будет использовать наш тестовый движок

# Фикстура для настройки тестовой базы данных
@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

# Фикстура для получения сессии базы данных в тестах
@pytest.fixture
def db_session():
    with TestingSessionLocal() as session:
        yield session

# Фикстура для получения клиента API, который использует тестовую базу данных
@pytest.fixture
def client():
    def override_get_db():
        with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)# создаём тестового клиента FastAPI, который будет использовать нашу тестовую базу данных
    app.dependency_overrides.clear()