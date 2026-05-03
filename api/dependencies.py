# api/dependencies.py
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from database import get_engine


engine = get_engine()
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session