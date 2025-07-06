# -*- coding: utf-8 -*-
"""
Главный файл для запуска телеграм-бота для отслеживания предметов.
"""
import telebot
import logging
import threading
from dotenv import load_dotenv

# Загружаем переменные из .env файла в корне проекта
load_dotenv()

from config import config
from item_tracker_bot.handlers import register_handlers
from item_tracker_bot.updater import periodic_updater

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def run():
    """
    Основная функция для инициализации и запуска бота.
    """
    if not config.validate_config():
        return

    # Убедимся, что токен - это строка, чтобы избежать ошибок
    if not isinstance(config.BOT_TOKEN, str):
        logging.error("Токен бота не является строкой. Проверьте .env файл.")
        return

    bot = telebot.TeleBot(config.BOT_TOKEN, parse_mode="HTML")
    logging.info("Бот для отслеживания предметов инициализирован.")

    register_handlers(bot)
    logging.info("Обработчики для трекера зарегистрированы.")

    update_thread = threading.Thread(
        target=periodic_updater, 
        args=(bot, config.NOTIFICATION_INTERVAL_HOURS), 
        daemon=True
    )
    update_thread.start()

    logging.info("Запуск бота для отслеживания предметов...")
    bot.polling(none_stop=True)

if __name__ == "__main__":
    run() 