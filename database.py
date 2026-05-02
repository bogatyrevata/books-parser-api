from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.orm import declarative_base, Session
import os


Base = declarative_base()

def get_engine():
    url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    return create_engine(url)
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

class Category(Base):
    __tablename__ = 'categories'
    
    id   = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    books = relationship('Book', back_populates='category')  # <-- обратная сторона

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