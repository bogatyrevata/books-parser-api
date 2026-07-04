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

config = context.config

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
config.set_main_option('sqlalchemy.url', DB_URL)

target_metadata = Base.metadata
```

### 6. Создание и применение миграций

```bash
alembic revision --autogenerate -m "create books table"
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

Открыть в браузере: http://localhost:8000/docs

### 10. Запуск Frontend

В отдельном терминале:

```bash
cd ../books-frontend
npm install
npm run dev
```

Фронтенд доступен на http://localhost:5173 — vite автоматически проксирует `/api/*` на `localhost:8000`.

---

## 🐳 Структура проекта

```
books-parser-api/              # бэкенд репозиторий
├── api/                       # FastAPI роуты
├── parser/                    # Playwright парсер
├── tests/                     # тесты
├── migrations/                # миграции Alembic
├── Dockerfile.api             # образ для API (включает Playwright + Chromium)
├── Dockerfile.parser          # образ для парсера
├── docker-compose.yml         # базовый конфиг (прод — порты закрыты)
├── docker-compose.override.yml  # локальная разработка (порты открыты, авто)
├── requirements.txt           # зависимости Python
├── .env                       # переменные окружения (НЕ в git!)
└── README.md

books-frontend/                # фронтенд репозиторий
├── src/
├── nginx.conf                 # конфиг nginx внутри контейнера
├── Dockerfile
└── package.json

nginx-proxy/                   # отдельный nginx-контейнер — точка входа для всех проектов
├── conf.d/
│   └── books.conf             # virtual host для books.bogatyrevata.com
├── nginx.conf                 # главный конфиг
├── Dockerfile
└── docker-compose.yml
```

---

## 🚀 Запуск с Docker (локально)

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

### 🎯 Запуск (первый раз)

```bash
cd books-parser-api

# Запустить все контейнеры
docker compose up -d

# Применить миграции
docker compose exec api alembic upgrade head

# Проверить статус
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
- 📖 API docs: http://localhost:8000/docs

> Порты 3000 и 8000 открыты только локально через `docker-compose.override.yml`,
> который Docker Compose подхватывает автоматически. На проде эти порты закрыты.

---

## 🌐 Запуск на сервере (прод)

На сервере контейнеры запускаются в два шага — сначала проект, потом nginx-proxy.

### Шаг 1: Запустить парсер книг

```bash
cd books-parser-api

# Запустить без override (порты наружу не торчат)
docker compose up -d

# Применить миграции
docker compose exec api alembic upgrade head
```

### Шаг 2: Запустить nginx-proxy

nginx-proxy — отдельный контейнер, который стоит перед всеми проектами.
Он должен запускаться после того как books-parser-api уже поднят (чтобы сеть существовала).

```bash
cd nginx-proxy
docker compose up -d
```

**Откройте в браузере:**
- 🖥️ Фронтенд: https://books.bogatyrevata.com
- 📖 API docs: https://books.bogatyrevata.com/api/docs

---

## 🔄 Последующие запуски

```bash
cd books-parser-api
docker compose up -d

cd ../nginx-proxy
docker compose up -d
```

---

## 📊 Проверить статус системы

```bash
# Статус контейнеров парсера
docker compose ps

# Логи API в реальном времени
docker compose logs -f api

# Логи базы данных
docker compose logs -f db
```

---

## 🧹 Остановка и очистка

```bash
# Остановить все контейнеры (данные БД сохранятся)
docker compose down

# Остановить и удалить ВСЕ данные (включая БД!)
docker compose down -v
```

⚠️ **Важно:** `docker compose down -v` удалит все данные в БД!

---

## 🎮 Запуск парсера

Парсинг категорий и книг доступен через кнопки в UI (только для администратора).

Также можно запустить парсер вручную через терминал:

```bash
docker compose --profile parser run --rm parser
```

---

## 🛠️ Полезные команды

### Контейнеры

```bash
docker compose ps                        # статус всех сервисов
docker compose up -d                     # запустить в фоне
docker compose up -d --build             # пересобрать образы и запустить
docker compose up -d --build api         # пересобрать только api
docker compose down                      # остановить всё
docker compose down -v                   # остановить и удалить данные
```

### Логи и отладка

```bash
docker compose logs api                  # логи API
docker compose logs db                   # логи БД
docker compose logs -f api               # логи в реальном времени
docker exec -it books-api bash           # зайти внутрь контейнера API
docker exec -it books-db psql -U parser_user -d parser_books  # зайти в БД
```

### Миграции

```bash
# Применить все миграции
docker compose exec api alembic upgrade head

# Создать новую миграцию после изменения моделей
docker compose exec api alembic revision --autogenerate -m "описание"
```

---

## ❌ Если что-то не работает

### 500 ошибка на парсинге

Проверьте логи api:
```bash
docker compose logs api --tail=50
```

### Ошибка подключения к БД / колонка не существует

Скорее всего не применены миграции:
```bash
docker compose exec api alembic upgrade head
```

Если ошибка `DuplicateTable` — пересоздайте базу (только для локалки!):
```bash
docker compose down -v
docker compose up -d
docker compose exec api alembic upgrade head
```

### Фронтенд не видит API

Проверьте что контейнеры в одной сети:
```bash
docker network ls | grep books
docker compose ps
```

### Docker daemon не запущен (Mac)

Откройте **Docker Desktop** приложение.

---

## 📚 Где что находится

### Локально (docker-compose.override.yml)

| Что? | Где? | Порт |
|------|------|------|
| Фронтенд (React) | http://localhost:3000 | 3000 |
| API (FastAPI) | http://localhost:8000 | 8000 |
| Swagger docs | http://localhost:8000/docs | 8000 |
| База данных (PostgreSQL) | localhost:5434 | 5434 |

### На сервере (прод)

| Что? | Где? |
|------|------|
| Фронтенд (React) | https://books.bogatyrevata.com |
| API | https://books.bogatyrevata.com/api/ |
| Swagger docs | https://books.bogatyrevata.com/api/docs |

---

## 💻 Локальная разработка (без Docker)

```bash
# ТЕРМИНАЛ 1 — БД (один раз, оставляете работать)
cd books-parser-api
docker compose up -d db

# ТЕРМИНАЛ 2 — API (локально)
cd books-parser-api
source .venv/bin/activate
uvicorn api.api:app --reload

# ТЕРМИНАЛ 3 — Парсер (если нужно парсить вручную)
cd books-parser-api
source .venv/bin/activate
python -m parser.main

# ТЕРМИНАЛ 4 — Фронтенд (локально)
cd books-frontend
npm run dev

# БРАУЗЕР:
# http://localhost:5173 — приложение (vite проксирует /api/* на localhost:8000)
# http://localhost:8000/docs — API docs
```