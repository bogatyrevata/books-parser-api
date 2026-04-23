# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from database import Book, Base
from api.api import app, get_db


@pytest.fixture
def db_session():
    """
    Фикстура — специальная функция pytest.
    Создаёт чистую тестовую БД перед каждым тестом
    и удаляет её после. Вместо PostgreSQL используем
    SQLite :memory: — она живёт только в оперативной памяти.
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)          # создаём таблицы
    with Session(engine) as session:
        yield session                         # отдаём сессию тесту
    Base.metadata.drop_all(engine)            # убираем за собой
