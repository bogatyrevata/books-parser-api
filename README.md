# 📚 Books Parser API

Проект состоит из **парсера книг** (Playwright), **REST API** (FastAPI) и **React фронтенда**.

---

## 📋 Инструкция для ручной разработки (без Docker)

Выполните эти шаги, если хотите работать локально (на Mac нужно установить PostgreSQL отдельно).

### 1. Создание виртуального окружения

```bash
python3 -m venv .venv
source .venv/bin/activate  # на Windows: .venv\Scripts\activate
```

Деактивация (когда закончили работу):
```bash
deactivate
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
pip list  # проверка
```

### 3. Установка Playwright

```bash
python -m playwright install chromium
```

### 4. Настройка базы данных

Создайте PostgreSQL базу (если запускаете локально):

```bash
createdb parser_books
createuser parser_user
# или через psql:
# CREATE DATABASE parser_books;
# CREATE USER parser_user WITH PASSWORD 'пароль';
# GRANT ALL PRIVILEGES ON DATABASE parser_books TO parser_user;
```

Создайте файл `.env`:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=parser_books
DB_USER=parser_user
DB_PASSWORD=пароль
SECRET_KEY=your_secret_key_here
LIMIT_BOOKS=5
CATEGORY_URL=http://books.toscrape.com/catalogue/category/books_1/index.html
```

### 5. Миграции (Alembic)

```bash
alembic init migrations
```

Отредактируйте `migrations/env.py` — добавьте в начало:

```python
from dotenv import load_dotenv
import os
from database import Base

load_dotenv()

# Подставляем URL из .env
config = context.config

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
config.set_main_option('sqlalchemy.url', DB_URL)

# Замените None на:
target_metadata = Base.metadata
```

### 6. Создание и применение миграций

```bash
# Первая миграция (модель уже должна быть в database.py)
alembic revision --autogenerate -m "create books table"

# Применение миграций
alembic upgrade head
```

### 7. Обновление схемы БД при изменении моделей

```bash
alembic revision --autogenerate -m "add category column"
alembic upgrade head
```

### 8. Запуск парсера и тестов

```bash
# Запуск парсера
python -m parser.main

# Запуск тестов
pytest tests/ -v

# Покрытие тестами
pytest tests/ --cov=src --cov-report=term-missing
```

### 9. Запуск API

```bash
uvicorn api.api:app --reload
```

Протестировать API:
```bash
pytest tests/test_api.py -v
```

Открыть в браузере: http://localhost:8000/docs

### 10. Запуск Frontend

В отдельном терминале:

```bash
cd ../books-frontend
npm install
npm run dev
```

---

## 🐳 Структура проекта

```
books-parser-api/              # бэкенд репозиторий
├── api/                       # FastAPI роуты
├── parser/                    # Playwright парсер
├── tests/                     # тесты
├── migrations/                # миграции Alembic
├── Dockerfile.api             # образ для API
├── Dockerfile.parser          # образ для парсера
├── docker-compose.yml         # конфиг для запуска контейнеров
├── requirements.txt           # зависимости Python
├── .env                       # переменные окружения (НЕ в git!)
└── README.md

books-frontend/                # фронтенд репозиторий
├── src/
├── Dockerfile
└── package.json
```

---

## 🚀 Запуск с Docker (рекомендуется)

### ✅ Требования

- Docker Desktop установлен и запущен
- Папки `books-parser-api` и `books-frontend` лежат в одной директории

### 📝 Шаг 1: Создайте `.env` файл

В папке `books-parser-api` создайте файл `.env`:

```env
DB_USER=parser_user
DB_PASSWORD=secure_password_here
DB_HOST=db
DB_PORT=5432
DB_NAME=parser_books
SECRET_KEY=your_secret_key_here_make_it_long_and_random
LIMIT_BOOKS=5
CATEGORY_URL=http://books.toscrape.com/catalogue/category/books_1/index.html
```

---

## 🎯 Запуск (первый раз)

Если контейнеры запускаются **в первый раз**:

```bash
cd books-parser-api

# Запустить всё (API, база данных, фронтенд)
docker compose up -d

# Проверить, всё ли запустилось
docker compose ps
```

**Ожидаемый результат:**
```
NAME              STATUS
books-db          Up (healthy)
books-api         Up
books-frontend    Up
```

**Откройте в браузере:**
- 🖥️ Фронтенд: http://localhost:3000
- 📡 API: http://localhost:8000
- 📖 API docs: http://localhost:8000/docs

---

## 🔄 Последующие запуски (контейнеры уже созданы)

Если вернулись через время и контейнеры уже существуют:

```bash
cd books-parser-api

# Просто запустить контейнеры
docker compose up -d

# Проверить статус
docker compose ps
```

Если контейнеры были остановлены (`docker compose down`), используйте ту же команду.

---

## 📊 Проверить статус системы

```bash
# Посмотреть какие контейнеры запущены
docker compose ps

# Посмотреть логи API в реальном времени
docker compose logs -f api

# Посмотреть логи базы данных
docker compose logs -f db

# Проверить, доступен ли API
curl http://localhost:8000/docs
```

---

## 🧹 Остановка и очистка

```bash
# Остановить все контейнеры (но данные БД сохранятся)
docker compose down

# Остановить и удалить ВСЕ данные (включая БД!)
docker compose down -v
```

⚠️ **Важно:** `docker compose down -v` удалит все данные в БД!

---

## 🎮 Запуск парсера

Парсер запускается отдельно по требованию:

```bash
# Запустить парсер один раз
docker compose --profile parser run --rm parser

# Запустить парсер и оставить контейнер
docker compose --profile parser run parser
```

---

## 🛠️ Полезные команды

### Контейнеры

```bash
docker compose ps              # статус всех сервисов
docker compose up -d           # запустить в фоне
docker compose down            # остановить всё
docker compose down -v         # остановить и удалить данные
```

### Логи и отладка

```bash
docker compose logs api        # логи API
docker compose logs db         # логи БД
docker compose logs -f api     # логи в реальном времени
docker exec -it books-api bash # зайти внутрь контейнера API
docker exec -it books-db psql -U parser_user -d parser_books  # зайти в БД
```

### Запуск команд внутри контейнера

```bash
# Запустить тесты
docker exec -it books-api pytest tests/ -v

# Посмотреть файлы в контейнере
docker exec -it books-api ls -la

# Применить миграции
docker exec -it books-api alembic upgrade head
```

---

## ❌ Если что-то не работает

### Ошибка: `port 8000 is already allocated`

```bash
# Убить процесс на порту 8000
lsof -i :8000
kill -9 <PID>

# Или остановить контейнеры
docker compose down
```

### Ошибка подключения к БД

```bash
# Проверить логи БД
docker compose logs db

# Пересоздать БД
docker compose down -v
docker compose up -d
```

### Docker daemon не запущен (Mac)

Откройте **Docker Desktop** приложение.

---

## 📚 Где что находится

| Что? | Где? | Порт |
|------|------|------|
| Фронтенд (React) | http://localhost:3000 | 3000 |
| API (FastAPI) | http://localhost:8000 | 8000 |
| Swagger docs | http://localhost:8000/docs | 8000 |
| База данных (PostgreSQL) | localhost:5432 | 5432 |


## Локальная разработка 

# ТЕРМИНАЛ 1 — БД (один раз, оставляете работать)
cd books-parser-api
docker compose up -d db

docker ps # должна быть books-db

# ТЕРМИНАЛ 2 — API (локально)
cd books-parser-api
source .venv/bin/activate
uvicorn api.api:app --reload

# ТЕРМИНАЛ 3 — Парсер (если нужно парсить)
cd books-parser-api
source .venv/bin/activate
python -m parser.main

# ТЕРМИНАЛ 4 — Фронтенд (локально)
cd books-frontend
npm run dev

# БРАУЗЕР:
# http://localhost:5173 — приложение
# http://localhost:8000/docs — API