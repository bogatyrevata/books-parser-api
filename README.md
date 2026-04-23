## О проекте

### Запуск проекта

1. Создаём виртуальное огружение:
```bash
   python3 -m venv .venv
```

   Активируем:
```bash
   source .venv/bin/activate
```
   Деактивирует:
```bash
   deactivate
```

2. Установка зависимостей:
```bash
   pip install -r requirements.txt
```
   Проверяем:
```bash
   pip list
```

3. Установка Playwright:
```bash
python -m playwright install chromium
```

4. Настройка базы данных.
   Создаем базу данны, суперпользователя, устанавливаем пароль, выдаем пользователю все права от базы данных. 
   Добавь настройки в `.env`
```bash
DB_HOST=localhost
DB_PORT=5433
DB_NAME=имя_твоей_базы
DB_USER=имя_пользователя
DB_PASSWORD=пароль
```

5. Миграции (Alembic).
```bash
alembic init migrations
```
   
   Настройка в `migrations/env.py` 
   Добавь:
```bash
# Добавляем эти три импорта
from dotenv import load_dotenv
import os
from database import Base

load_dotenv()

# Подставляем URL из .env
config = context.config

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
config.set_main_option('sqlalchemy.url', DB_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)
    
# Было None — меняем на Base.metadata
target_metadata = Base.metadata #тут указана модель Base что мы написали сами, из нее берутся данные
```

6. Создание и применение миграций
   Первая миграция, к этому моменту должна быть уже добавлеа модель в database.py
```bash
alembic revision --autogenerate -m "create books table"
```

   Применемени:
```bash
alembic upgrade head
```

7. Обновление схемы БД
   При изменении моделей:
```bash
alembic revision --autogenerate -m "add category column"
alembic upgrade head
```

8. Запускаем приложение:
```bash
   python -m parser.main
```

   Запускаем тесты:
```bash
   pytest tests/ -v
```

   Покрытие тестами:
```bash
   pytest tests/ --cov=src --cov-report=term-missing
```

9. Запуск API
```bash
   uvicorn api.api:app --reload
```
   Запуск тестов API
```bash
   pytest tests/test_api.py -v
```

10. Frontend 
   Запуск в отдельном терминале
```bash
   cd ./Documents/GitHub/books_frontend
   npm run dev
```