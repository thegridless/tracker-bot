# -*- coding: utf-8 -*-
"""
Главный скрипт для запуска телеграм-бота для отслеживания предметов.
"""
from dotenv import load_dotenv

def main():
    """
    Инициализирует и запускает бота.
    """
    # Загружаем переменные из .env файла в корне проекта
    load_dotenv()

    # Импортируем и запускаем бота
    from item_tracker_bot import bot
    bot.run()

if __name__ == "__main__":
    main()
