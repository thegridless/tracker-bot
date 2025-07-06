#!/bin/bash

# Скрипт для управления CS:GO Market Tracker Bot через Screen
# Использование: ./bot_manager.sh [start|stop|status|connect|logs]

# Настройки
BOT_NAME="cs-market-tracker-bot"
BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$BOT_DIR/.venv"
PYTHON_SCRIPT="$BOT_DIR/main.py"
LOG_FILE="$BOT_DIR/logs/bot.log"

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Проверка установки screen
check_screen() {
    if ! command -v screen &> /dev/null; then
        print_error "Screen не установлен!"
        echo "Установите screen командой:"
        echo "  macOS: brew install screen"
        echo "  Ubuntu: sudo apt install screen"
        echo "  CentOS: sudo yum install screen"
        exit 1
    fi
}

# Проверка зависимостей
check_dependencies() {
    if [[ ! -d "$VENV_PATH" ]]; then
        print_error "Виртуальное окружение не найдено: $VENV_PATH"
        print_info "Создайте виртуальное окружение командой:"
        print_info "python -m venv .venv"
        exit 1
    fi
    
    if [[ ! -f "$PYTHON_SCRIPT" ]]; then
        print_error "Скрипт бота не найден: $PYTHON_SCRIPT"
        exit 1
    fi
    
    if [[ ! -f "$BOT_DIR/.env" ]]; then
        print_warning ".env файл не найден в $BOT_DIR"
        print_info "Запустите настройку: python setup_bot.py setup"
    fi
    
    # Проверяем наличие токена бота
    if [[ -f "$BOT_DIR/.env" ]]; then
        if ! grep -q "BOT_TOKEN=" "$BOT_DIR/.env"; then
            print_warning "Токен бота не найден в .env файле"
        fi
    fi
    
    # Создаем директорию для логов
    mkdir -p "$BOT_DIR/logs"
}

# Проверка статуса бота
check_bot_status() {
    if screen -ls | grep -q "$BOT_NAME"; then
        return 0  # Бот запущен
    else
        return 1  # Бот не запущен
    fi
}

# Запуск бота
start_bot() {
    print_info "Запуск CS:GO Market Tracker Bot..."
    
    if check_bot_status; then
        print_warning "Бот уже запущен!"
        return 0
    fi
    
    # Создаем screen сессию и запускаем бота
    screen -dmS "$BOT_NAME" bash -c "
        cd '$BOT_DIR' && 
        source '$VENV_PATH/bin/activate' && 
        python '$PYTHON_SCRIPT' 2>&1 | tee -a '$LOG_FILE'
    "
    
    sleep 3
    
    if check_bot_status; then
        print_success "Бот успешно запущен!"
        print_info "Для подключения к сессии: ./bot_manager.sh connect"
        print_info "Для просмотра логов: ./bot_manager.sh logs"
        print_info "Для остановки: ./bot_manager.sh stop"
        
        # Показываем последние строки лога
        if [[ -f "$LOG_FILE" ]]; then
            echo ""
            echo "Последние записи в логе:"
            tail -n 5 "$LOG_FILE"
        fi
    else
        print_error "Не удалось запустить бота"
        print_info "Проверьте логи: ./bot_manager.sh logs"
        exit 1
    fi
}

# Остановка бота
stop_bot() {
    print_info "Остановка CS:GO Market Tracker Bot..."
    
    if ! check_bot_status; then
        print_warning "Бот не запущен"
        return 0
    fi
    
    # Завершаем screen сессию
    screen -S "$BOT_NAME" -X quit
    
    sleep 2
    
    if ! check_bot_status; then
        print_success "Бот успешно остановлен"
    else
        print_error "Не удалось остановить бота"
        print_info "Попробуйте принудительно: screen -S $BOT_NAME -X kill"
        exit 1
    fi
}

# Статус бота
show_status() {
    echo "🤖 === CS:GO Market Tracker Bot Status ==="
    echo ""
    
    if check_bot_status; then
        print_success "Бот запущен"
        echo ""
        echo "Активные screen сессии:"
        screen -ls | grep "$BOT_NAME" || echo "Нет активных сессий"
        
        # Показываем информацию о процессе
        if command -v ps &> /dev/null; then
            echo ""
            echo "Процессы бота:"
            ps aux | grep -E "(python.*main\.py|$BOT_NAME)" | grep -v grep || echo "Процессы не найдены"
        fi
        
        # Показываем размер лог файла
        if [[ -f "$LOG_FILE" ]]; then
            log_size=$(du -h "$LOG_FILE" | cut -f1)
            echo ""
            echo "Размер лог файла: $log_size"
        fi
    else
        print_warning "Бот не запущен"
    fi
    
    echo ""
    echo "Все screen сессии:"
    screen -ls || echo "Нет активных screen сессий"
    
    # Проверяем конфигурацию
    echo ""
    echo "Конфигурация:"
    if [[ -f "$BOT_DIR/.env" ]]; then
        print_success ".env файл найден"
        if grep -q "BOT_TOKEN=" "$BOT_DIR/.env"; then
            print_success "Токен бота настроен"
        else
            print_warning "Токен бота не найден"
        fi
        if grep -q "ADMIN_ID=" "$BOT_DIR/.env"; then
            admin_id=$(grep "ADMIN_ID=" "$BOT_DIR/.env" | cut -d'=' -f2)
            print_success "ID администратора: $admin_id"
        else
            print_warning "ID администратора не настроен"
        fi
    else
        print_error ".env файл не найден"
    fi
}

# Подключение к сессии
connect_to_bot() {
    if ! check_bot_status; then
        print_error "Бот не запущен"
        print_info "Запустите бота: ./bot_manager.sh start"
        exit 1
    fi
    
    print_info "Подключение к сессии бота..."
    print_info "Для отключения нажмите Ctrl+A, затем D"
    print_info "Для остановки бота нажмите Ctrl+C в сессии"
    sleep 2
    
    # Подключаемся к сессии
    screen -r "$BOT_NAME"
}

# Просмотр логов
show_logs() {
    if [[ -f "$LOG_FILE" ]]; then
        print_info "Показываю логи (Ctrl+C для выхода):"
        echo "Файл: $LOG_FILE"
        echo "=" * 60
        tail -f "$LOG_FILE"
    else
        print_warning "Файл логов не найден: $LOG_FILE"
        print_info "Запустите бота для создания логов"
    fi
}

# Просмотр последних логов
show_recent_logs() {
    if [[ -f "$LOG_FILE" ]]; then
        print_info "Последние 20 записей в логе:"
        echo "Файл: $LOG_FILE"
        echo "=" * 60
        tail -n 20 "$LOG_FILE"
    else
        print_warning "Файл логов не найден: $LOG_FILE"
    fi
}

# Перезапуск бота
restart_bot() {
    print_info "Перезапуск CS:GO Market Tracker Bot..."
    stop_bot
    sleep 3
    start_bot
}

# Очистка логов
clear_logs() {
    if [[ -f "$LOG_FILE" ]]; then
        echo -n "Вы уверены, что хотите очистить логи? (y/N): "
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            > "$LOG_FILE"
            print_success "Логи очищены"
        else
            print_info "Отменено"
        fi
    else
        print_warning "Файл логов не найден"
    fi
}

# Проверка обновлений
check_updates() {
    print_info "Проверка обновлений зависимостей..."
    
    if [[ -f "$BOT_DIR/requirements.txt" ]]; then
        source "$VENV_PATH/bin/activate"
        pip list --outdated
    else
        print_warning "requirements.txt не найден"
    fi
}

# Справка
show_help() {
    echo "🤖 CS:GO Market Tracker Bot Manager"
    echo ""
    echo "Использование: $0 [команда]"
    echo ""
    echo "Команды управления:"
    echo "  start       - Запустить бота"
    echo "  stop        - Остановить бота"
    echo "  restart     - Перезапустить бота"
    echo "  status      - Показать статус"
    echo ""
    echo "Команды мониторинга:"
    echo "  connect     - Подключиться к сессии"
    echo "  logs        - Показать логи в реальном времени"
    echo "  recent      - Показать последние логи"
    echo ""
    echo "Дополнительные команды:"
    echo "  clear-logs  - Очистить логи"
    echo "  updates     - Проверить обновления"
    echo "  help        - Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $0 start      # Запустить бота"
    echo "  $0 status     # Проверить статус"
    echo "  $0 connect    # Подключиться к сессии"
    echo "  $0 logs       # Смотреть логи"
    echo ""
    echo "Файлы проекта:"
    echo "  Основной скрипт: $PYTHON_SCRIPT"
    echo "  Логи: $LOG_FILE"
    echo "  Конфигурация: $BOT_DIR/.env"
}

# Основная функция
main() {
    check_screen
    check_dependencies
    
    case "${1:-help}" in
        start)
            start_bot
            ;;
        stop)
            stop_bot
            ;;
        restart)
            restart_bot
            ;;
        status)
            show_status
            ;;
        connect)
            connect_to_bot
            ;;
        logs)
            show_logs
            ;;
        recent)
            show_recent_logs
            ;;
        clear-logs)
            clear_logs
            ;;
        updates)
            check_updates
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Неизвестная команда: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Запуск
main "$@" 