# 🚀 Bash скрипты для Books Parser API

Два скрипта для быстрого запуска проекта из одной команды.

---

## 📦 Вариант 1: Полный скрипт с опциями (рекомендуется)

**Файл:** `start_project.sh`

Этот скрипт содержит все команды которые вам нужны.

### Установка

Поместите скрипт в папку `books-parser-api`:

```bash
cp start_project.sh books-parser-api/
cd books-parser-api
chmod +x start_project.sh
```

### Использование

```bash
# Запустить контейнеры (по умолчанию)
./start_project.sh up

# Или просто (without аргумента)
./start_project.sh

# Остановить контейнеры
./start_project.sh down

# Перезапустить
./start_project.sh restart

# Показать логи API
./start_project.sh logs

# Статус контейнеров
./start_project.sh status

# Удалить всё включая БД (осторожнее!)
./start_project.sh clean
```

### Пример использования

```bash
# День 1 - первый запуск
./start_project.sh
# ✓ Docker работает
# ✓ Контейнеры запущены!
# 🖥️  Фронтенд: http://localhost:3000
# 📡 API: http://localhost:8000

# Когда закончили
./start_project.sh down

# День 2 - вернулись через время
./start_project.sh up

# Что-то сломалось
./start_project.sh restart

# Нужны логи
./start_project.sh logs
```

---

## 🔧 Сделать скрипт доступным из любой папки

Если хотите запускать скрипт из любого места (а не только из `books-parser-api`):

### На Mac/Linux

**Вариант A:** Добавить в `~/.zshrc` или `~/.bash_profile`:

```bash
alias start-parser="cd ~/path/to/books-parser-api && ./start_project.sh"
```

Потом просто:
```bash
start-parser        # запуск
start-parser down   # остановка
start-parser logs   # логи
```

**Вариант B:** Скопировать в `/usr/local/bin/`:

```bash
sudo cp start_project.sh /usr/local/bin/start-parser
sudo chmod +x /usr/local/bin/start-parser

# Теперь можно использовать откуда угодно
start-parser
start-parser down
```

---

## 💡 Ещё проще - одна строка

Если совсем лень, добавьте в `~/.zshrc`:

```bash
alias books="cd ~/path/to/books-parser-api && docker compose"
```

Потом:
```bash
books up -d        # запуск
books down         # остановка
books logs api     # логи
books ps           # статус
```

---

## 🐞 Если скрипт не запускается

```bash
# Дайте права на выполнение
chmod +x start_project.sh

# И запустите
./start_project.sh
```

Если ошибка `command not found: docker`:
- Убедитесь что Docker Desktop установлен
- Если на Mac - может нужно перезагрузиться после установки

---
