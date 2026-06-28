#!/bin/bash

# 📚 Books Parser API - Скрипт для быстрого запуска проекта
# Использование: ./start_project.sh [команда]
# Команды: up (по умолчанию), down, logs, status, restart

# Получаем директорию где лежит этот скрипт
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Переходим в папку с docker-compose.yml (предполагаем что скрипт в books-parser-api)
BACKEND_DIR="$SCRIPT_DIR"

# Если скрипт лежит выше, ищем папку books-parser-api
if [ ! -f "$BACKEND_DIR/docker-compose.yml" ]; then
    BACKEND_DIR="$SCRIPT_DIR/books-parser-api"
fi

# Команда (по умолчанию "up")
COMMAND="${1:-up}"

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}➜${NC} $1"
}

# Проверка что Docker запущен
check_docker() {
    if ! docker ps > /dev/null 2>&1; then
        print_error "Docker не запущен!"
        print_info "Пожалуйста, запустите Docker Desktop"
        exit 1
    fi
    print_status "Docker работает"
}

# Проверка что docker-compose.yml существует
check_compose_file() {
    if [ ! -f "$BACKEND_DIR/docker-compose.yml" ]; then
        print_error "docker-compose.yml не найден в $BACKEND_DIR"
        exit 1
    fi
}

# Основная функция
main() {
    echo ""
    print_info "📚 Books Parser API"
    echo ""

    check_docker
    check_compose_file

    cd "$BACKEND_DIR"
    print_info "Рабочая директория: $BACKEND_DIR"
    echo ""

    case "$COMMAND" in
        up)
            print_info "Запуск контейнеров..."
            docker compose up -d
            echo ""
            print_status "Контейнеры запущены!"
            echo ""
            print_info "Откройте в браузере:"
            echo "   🖥️  Фронтенд: http://localhost:3000"
            echo "   📡 API: http://localhost:8000"
            echo "   📖 API docs: http://localhost:8000/docs"
            echo ""
            docker compose ps
            ;;

        down)
            print_info "Остановка контейнеров..."
            docker compose down
            echo ""
            print_status "Контейнеры остановлены"
            ;;

        restart)
            print_info "Перезапуск контейнеров..."
            docker compose down
            docker compose up -d
            echo ""
            print_status "Контейнеры перезапущены!"
            echo ""
            docker compose ps
            ;;

        logs)
            print_info "Логи API (Ctrl+C для выхода)..."
            docker compose logs -f api
            ;;

        status|ps)
            print_info "Статус контейнеров:"
            echo ""
            docker compose ps
            ;;

        clean)
            print_error "ВНИМАНИЕ! Это удалит все данные в БД"
            read -p "Вы уверены? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                print_info "Удаление контейнеров и данных..."
                docker compose down -v
                print_status "Очистка завершена"
            else
                print_info "Отменено"
            fi
            ;;

        *)
            echo "Неизвестная команда: $COMMAND"
            echo ""
            echo "Использование: $0 [команда]"
            echo ""
            echo "Доступные команды:"
            echo "  up         - Запустить контейнеры (по умолчанию)"
            echo "  down       - Остановить контейнеры"
            echo "  restart    - Перезапустить контейнеры"
            echo "  logs       - Показать логи API"
            echo "  status/ps  - Показать статус контейнеров"
            echo "  clean      - Удалить контейнеры и данные БД"
            echo ""
            exit 1
            ;;
    esac

    echo ""
}

main
