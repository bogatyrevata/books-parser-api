from src.utils import parse_price, parse_rating, parse_in_stock
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from database import Book, Base

# Тесты для утилит парсинга данных о книгах
@pytest.mark.parametrize("raw, expected", [
    ("£12.99", 12.99),
    ("£0.00",  0.0),
    ("£100.00", 100.0),
])
class TestParsePrice:
    """Проверяем правильность парсинга цены."""
    def test_normal_price(self, raw, expected):
        assert parse_price(raw) == expected
 

class TestParseRating:
    """Проверяем конвертацию текстового рейтинга в число."""
 
    RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
 
    def test_one(self):
        assert parse_rating("star-rating One", self.RATING_MAP) == 1
 
    def test_three(self):
        assert parse_rating("star-rating Three", self.RATING_MAP) == 3
 
    def test_five(self):
        assert parse_rating("star-rating Five", self.RATING_MAP) == 5
 
    def test_unknown_returns_zero(self):
        # Если встретится незнакомое слово — возвращаем 0, не падаем
        assert parse_rating("star-rating Unknown", self.RATING_MAP) == 0
 
 
class TestParseInStock:
    """Проверяем определение наличия книги."""
 
    def test_in_stock_true(self):
        assert parse_in_stock("In stock") is True
 
    def test_in_stock_with_extra_text(self):
        assert parse_in_stock("  In stock  (22 available)") is True
 
    def test_not_in_stock(self):
        assert parse_in_stock("Out of stock") is False
 
    def test_empty_string(self):
        assert parse_in_stock("") is False


# Tесты базы данных (используем SQLite
# в памяти, чтобы не трогать реальный PostgreSQL)
 
@pytest.fixture
def db_session():
    """
    Фикстура — специальная функция pytest.
    Создаёт чистую тестовую БД перед каждым тестом
    и удаляет её после. Вместо PostgreSQL используем
    SQLite :memory: — она живёт только в оперативной памяти.
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)          # создаём таблицы
    with Session(engine) as session:
        yield session                         # отдаём сессию тесту
    Base.metadata.drop_all(engine)            # убираем за собой
 
 
def make_book(**kwargs) -> dict:
    """Фабрика тестовых данных — возвращает словарь книги."""
    defaults = {
        "title": "Test Book",
        "url": "http://books.example.com/test",
        "price": 9.99,
        "in_stock": True,
        "rating": 3,
    }
    defaults.update(kwargs)
    return defaults
 
 
class TestDatabaseSave:
    """Проверяем сохранение книг в базу данных."""
 
    def test_save_single_book(self, db_session):
        book_data = make_book()
        db_session.add(Book(**book_data))
        db_session.commit()
 
        result = db_session.query(Book).first()
        assert result is not None
        assert result.title == "Test Book"
        assert result.price == 9.99
 
    def test_save_multiple_books(self, db_session):
        books = [
            make_book(title="Book A", url="http://example.com/a"),
            make_book(title="Book B", url="http://example.com/b"),
            make_book(title="Book C", url="http://example.com/c"),
        ]
        for b in books:
            db_session.add(Book(**b))
        db_session.commit()
 
        count = db_session.query(Book).count()
        assert count == 3
 
    def test_duplicate_url_is_skipped(self, db_session):
        """Дубликат по URL не должен добавляться в БД."""
        book_data = make_book()
        db_session.add(Book(**book_data))
        db_session.commit()
 
        # Пытаемся добавить книгу с тем же URL
        exists = db_session.query(Book).filter_by(url=book_data['url']).first()
        if not exists:
            db_session.add(Book(**book_data))
            db_session.commit()
 
        count = db_session.query(Book).count()
        assert count == 1  # всё равно одна запись
 
    def test_book_fields_saved_correctly(self, db_session):
        book_data = make_book(
            title="Specific Title",
            price=42.0,
            in_stock=False,
            rating=5,
        )
        db_session.add(Book(**book_data))
        db_session.commit()
 
        saved = db_session.query(Book).first()
        assert saved.title    == "Specific Title"
        assert saved.price    == 42.0
        assert saved.in_stock is False
        assert saved.rating   == 5
 
    def test_out_of_stock_book_saved(self, db_session):
        book_data = make_book(in_stock=False)
        db_session.add(Book(**book_data))
        db_session.commit()
 
        saved = db_session.query(Book).first()
        assert saved.in_stock is False
 
# Tесты с mock-объектами Playwright
# (проверяем логику без реального браузера)
 
class TestPlaywrightMock:
    """
    Mock — это «подделка» реального объекта.
    Вместо настоящего браузера создаём объект,
    который ведёт себя как карточка книги на странице.
    """
 
    RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
 
    def _make_book_card(self, title, href, price_text, stock_text, rating_class):
        """Создаёт фейковую карточку книги (article.product_pod)."""
        card = MagicMock()
 
        title_el = MagicMock()
        title_el.get_attribute.return_value = title      # .get_attribute("title")
        title_el.get_attribute.side_effect = lambda attr: title if attr == "title" else href
 
        # h3 a — отдаёт и title и href в зависимости от аргумента
        h3_a = MagicMock()
        h3_a.get_attribute = lambda attr: title if attr == "title" else href
 
        price_el  = MagicMock(); price_el.inner_text.return_value  = price_text
        stock_el  = MagicMock(); stock_el.inner_text.return_value  = stock_text
        rating_el = MagicMock(); rating_el.get_attribute.return_value = rating_class
 
        def query_selector(selector):
            mapping = {
                "h3 a":                     h3_a,
                "p.price_color":            price_el,
                "p.instock.availability":   stock_el,
                "p.star-rating":            rating_el,
            }
            return mapping.get(selector, MagicMock())
 
        card.query_selector = query_selector
        return card
 
    def _extract_book_data(self, card, base_url):
        """Та же логика что в парсере, но вынесена в функцию."""
        from urllib.parse import urljoin
        title    = card.query_selector("h3 a").get_attribute("title")
        rel_url  = card.query_selector("h3 a").get_attribute("href")
        url      = urljoin(base_url, rel_url)
        price    = parse_price(card.query_selector("p.price_color").inner_text())
        in_stock = parse_in_stock(card.query_selector("p.instock.availability").inner_text())
        rating   = parse_rating(
            card.query_selector("p.star-rating").get_attribute("class"),
            self.RATING_MAP,
        )
        return {"title": title, "url": url, "price": price,
                "in_stock": in_stock, "rating": rating}
 
    def test_extract_title(self):
        card = self._make_book_card(
            title="A Light in the Attic", href="catalogue/book_1/index.html",
            price_text="£51.77", stock_text="In stock", rating_class="star-rating Three"
        )
        data = self._extract_book_data(card, "http://books.toscrape.com/catalogue/")
        assert data["title"] == "A Light in the Attic"
 
    def test_extract_price(self):
        card = self._make_book_card(
            title="Book", href="catalogue/book_2/index.html",
            price_text="£13.99", stock_text="In stock", rating_class="star-rating Two"
        )
        data = self._extract_book_data(card, "http://books.toscrape.com/catalogue/")
        assert data["price"] == 13.99
 
    def test_extract_rating(self):
        card = self._make_book_card(
            title="Book", href="catalogue/book_3/index.html",
            price_text="£9.00", stock_text="In stock", rating_class="star-rating Four"
        )
        data = self._extract_book_data(card, "http://books.toscrape.com/catalogue/")
        assert data["rating"] == 4
 
    def test_extract_out_of_stock(self):
        card = self._make_book_card(
            title="Book", href="catalogue/book_4/index.html",
            price_text="£5.00", stock_text="Out of stock", rating_class="star-rating One"
        )
        data = self._extract_book_data(card, "http://books.toscrape.com/catalogue/")
        assert data["in_stock"] is False
 
    def test_url_is_absolute(self):
        card = self._make_book_card(
            title="Book", href="catalogue/book_5/index.html",
            price_text="£5.00", stock_text="In stock", rating_class="star-rating One"
        )
        data = self._extract_book_data(card, "http://books.toscrape.com/catalogue/")
        assert data["url"].startswith("http://")
 