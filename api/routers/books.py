from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database import Book, User
from api.dependencies import get_db
from api.schemas import BookSchema, BookCreate, BookUpdate
from api.auth import get_current_user, get_admin_user

# Роуты для работы с книгами
books_router = APIRouter(
    prefix="/books",  # все роуты начинаются с /books
    tags=["books"]    # группировка в Swagger
)

@books_router.get("", response_model=list[BookSchema])
async def get_books(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book).options(selectinload(Book.category)))
    return result.scalars().all()

# только для залогиненных
@books_router.post("", response_model=BookSchema, status_code=201)
async def create_book(book: BookCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Book).where(Book.url == book.url).options(selectinload(Book.category)))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Book already exists")
    new_book = Book(**book.model_dump())
    db.add(new_book)
    await db.commit()
    await db.refresh(new_book)
    return new_book

@books_router.get("/{book_id}", response_model=BookSchema)
async def get_book(book_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book).where(Book.id == book_id).options(selectinload(Book.category)))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

# только для админа
@books_router.put("/{book_id}", response_model=BookSchema)
async def update_book(book_id: int, book: BookCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_admin_user)):
    result = await db.execute(select(Book).where(Book.id == book_id))
    existing_book = result.scalar_one_or_none()
    if not existing_book:
        raise HTTPException(status_code=404, detail="Book not found")
    for key, value in book.model_dump().items():
        setattr(existing_book, key, value)
    await db.commit()
    await db.refresh(existing_book)
    return existing_book

@books_router.patch("/{book_id}", response_model=BookSchema)
async def patch_book(book_id: int, book: BookUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_admin_user)):
    result = await db.execute(select(Book).where(Book.id == book_id))
    existing_book = result.scalar_one_or_none()
    if not existing_book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # exclude_unset=True — берём только те поля которые пришли в запросе
    for key, value in book.model_dump(exclude_unset=True).items():
        setattr(existing_book, key, value)
    
    await db.commit()
    await db.refresh(existing_book)
    return existing_book


@books_router.delete("/{book_id}", status_code=204)
async def delete_book(book_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_admin_user)):
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    await db.delete(book)
    await db.commit()
    return None