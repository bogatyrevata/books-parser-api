# api/dependencies.py
from sqlalchemy.orm import Session, sessionmaker
from database import get_engine

# создаём engine один раз при старте
engine = get_engine()
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

