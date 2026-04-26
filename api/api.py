from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import Base, get_engine, Category, Book, User
from api.schemas import CategorySchema, CategoryCreate, BookSchema, BookCreate, BookUpdate
from api.dependencies import get_db

from fastapi.middleware.cors import CORSMiddleware

from fastapi.security import OAuth2PasswordRequestForm
from api.auth import hash_password, verify_password, create_access_token, get_current_user, get_admin_user
from api.schemas import UserCreate, UserSchema, TokenSchema


app = FastAPI(title="Books API")

# Разрешаем CORS для React приложения, чтобы оно могло обращаться к API без проблем с политикой одного источника (Same-Origin Policy). Это важно для разработки фронтенда и бэкенда на разных портах.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # адрес React приложения
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- КАТЕГОРИИ ---

@app.get("/categories", response_model=list[CategorySchema])
def get_categories(db: Session = Depends(get_db)): #Dependency Injection — это паттерн когда объект не создаёт зависимости сам, а получает их снаружи. В данном случае, мы не создаём сессию базы данных внутри функции, а получаем её через аргумент db, который заполняется с помощью Depends(get_db). Это позволяет легко менять реализацию get_db или использовать её в других местах без изменения кода функции.
    return db.query(Category).all()

# только для админа
@app.post("/categories", response_model=CategorySchema, status_code=201)
def create_category(category: CategoryCreate, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)): #Type hints — это способ указать тип данных для аргументов функции и её возвращаемого значения. В данном случае, мы указываем что аргумент category должен быть типа CategoryCreate, а возвращаемое значение должно быть типа CategorySchema. Это помогает разработчикам и инструментам разработки понимать структуру данных и предотвращать ошибки.
    existing = db.query(Category).filter(Category.name == category.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    
    new_category = Category(name=category.name)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category


@app.get("/categories/{category_id}", response_model=CategorySchema)
def get_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@app.delete("/categories/{category_id}", status_code=204)
def delete_category(category_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(category)
    db.commit()

# --- КНИГИ ---

# открыт для всех
@app.get("/books", response_model=list[BookSchema])
def get_books(db: Session = Depends(get_db)):
    return db.query(Book).all()

# только для залогиненных
@app.post("/books", response_model=BookSchema, status_code=201)
def create_book(book: BookCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing = db.query(Book).filter(Book.url == book.url).first()
    if existing:
        raise HTTPException(status_code=400, detail="Book already exists")
    new_book = Book(**book.model_dump())
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return new_book

# только для админа
@app.put("/books/{book_id}", response_model=BookSchema)
def update_book(book_id: int, book: BookCreate, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    existing_book = db.query(Book).filter(Book.id == book_id).first()
    if not existing_book:
        raise HTTPException(status_code=404, detail="Book not found")
    for key, value in book.model_dump().items():
        setattr(existing_book, key, value)
    db.commit()
    db.refresh(existing_book)
    return existing_book



@app.put("/books/{book_id}", response_model=BookSchema)
def update_book(book_id: int, book: BookCreate, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    existing_book = db.query(Book).filter(Book.id == book_id).first()
    if not existing_book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    for key, value in book.model_dump().items():
        setattr(existing_book, key, value)
    
    db.commit()
    db.refresh(existing_book)
    return existing_book

@app.patch("/books/{book_id}", response_model=BookSchema)
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


@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(book)
    db.commit()
    return None


# --- АВТОРИЗАЦИЯ ---

@app.post("/auth/register", response_model=UserSchema, status_code=201)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # проверяем что такого пользователя нет
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Пользователь уже существует")

    # первый пользователь становится админом
    is_first = db.query(User).count() == 0

    new_user = User(
        username=user.username,
        email=user.email,
        password=hash_password(user.password),
        is_admin=is_first
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/auth/login", response_model=TokenSchema)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/auth/me", response_model=UserSchema)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user