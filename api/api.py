from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import Base, get_engine, Category, Book
from api.schemas import CategorySchema, CategoryCreate, BookSchema, BookCreate, BookUpdate

from fastapi.middleware.cors import CORSMiddleware

#Запрос от клиента
#1. Uvicorn — принимает HTTP запрос
#2. Middleware — обрабатывает запрос до роута
#3. Router — находит нужную функцию по пути и методу
#4. Depends — вызывает get_db, создаёт сессию
#5. Pydantic — парсит и валидирует тело запроса
#6. Функция — выполняется с готовыми данными
#7. Pydantic — сериализует ответ через response_model
#`8. Uvicorn — отправляет JSON клиенту

app = FastAPI(title="Books API")

# Разрешаем CORS для React приложения, чтобы оно могло обращаться к API без проблем с политикой одного источника (Same-Origin Policy). Это важно для разработки фронтенда и бэкенда на разных портах.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # адрес React приложения
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = Session(bind=get_engine())
    try:
        yield db
    finally:
        db.close()


# --- КАТЕГОРИИ ---

@app.get("/categories", response_model=list[CategorySchema])
def get_categories(db: Session = Depends(get_db)): #Dependency Injection — это паттерн когда объект не создаёт зависимости сам, а получает их снаружи. В данном случае, мы не создаём сессию базы данных внутри функции, а получаем её через аргумент db, который заполняется с помощью Depends(get_db). Это позволяет легко менять реализацию get_db или использовать её в других местах без изменения кода функции.
    return db.query(Category).all()


@app.post("/categories", response_model=CategorySchema, status_code=201)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)): #Type hints — это способ указать тип данных для аргументов функции и её возвращаемого значения. В данном случае, мы указываем что аргумент category должен быть типа CategoryCreate, а возвращаемое значение должно быть типа CategorySchema. Это помогает разработчикам и инструментам разработки понимать структуру данных и предотвращать ошибки.
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
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(category)
    db.commit()

# --- КНИГИ ---

@app.get("/books", response_model=list[BookSchema])
def get_books(db: Session = Depends(get_db)):
    return db.query(Book).all()


@app.post("/books", response_model=BookSchema, status_code=201)
def create_book(book: BookCreate, db: Session = Depends(get_db)):
    existing = db.query(Book).filter(Book.url == book.url).first()
    if existing:
        raise HTTPException(status_code=400, detail="Book already exists")
    
    new_book = Book(**book.model_dump())#model_dump() — это Pydantic метод который превращает схему в словарь {"title": "...", "price": ...}, а ** распаковывает его в аргументы.
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return new_book


@app.get("/books/{book_id}", response_model=BookSchema)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@app.put("/books/{book_id}", response_model=BookSchema)
def update_book(book_id: int, book: BookCreate, db: Session = Depends(get_db)):
    existing_book = db.query(Book).filter(Book.id == book_id).first()
    if not existing_book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    for key, value in book.model_dump().items():
        setattr(existing_book, key, value)
    
    db.commit()
    db.refresh(existing_book)
    return existing_book

@app.patch("/books/{book_id}", response_model=BookSchema)
def patch_book(book_id: int, book: BookUpdate, db: Session = Depends(get_db)):
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
def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(book)
    db.commit()
    return None