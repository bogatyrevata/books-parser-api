import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.auth import get_admin_user
from api.dependencies import get_db
from api.schemas import CategorySchema
from database import Category, get_engine

parser_router = APIRouter(
    prefix="/parser",
    tags=["parser"]
)


async def run_category_parser() -> list[dict]:
    """Запускает парсер категорий и возвращает список категорий"""
    from playwright.async_api import async_playwright

    from parser.main import parse_categories, save_categories

    engine = get_engine()
    AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        categories = await parse_categories(page)
        await browser.close()

    async with AsyncSessionLocal() as db:
        saved = await save_categories(categories, db)
        return [{"id": c.id, "name": c.name, "url": c.url} for c in saved]


async def run_books_parser(category_url: str, category_id: int) -> dict:
    """Запускает парсер книг по категории"""
    from playwright.async_api import async_playwright

    from parser.main import parse_books_by_category, save_books

    LIMIT_BOOKS = int(os.getenv("LIMIT_BOOKS", "10"))
    engine = get_engine()
    AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        books = await parse_books_by_category(page, category_url, LIMIT_BOOKS)
        await browser.close()

    async with AsyncSessionLocal() as db:
        await save_books(books, category_id, db)

    return {"parsed": len(books)}


@parser_router.post("/categories", response_model=list[CategorySchema])
async def parse_categories_route(current_user=Depends(get_admin_user)):
    """Запускает парсинг всех категорий — только для админа"""
    try:
        categories = await run_category_parser()
        return categories
    except Exception as e:  # noqa: BLE001 — парсер может упасть по многим причинам (Playwright, сеть, БД), отдаём как есть в HTTP-ответе
        raise HTTPException(status_code=500, detail=str(e))


@parser_router.post("/books/{category_id}")
async def parse_books_route(category_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_admin_user)):
    """Запускает парсинг книг по категории — только для админа"""
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")

    if not category.url:
        raise HTTPException(status_code=400, detail="У категории нет URL для парсинга")

    try:
        result = await run_books_parser(category.url, category_id)
        return {"message": f"Спарсено книг: {result['parsed']}", "category": category.name}
    except Exception as e:  # noqa: BLE001 — см. комментарий выше
        raise HTTPException(status_code=500, detail=str(e))
    

@parser_router.get("/settings")
async def get_settings(current_user=Depends(get_admin_user)):
    return {"limit_books": int(os.getenv("LIMIT_BOOKS", "10"))}


@parser_router.post("/settings")
async def update_settings(limit_books: int, current_user=Depends(get_admin_user)):
    os.environ["LIMIT_BOOKS"] = str(limit_books)
    return {"limit_books": limit_books}