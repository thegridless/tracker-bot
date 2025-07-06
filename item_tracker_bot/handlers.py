# -*- coding: utf-8 -*-
"""
Модуль для обработки команд и сообщений от пользователя.
"""
from functools import wraps
import telebot
from telebot.types import Message

# Импортируем бизнес-логику
from db.connector import CSMarketDatabase
from db.models import Item
from parser.parser import CSMarketParser

# Импортируем клавиатуру, константы и общую конфигурацию
from item_tracker_bot.keyboards import main_menu_keyboard, cancel_keyboard, numeric_keyboard, confirm_delete_keyboard
from item_tracker_bot.constants import MainMenuCommands, ActionCommands
from config import config

# Инициализируем коннектор к базе данных
# Путь к БД берется из общего конфига
db = CSMarketDatabase(db_path=config.DATABASE_PATH)


def access_checker(func):
    """
    Декоратор для проверки доступа к боту.
    Разрешает доступ только администратору, указанному в config.py.
    """
    @wraps(func)
    def wrapper(message: Message, *args, **kwargs):
        if not message.from_user or not config.is_admin(message.from_user.id):
            # Если ID пользователя не совпадает, ничего не делаем
            return
        
        # Если проверка пройдена, вызываем основную функцию
        return func(message, *args, **kwargs)
    return wrapper


def register_handlers(bot: telebot.TeleBot):
    """
    Регистрирует все обработчики команд для бота.
    
    Args:
        bot (telebot.TeleBot): Экземпляр бота.
    """
    # Оборачиваем вызовы в lambda, чтобы передать экземпляр `bot`
    bot.register_message_handler(
        lambda message: cancel_handler(message, bot),
        func=lambda message: message.text == ActionCommands.CANCEL
    )
    bot.register_message_handler(
        lambda message: start_handler(message, bot), 
        commands=['start', 'help']
    )
    bot.register_message_handler(
        lambda message: add_item_start(message, bot), 
        func=lambda message: message.text == MainMenuCommands.ADD_ITEM
    )
    bot.register_message_handler(
        lambda message: delete_item_start(message, bot),
        func=lambda message: message.text == MainMenuCommands.REMOVE_ITEM
    )
    bot.register_message_handler(
        lambda message: show_statistics(message, bot),
        func=lambda message: message.text == MainMenuCommands.GET_STATS
    )
    bot.register_message_handler(
        lambda message: edit_price_start(message, bot),
        func=lambda message: message.text == MainMenuCommands.EDIT_PRICE
    )
    # Здесь будут регистрироваться другие обработчики


@access_checker
def start_handler(message: Message, bot: telebot.TeleBot):
    """
    Обработчик команд /start и /help.
    Отправляет приветственное сообщение и главное меню.
    """
    bot.send_message(
        message.chat.id,
        "Привет! Я бот для отслеживания цен на предметы. Выбери действие:",
        reply_markup=main_menu_keyboard()
    )


# --- Логика редактирования цены (новая версия) ---

@access_checker
def edit_price_start(message: Message, bot: telebot.TeleBot):
    """
    Начало сценария редактирования цены.
    Показывает нумерованный список предметов и клавиатуру с цифрами.
    """
    items = db.get_all_items()
    if not items:
        bot.send_message(message.chat.id, "У вас пока нет предметов для редактирования.")
        return

    report_parts = ["*Какой предмет вы хотите отредактировать?*\nОтправьте его номер (для первых 10 можно использовать клавиатуру).\n"]
    for i, item in enumerate(items, 1):
        report_parts.append(f"*{i}*. {item['title']} (текущая цена: ${item['purchase_price']:.2f})")
    
    report = "\n".join(report_parts)
    
    bot.send_message(
        message.chat.id,
        report,
        reply_markup=numeric_keyboard(len(items)),
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(message, process_item_choice_for_edit, bot, items)


def process_item_choice_for_edit(message: Message, bot: telebot.TeleBot, items: list):
    """
    Обрабатывает выбор номера предмета для редактирования.
    """
    if message.text == ActionCommands.CANCEL:
        return cancel_handler(message, bot)

    if not message.text or not message.text.isdigit():
        bot.send_message(message.chat.id, "Пожалуйста, введите номер предмета из списка.", reply_markup=numeric_keyboard(len(items)))
        bot.register_next_step_handler(message, process_item_choice_for_edit, bot, items)
        return
        
    choice = int(message.text)
    if not (1 <= choice <= len(items)):
        bot.send_message(message.chat.id, f"Неверный номер. Введите число от 1 до {len(items)}.", reply_markup=numeric_keyboard(len(items)))
        bot.register_next_step_handler(message, process_item_choice_for_edit, bot, items)
        return

    selected_item = items[choice - 1]
    item_id = selected_item['id']
    item_title = selected_item['title']

    bot.send_message(
        message.chat.id,
        f"Введите новую закупочную цену для '{item_title}':",
        reply_markup=cancel_keyboard()
    )
    bot.register_next_step_handler(message, process_new_price_step, bot, item_id)


def process_new_price_step(message: Message, bot: telebot.TeleBot, item_id: int):
    """
    Обрабатывает новую цену и обновляет ее в БД.
    """
    if message.text == ActionCommands.CANCEL:
        return cancel_handler(message, bot)

    if not message.text:
        bot.send_message(message.chat.id, "Пожалуйста, отправь цену в виде текстового сообщения.", reply_markup=cancel_keyboard())
        bot.register_next_step_handler(message, process_new_price_step, bot, item_id)
        return

    try:
        new_price = float(message.text.replace(',', '.'))
    except (ValueError, TypeError):
        bot.send_message(message.chat.id, "Неверный формат цены. Попробуй еще раз, например: 15.55", reply_markup=cancel_keyboard())
        bot.register_next_step_handler(message, process_new_price_step, bot, item_id)
        return
    
    if db.set_purchase_price_by_id(item_id, new_price):
        bot.send_message(
            message.chat.id, 
            f"✅ Цена закупки для предмета успешно изменена на ${new_price:.2f}.",
            reply_markup=main_menu_keyboard()
        )
    else:
        bot.send_message(
            message.chat.id, 
            "❌ Не удалось изменить цену. Предмет не найден.",
            reply_markup=main_menu_keyboard()
        )


# --- Логика удаления предмета (новая версия) ---

@access_checker
def delete_item_start(message: Message, bot: telebot.TeleBot):
    """
    Начало сценария удаления предмета.
    Показывает нумерованный список предметов и клавиатуру с цифрами.
    """
    items = db.get_all_items()
    if not items:
        bot.send_message(message.chat.id, "У вас пока нет отслеживаемых предметов.")
        return

    report_parts = ["*Какой предмет вы хотите удалить?*\nОтправьте его номер (для первых 10 можно использовать клавиатуру).\n"]
    for i, item in enumerate(items, 1):
        report_parts.append(f"*{i}*. {item['title']}")

    report = "\n".join(report_parts)
    bot.send_message(
        message.chat.id,
        report,
        reply_markup=numeric_keyboard(len(items)),
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(message, process_item_choice_for_delete, bot, items)


def process_item_choice_for_delete(message: Message, bot: telebot.TeleBot, items: list):
    """Обрабатывает выбор номера предмета для удаления."""
    if message.text == ActionCommands.CANCEL:
        return cancel_handler(message, bot)

    if not message.text or not message.text.isdigit():
        bot.send_message(message.chat.id, "Пожалуйста, введите номер предмета из списка.", reply_markup=numeric_keyboard(len(items)))
        bot.register_next_step_handler(message, process_item_choice_for_delete, bot, items)
        return

    choice = int(message.text)
    if not (1 <= choice <= len(items)):
        bot.send_message(message.chat.id, f"Неверный номер. Введите число от 1 до {len(items)}.", reply_markup=numeric_keyboard(len(items)))
        bot.register_next_step_handler(message, process_item_choice_for_delete, bot, items)
        return

    selected_item = items[choice - 1]
    item_id = selected_item['id']
    item_title = selected_item['title']

    # Запрашиваем подтверждение
    bot.send_message(
        message.chat.id,
        f"Вы уверены, что хотите удалить '{item_title}'?",
        reply_markup=confirm_delete_keyboard()
    )
    bot.register_next_step_handler(message, confirm_delete_step, bot, item_id, item_title)


def confirm_delete_step(message: Message, bot: telebot.TeleBot, item_id: int, item_title: str):
    """Подтверждение удаления."""
    if message.text == ActionCommands.CANCEL:
        return cancel_handler(message, bot)

    if message.text != ActionCommands.CONFIRM_DELETE:
        # Если что-то другое, повторяем запрос
        bot.send_message(message.chat.id, "Нажмите '✅ Да' для удаления или '❌ Отмена' для отмены.", reply_markup=confirm_delete_keyboard())
        bot.register_next_step_handler(message, confirm_delete_step, bot, item_id, item_title)
        return

    if db.remove_item(item_id):
        bot.send_message(
            message.chat.id,
            f"✅ Предмет '{item_title}' был успешно удалён.",
            reply_markup=main_menu_keyboard()
        )
    else:
        bot.send_message(
            message.chat.id,
            "❌ Не удалось удалить предмет.",
            reply_markup=main_menu_keyboard()
        )


# --- Логика статистики ---

@access_checker
def show_statistics(message: Message, bot: telebot.TeleBot):
    """
    Показывает статистику по всем отслеживаемым предметам.
    """
    items_data = db.get_all_items()

    if not items_data:
        bot.send_message(message.chat.id, "У вас пока нет отслеживаемых предметов для статистики.")
        return

    total_purchase_price = 0
    total_current_price = 0
    
    report_parts = ["<b>📊 Статистика по предметам:</b>\n"]

    for item_data in items_data:
        item = Item.from_dict(item_data)
        
        purchase_price = item.purchase_price or 0
        current_price = item.current_price or 0

        total_purchase_price += purchase_price
        total_current_price += current_price

        absolute_profit, percent_profit = item.calculate_profit()

        sign = "🟢" if absolute_profit >= 0 else "🔴"
        
        report_parts.append(
            f"\n<b>{item.title}</b>\n"
            f"  - Цена покупки: ${purchase_price:.2f}\n"
            f"  - Текущая цена: ${current_price:.2f}\n"
            f"  - Прибыль: {sign} ${absolute_profit:.2f} ({percent_profit:.2f}%)"
        )
    
    # Расчет общей прибыли
    total_profit = total_current_price - total_purchase_price
    total_profit_percent = (total_profit / total_purchase_price * 100) if total_purchase_price > 0 else 0
    total_sign = "🟢" if total_profit >= 0 else "🔴"

    # Итоговая сводка
    summary = (
        f"\n\n\n<b>📈 Итого:</b>\n"
        f"  - Общая сумма закупки: ${total_purchase_price:.2f}\n"
        f"  - Общая текущая стоимость: ${total_current_price:.2f}\n"
        f"  - <b>Общая прибыль: {total_sign} ${total_profit:.2f} ({total_profit_percent:.2f}%)</b>"
    )
    report_parts.append(summary)

    # Отправляем отчет
    # Разделяем на части, если он слишком длинный
    full_report = "\n".join(report_parts)
    if len(full_report) > 4096:
        for i in range(0, len(full_report), 4096):
            bot.send_message(message.chat.id, full_report[i:i + 4096])
    else:
        bot.send_message(message.chat.id, full_report)


# --- Логика добавления предмета ---

@access_checker
def add_item_start(message: Message, bot: telebot.TeleBot):
    """
    Начало сценария добавления предмета.
    Запрашивает у пользователя URL.
    """
    bot.send_message(
        message.chat.id, 
        "Пожалуйста, отправь мне ссылку на предмет:", 
        reply_markup=cancel_keyboard()
    )
    bot.register_next_step_handler(message, process_url_step, bot)


def process_url_step(message: Message, bot: telebot.TeleBot):
    """
    Обрабатывает полученный URL и запрашивает цену закупки.
    """
    if message.text == ActionCommands.CANCEL:
        return cancel_handler(message, bot)

    if not message.text:
        bot.send_message(message.chat.id, "Пожалуйста, отправь ссылку в виде текстового сообщения.", reply_markup=cancel_keyboard())
        bot.register_next_step_handler(message, process_url_step, bot)
        return

    url = message.text
    if not config.is_valid_url(url):
        bot.send_message(message.chat.id, "Этот домен не поддерживается. Пожалуйста, отправь ссылку с одного из разрешенных доменов.", reply_markup=cancel_keyboard())
        bot.register_next_step_handler(message, process_url_step, bot)
        return
        
    bot.send_message(
        message.chat.id, 
        "Отлично! Теперь введи цену закупки (например: 15.55):",
        reply_markup=cancel_keyboard()
    )
    bot.register_next_step_handler(message, process_price_step, bot, url)


def process_price_step(message: Message, bot: telebot.TeleBot, url: str):
    """
    Обрабатывает цену закупки, парсит данные и сохраняет предмет в БД.
    """
    if message.text == ActionCommands.CANCEL:
        return cancel_handler(message, bot)

    if not message.text:
        bot.send_message(message.chat.id, "Пожалуйста, отправь цену в виде текстового сообщения.", reply_markup=cancel_keyboard())
        bot.register_next_step_handler(message, process_price_step, bot, url)
        return

    try:
        purchase_price = float(message.text.replace(',', '.'))
    except (ValueError, TypeError):
        bot.send_message(message.chat.id, "Неверный формат цены. Попробуй еще раз, например: 15.55", reply_markup=cancel_keyboard())
        bot.register_next_step_handler(message, process_price_step, bot, url)
        return

    bot.send_message(message.chat.id, "⏳ Начинаю обработку, это может занять некоторое время...", reply_markup=main_menu_keyboard())

    try:
        # Используем парсер как контекстный менеджер
        with CSMarketParser() as parser:
            item_data = parser.parse_item_page(url)

        if not item_data or not item_data.get('title'):
            bot.send_message(message.chat.id, "Не удалось получить данные о предмете. Проверь ссылку и попробуй снова.")
            return

        # 1. Добавляем предмет в БД (с ценой закупки 0)
        db.add_item(item_data)
        
        # 2. Устанавливаем цену закупки (и пересчитываем прибыль)
        db.set_purchase_price(url, purchase_price)

        bot.send_message(
            message.chat.id,
            f"✅ Предмет '{item_data['title']}' успешно добавлен с ценой закупки ${purchase_price:.2f}."
        )

    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"Произошла ошибка при обработке: {e}. Попробуй еще раз."
        )


def cancel_handler(message: Message, bot: telebot.TeleBot):
    """
    Обрабатывает команду отмены, сбрасывает состояние и возвращает в главное меню.
    """
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    bot.send_message(
        message.chat.id, 
        "Действие отменено.", 
        reply_markup=main_menu_keyboard()
    )
