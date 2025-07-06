# -*- coding: utf-8 -*-
"""
Модуль для периодического обновления данных о предметах и отправки отчетов.
"""
import time
import logging
import telebot

from db.connector import CSMarketDatabase
from db.models import Item
from parser.parser import CSMarketParser
from config import config

# Инициализируем коннектор к базе данных
db = CSMarketDatabase(db_path=config.DATABASE_PATH)

def _generate_report() -> str:
    """
    Генерирует текстовый отчет на основе текущих данных из БД.
    """
    items_data = db.get_all_items()
    if not items_data:
        return ""

    total_purchase_price = 0
    total_current_price = 0
    report_parts = ["<b>📊 Сводка по прибыли:</b>\n"]

    for item_data in items_data:
        item = Item.from_dict(item_data)
        purchase_price = item.purchase_price or 0
        current_price = item.current_price or 0
        total_purchase_price += purchase_price
        total_current_price += current_price
        absolute_profit, percent_profit = item.calculate_profit()
        sign = "🟢" if absolute_profit >= 0 else "🔴"
        
        report_parts.append(
            f"\n<b>{item.title}</b>: {sign} ${absolute_profit:.2f} ({percent_profit:.2f}%)"
        )
    
    total_profit = total_current_price - total_purchase_price
    total_profit_percent = (total_profit / total_purchase_price * 100) if total_purchase_price > 0 else 0
    total_sign = "🟢" if total_profit >= 0 else "🔴"

    summary = (
        f"\n\n<b>📈 Общая прибыль: {total_sign} ${total_profit:.2f} ({total_profit_percent:.2f}%)</b>"
    )
    report_parts.append(summary)
    
    return "\n".join(report_parts)


def periodic_updater(bot: telebot.TeleBot, interval_hours: int):
    """
    Основная функция для фонового потока.
    Обновляет данные и отправляет отчет.
    
    Args:
        bot (telebot.TeleBot): Экземпляр бота.
        interval_hours (int): Интервал между обновлениями в часах.
    """
    logging.info("🚀 Фоновый обработчик запущен.")
    while True:
        try:
            logging.info("Начинаю цикл обновления цен...")
            items_to_update = db.get_all_items()

            if not items_to_update:
                logging.info("Нет предметов для обновления. Следующая проверка через 4 часа.")
            else:
                with CSMarketParser() as parser:
                    for item_data in items_to_update:
                        try:
                            logging.info(f"Обновляю {item_data['title']}...")
                            parsed_data = parser.parse_item_page(item_data['url'])
                            if parsed_data and parsed_data.get('title'):
                                db.upsert_item(parsed_data)
                                time.sleep(5) # Небольшая задержка между запросами
                            else:
                                logging.warning(f"Не удалось получить данные для {item_data['url']}")
                        except Exception as e:
                            logging.error(f"Ошибка при обновлении предмета {item_data.get('title')}: {e}")
                
                logging.info("Обновление цен завершено. Генерирую отчет...")
                report = _generate_report()
                if report and config.ADMIN_ID:
                    bot.send_message(
                        config.ADMIN_ID,
                        report,
                        disable_notification=True
                    )
                    logging.info("Отчет отправлен.")

        except Exception as e:
            logging.error(f"Критическая ошибка в фоновом обработчике: {e}")

        # Пауза
        logging.info(f"Следующее обновление через {interval_hours} час(а/ов).")
        time.sleep(interval_hours * 60 * 60) 