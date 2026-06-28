import asyncio
import os
import csv
from dotenv import load_dotenv
from urllib.parse import urljoin
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select
from database import Book, Category, Base, get_engine
from loguru import logger
from playwright.async_api import async_playwright


logger.add("logs/parser/parser.log", 
           rotation="1 MB",       # новый файл когда вырастет до 1MB
           retention="7 days",    # хранить логи 7 дней
           level="INFO")          # писать INFO и выше

load_dotenv()

BASE_URL = "http://books.toscrape.com"
MAIN_URL = f"{BASE_URL}/catalogue/category/books_1/index.html"
rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


async def parse_categories(page) -> list[dict]:
    """Парсит все категории с главной страницы"""
    await page.goto(MAIN_URL)
    await page.wait_for_selector("ul.nav-list")

    categories = []
    links = await page.query_selector_all("ul.nav-list li ul li a")

    for link in links:
        name = (await link.inner_text()).strip()
        relative_url = await link.get_attribute("href")
        url = urljoin(MAIN_URL, relative_url)
        categories.append({"name": name, "url": url})
        logger.info(f"Категория: {name} | {url}")

    return categories


async def parse_books_by_category(page, category_url: str, limit: int) -> list[dict]:
    """Парсит книги по URL категории"""
    all_books = []
    url = category_url

    await page.goto(url)

    while len(all_books) < limit:
        try:
            await page.wait_for_selector("article.product_pod")
            books = await page.query_selector_all("article.product_pod")

            for book in books:
                if len(all_books) >= limit:
                    break

                title = await (await book.query_selector("h3 a")).get_attribute("title")
                relative_url = await (await book.query_selector("h3 a")).get_attribute("href")
                book_url = urljoin(url, relative_url)
                price_text = await (await book.query_selector("p.price_color")).inner_text()
                price = float(price_text.replace('£', '').strip())
                stock_text = await (await book.query_selector("p.instock.availability")).inner_text()
                in_stock = 'In stock' in stock_text
                rating_class = await (await book.query_selector("p.star-rating")).get_attribute("class")
                rating_name = rating_class.split()[1]
                rating = rating_map.get(rating_name, 0)

                all_books.append({
                    "title": title,
                    "url": book_url,
                    "price": price,
                    "in_stock": in_stock,
                    "rating": rating
                })

                logger.info(f"{len(all_books)}. {title} | {price} | {rating}")
                await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"Ошибка при парсинге {url}: {e}")
            break

        next_btn = await page.query_selector("li.next a")
        if next_btn:
            await next_btn.click()
            await page.wait_for_load_state("networkidle")
        else:
            break

    return all_books


async def save_categories(categories: list[dict], db: AsyncSession) -> list[Category]:
    saved = []
    for cat in categories:
        # проверяем по url
        result = await db.execute(select(Category).where(Category.url == cat['url']))
        existing = result.scalar_one_or_none()

        if not existing:
            # проверяем по имени
            result = await db.execute(select(Category).where(Category.name == cat['name']))
            existing_by_name = result.scalar_one_or_none()

            if existing_by_name:
                # обновляем url у существующей категории
                existing_by_name.url = cat['url']
                await db.flush()
                saved.append(existing_by_name)
                logger.info(f"Обновлён URL категории: {cat['name']}")
            else:
                # создаём новую
                new_cat = Category(name=cat['name'], url=cat['url'])
                db.add(new_cat)
                await db.flush()
                saved.append(new_cat)
                logger.info(f"Сохранена категория: {cat['name']}")
        else:
            saved.append(existing)
            logger.warning(f"Уже в БД: {cat['name']}")

    await db.commit()
    return saved


async def save_books(books: list[dict], category_id: int, db: AsyncSession) -> None:
    """Сохраняет книги в базу данных"""
    counter = 0
    skipped = 0
    for book in books:
        result = await db.execute(select(Book).where(Book.url == book['url']))
        exists = result.scalar_one_or_none()
        if not exists:
            db.add(Book(**book, category_id=category_id))
            counter += 1
        else:
            skipped += 1
            logger.warning(f"Уже в БД: {book['title']}")
    await db.commit()
    logger.info(f"Сохранено: {counter} | Пропущено: {skipped}")


async def main():
    LIMIT_BOOKS = int(os.getenv("LIMIT_BOOKS", 10))

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # шаг 1 — парсим категории
        logger.info("Парсим категории...")
        categories = await parse_categories(page)
        logger.info(f"Найдено категорий: {len(categories)}")

        async with AsyncSessionLocal() as db:
            saved_categories = await save_categories(categories, db)

        # шаг 2 — парсим книги по первой категории (или по CATEGORY_URL из .env)
        category_url = os.getenv("CATEGORY_URL", categories[0]['url'] if categories else None)
        if category_url:
            logger.info(f"Парсим книги из: {category_url}")
            books = await parse_books_by_category(page, category_url, LIMIT_BOOKS)

            # находим категорию в базе
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(Category).where(Category.url == category_url))
                category = result.scalar_one_or_none()
                if category:
                    await save_books(books, category.id, db)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())