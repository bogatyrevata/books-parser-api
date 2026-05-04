import asyncio
import os
import csv
from dotenv import load_dotenv
from urllib.parse import urljoin
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select
from database import Book, Base, get_engine
from loguru import logger
from playwright.async_api import async_playwright


logger.add("logs/parser.log", 
           rotation="1 MB",       # новый файл когда вырастет до 1MB
           retention="7 days",    # хранить логи 7 дней
           level="INFO")          # писать INFO и выше

load_dotenv()

LIMIT_BOOKS = int(os.getenv("LIMIT_BOOKS")) # Получаем лимит из переменных окружения
current_url = os.getenv("CATEGORY_URL")
rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

all_books = []

async def parse_books() -> list[dict]:
    '''Парсит книги с сайта и возвращает список словарей с данными о книгах.
      Каждая книга представлена словарём с ключами: title, url, price, in_stock, rating. 
      Функция использует Playwright для асинхронного взаимодействия с сайтом. 
      Она открывает браузер, переходит по URL категории книг и извлекает данные о каждой книге на странице. 
      Если количество собранных книг достигает LIMIT_BOOKS, парсинг прекращается. 
      Если на странице есть кнопка "next", функция кликает по ней и продолжает парсинг следующей страницы. 
      В случае ошибок при парсинге страницы, ошибка логируется и парсинг прекращается.'''
    all_books = []
    url = current_url
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)#открывает окно браузера, false чтобы видеть процесс, true для работы в фоне
        page = await browser.new_page() #открывает новую вкладку
        await page.goto(url)#переходит по URL категории книг

        while len(all_books) < LIMIT_BOOKS:
            # Ждём карточки книг
            try:            
                await page.wait_for_selector("article.product_pod")#ждём пока на странице появится элемент с классом product_pod, который соответствует карточке книги. Это гарантирует, что страница полностью загрузилась и мы можем безопасно извлекать данные о книгах.

                # Берём все карточки
                books = await page.query_selector_all("article.product_pod")

                for book in books:
                    if len(all_books) >= LIMIT_BOOKS:
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
                    
                    logger.info(f"{len(all_books)}. {title} | {price} | {rating} | {in_stock}")
                    await asyncio.sleep(1)  # asyncio.sleep позволяет приостановить выполнение текущей задачи на заданное количество секунд, не блокируя при этом выполнение других задач. Это особенно полезно в асинхронных программах, где нужно выполнять несколько операций одновременно, например, обрабатывать данные и делать запросы к серверу. В данном случае, после обработки каждой книги, мы делаем паузу в 1 секунду, чтобы не перегружать сайт слишком быстрыми запросами и имитировать более естественное поведение пользователя.
            
            except Exception as e:
                logger.error(f"Ошибка при парсинге страницы {url}: {e}")
                break   

            # Ищем кнопку next
            next_btn = await page.query_selector("li.next a")
            if next_btn:
                await next_btn.click()
                await page.wait_for_load_state("networkidle")
            else:
                break

        await browser.close()

    return all_books


async def save_to_csv(books: list[dict]) -> None:
    '''Сохраняет список книг в CSV файл. Каждая книга представлена словарём с ключами:
      title, url, price, in_stock, rating. Файл сохраняется с именем "books.csv" в 
      кодировке UTF-8. В первой строке файла записываются заголовки столбцов. 
      Каждая последующая строка соответствует одной книге из списка.'''
    with open("books.csv", "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["title", "url", "price", "in_stock", "rating"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for book in books:
            writer.writerow(book)
    logger.info(f"Сохранено в CSV: {len(books)} книг")


async def save_to_db(books: list[dict], engine) -> None:
    '''Сохраняет список книг в базу данных. Каждая книга представлена словарём с ключами:
      title, url, price, in_stock, rating. Функция использует SQLAlchemy для взаимодействия с базой данных. 
      Для каждой книги проверяется наличие записи с таким же URL. Если запись с таким URL уже существует, книга пропускается и логируется предупреждение. 
      Если книги с таким URL нет, она добавляется в базу данных. В конце функции логируется количество сохранённых книг и количество пропущенных из-за дублей. 
      В случае ошибок при сохранении в базу данных, ошибка логируется как критическая.'''
    AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
    try:
        async with AsyncSessionLocal() as db:
            counter = 0 # Счётчик сохранённых книг
            skipped = 0 # Счётчик пропущенных книг из-за дублей
            for book in books:
                result = await db.execute(select(Book).where(Book.url == book['url'])) # Проверяем, есть ли уже книга с таким URL в БД
                exists = result.scalar_one_or_none()
                if not exists:
                    db.add(Book(**book)) # Если книги с таким URL нет, добавляем её в БД
                    counter += 1
                else:
                    skipped += 1
                    logger.warning(f"Уже в БД: {book['title']}")
            await db.commit()
        logger.info(f"Сохранено в БД: {counter} книг | Пропущено дублей: {skipped}")
    except Exception as e:
        logger.critical(f"Ошибка сохранения в БД: {e}")

async def main():
    # создаём таблицы если нет
    engine = get_engine() # Получаем асинхронный движок базы данных, который будет использоваться для взаимодействия с базой данных. Этот движок создаётся с помощью функции get_engine(), которая обычно настраивается для подключения к конкретной базе данных, например, PostgreSQL.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # парсим
    books = await parse_books()
    logger.info(f"Всего книг: {len(books)}")

    # сохраняем
    await save_to_csv(books)
    await save_to_db(books, engine)


if __name__ == "__main__":
    asyncio.run(main())