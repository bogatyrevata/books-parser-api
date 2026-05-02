from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware
from api.routers.categories import categories_router
from api.routers.books import books_router
from api.routers.auth import auth_router

app = FastAPI(title="Books API")

# Разрешаем CORS для React приложения, чтобы оно могло обращаться к API без проблем с политикой одного источника (Same-Origin Policy). Это важно для разработки фронтенда и бэкенда на разных портах.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # адрес React приложения
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(categories_router)
app.include_router(books_router)
app.include_router(auth_router) 