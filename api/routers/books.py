from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
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
def get_books(db: Session = Depends(get_db)):
    return db.query(Book).all()

# только для залогиненных
@books_router.post("", response_model=BookSchema, status_code=201)
def create_book(book: BookCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing = db.query(Book).filter(Book.url == book.url).first()
    if existing:
        raise HTTPException(status_code=400, detail="Book already exists")
    new_book = Book(**book.model_dump())
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return new_book

@books_router.get("/{book_id}", response_model=BookSchema)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

# только для админа
@books_router.put("/{book_id}", response_model=BookSchema)
def update_book(book_id: int, book: BookCreate, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    existing_book = db.query(Book).filter(Book.id == book_id).first()
    if not existing_book:
        raise HTTPException(status_code=404, detail="Book not found")
    for key, value in book.model_dump().items():
        setattr(existing_book, key, value)
    db.commit()
    db.refresh(existing_book)
    return existing_book

@books_router.patch("/{book_id}", response_model=BookSchema)
def patch_book(book_id: int, book: BookUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    existing_book = db.query(Book).filter(Book.id == book_id).first()
    if not existing_book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # exclude_unset=True — берём только те поля которые пришли в запросе
    for key, value in book.model_dump(exclude_unset=True).items():
        setattr(existing_book, key, value)
    
    db.commit()
    db.refresh(existing_book)
    return existing_book


@books_router.delete("/{book_id}", status_code=204)
def delete_book(book_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(book)
    db.commit()
    return None