from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import declarative_base, Session
import os

Base = declarative_base()

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
    books = relationship('Book', back_populates='category')  # <-- обратная с

def get_engine():
    url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    return create_engine(url)

class User(Base):
    __tablename__ = 'users'

    id       = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email    = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)  # хэш пароля
    is_admin = Column(Boolean, default=False)