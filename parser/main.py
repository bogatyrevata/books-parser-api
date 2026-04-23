import time, os, csv
from dotenv import load_dotenv
from urllib.parse import urljoin

from database import Book, Base, get_engine
from sqlalchemy.orm import Session
from loguru import logger
from playwright.sync_api import sync_playwright

logger.add("logs/parser.log", 
           rotation="1 MB",       # новый файл когда вырастет до 1MB
           retention="7 days",    # хранить логи 7 дней
           level="INFO")          # писать INFO и выше

load_dotenv()

# Создаёт таблицу в БД если её ещё нет
engine = get_engine()
Base.metadata.create_all(engine)

all_books = []
LIMIT_BOOKS = int(os.getenv("LIMIT_BOOKS")) # Получаем лимит из переменных окружения

current_url = os.getenv("CATEGORY_URL")
rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)#открывает окно браузера, false чтобы видеть процесс, true для работы в фоне
    page = browser.new_page() #открывает новую вкладку

    page.goto(current_url)#переходит по URL категории книг
    while len(all_books) < LIMIT_BOOKS:
        # Ждём карточки книг
        try:            
            page.wait_for_selector("article.product_pod")#ждём пока на странице появится элемент с классом product_pod, который соответствует карточке книги. Это гарантирует, что страница полностью загрузилась и мы можем безопасно извлекать данные о книгах.

            # Берём все карточки
            books = page.query_selector_all("article.product_pod")

            for book in books:
                if len(all_books) >= LIMIT_BOOKS:
                    break
                title = book.query_selector("h3 a").get_attribute("title")
                relative_url = book.query_selector("h3 a").get_attribute("href") # Получаем относительный URL так как в playwright нет метода для получения абсолютного URL
                url = urljoin(current_url, relative_url) # склеиваем базовый URL с относительным, чтобы получить полный URL книги
                price = float(book.query_selector("p.price_color").inner_text().replace('£', '').strip())
                in_stock = 'In stock' in book.query_selector("p.instock.availability").inner_text() # Проверяем наличие книги в наличии, если в тексте элемента с классом instock.availability есть фраза 'In stock', то считаем, что книга есть в наличии
                rating_name = book.query_selector("p.star-rating").get_attribute("class").split()[1]  # получаем класс и разбиваем его по пробелу на части, чтобы извлечь название рейтинга (One, Two, Three, Four, Five)
                rating = rating_map.get(rating_name, 0)
                all_books.append({
                    "title": title, 
                    "url": url, 
                    "price": price, 
                    "in_stock": in_stock, 
                    "rating": rating
                    })
                
                logger.info(f"{len(all_books)}. {title} | {price} | {rating} | {in_stock}")
                time.sleep(1)  # пауза между запросами
        except Exception as e:
            logger.error(f"Ошибка при парсинге страницы {current_url}: {e}")
            break   

        # Ищем кнопку next
        next_btn = page.query_selector("li.next a")
        if next_btn:
            next_btn.click()
            page.wait_for_load_state("networkidle")
        else:
            break

    browser.close()

# Вывести все собранные книги и их URL
logger.info(f"Всего книг: {len(all_books)}")

# Сохранить результаты в файл csv
with open("books.csv", "w", newline="", encoding="utf-8") as csvfile:
    fieldnames = ["title", "url", "price", "in_stock", "rating"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for book in all_books:
        writer.writerow(book)


# Сохранить результаты в базу данных
try:
     with Session(engine) as db:
         counter = 0 # Счётчик сохранённых книг
         skipped = 0 # Счётчик пропущенных книг из-за дублей
         for book in all_books:
             exists = db.query(Book).filter_by(url=book['url']).first() # Проверяем, есть ли уже книга с таким URL в БД
             if not exists:
                 db.add(Book(**book)) # Если книги с таким URL нет, добавляем её в БД
                 counter += 1
             else:
                 skipped += 1
                 logger.warning(f"Уже в БД: {book['title']}")
         db.commit()
     logger.info(f"Сохранено в БД: {counter} книг | Пропущено дублей: {skipped}")
except Exception as e:
     logger.critical(f"Ошибка сохранения в БД: {e}")