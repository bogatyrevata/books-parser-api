# api/dependencies.py
from sqlalchemy.orm import Session
from database import get_engine

# Dependency для получения сессии базы данных. 
def get_db():
    db = Session(bind=get_engine())
    try:
        yield db
    finally:
        db.close()