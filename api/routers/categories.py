from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import Category
from api.dependencies import get_db
from api.schemas import CategorySchema, CategoryCreate
from api.auth import get_admin_user

categories_router = APIRouter(
    prefix="/categories",
    tags=["categories"]
)

@categories_router.get("", response_model=list[CategorySchema])
async def get_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category))
    return result.scalars().all()

@categories_router.post("", response_model=CategorySchema, status_code=201)
async def create_category(category: CategoryCreate, db: AsyncSession = Depends(get_db), current_user=Depends(get_admin_user)):
    result = await db.execute(select(Category).where(Category.name == category.name))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    new_category = Category(name=category.name)
    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)
    return new_category

@categories_router.get("/{category_id}", response_model=CategorySchema)
async def get_category(category_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@categories_router.delete("/{category_id}", status_code=204)
async def delete_category(category_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_admin_user)):
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    await db.delete(category)
    await db.commit()