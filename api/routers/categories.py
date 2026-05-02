from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import Category
from api.dependencies import get_db
from api.schemas import CategorySchema, CategoryCreate
from api.auth import get_admin_user

#Роуты для работы с категориями книг

categories_router = APIRouter(
    prefix="/categories",  # все роуты начинаются с /categories
    tags=["categories"]    # группировка в Swagger
)

@categories_router.get("", response_model=list[CategorySchema])
def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()

@categories_router.post("", response_model=CategorySchema, status_code=201)
def create_category(category: CategoryCreate, db: Session = Depends(get_db), current_user=Depends(get_admin_user)):
    existing = db.query(Category).filter(Category.name == category.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    new_category = Category(name=category.name)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@categories_router.get("/{category_id}", response_model=CategorySchema)
def get_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@categories_router.delete("/{category_id}", status_code=204)
def delete_category(category_id: int, db: Session = Depends(get_db), current_user=Depends(get_admin_user)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(category)
    db.commit()