from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from dotenv import load_dotenv
import os

load_dotenv()

Base = declarative_base()

class Category(Base):
    __tablename__ = 'categories'
    id    = Column(Integer, primary_key=True)
    name  = Column(String, unique=True, nullable=False)
    books = relationship('Book', back_populates='category')

class Book(Base):
    __tablename__ = 'books'

    id       = Column(Integer, primary_key=True)
    title    = Column(String, nullable=False)
    url      = Column(String, unique=True)
    price    = Column(Float)
    in_stock = Column(Boolean)
    rating   = Column(Integer)
    category_id = Column(Integer, ForeignKey('categories.id'))  # <-- новое

    # relationship для удобного доступа: book.category
    category = relationship('Category', back_populates='books')  # <-- новое

class User(Base):
    __tablename__ = 'users'

    id       = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email    = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)  # хэш пароля
    is_admin = Column(Boolean, default=False)

class RefreshToken(Base):
    __tablename__ = 'refresh_tokens'

    id         = Column(Integer, primary_key=True)
    token      = Column(String, unique=True, nullable=False)
    user_id    = Column(Integer, ForeignKey('users.id'), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    user       = relationship('User', backref='refresh_tokens')


def get_engine():
    # postgresql+asyncpg вместо postgresql+psycopg2
    url = f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    return create_async_engine(url)
