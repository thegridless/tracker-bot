# -*- coding: utf-8 -*-
"""
Модуль для создания клавиатур телеграм-бота.
"""
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from item_tracker_bot.constants import MainMenuCommands, ActionCommands


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Создает и возвращает клавиатуру главного меню.
    
    Returns:
        ReplyKeyboardMarkup: Объект клавиатуры для главного меню.
    """
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    add_item_btn = KeyboardButton(MainMenuCommands.ADD_ITEM)
    remove_item_btn = KeyboardButton(MainMenuCommands.REMOVE_ITEM)
    stats_btn = KeyboardButton(MainMenuCommands.GET_STATS)
    edit_price_btn = KeyboardButton(MainMenuCommands.EDIT_PRICE)
    
    markup.add(add_item_btn, remove_item_btn)
    markup.add(stats_btn, edit_price_btn)
    
    return markup


def cancel_keyboard() -> ReplyKeyboardMarkup:
    """
    Создает и возвращает клавиатуру с кнопкой 'Отмена'.
    
    Returns:
        ReplyKeyboardMarkup: Объект клавиатуры.
    """
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    cancel_btn = KeyboardButton(ActionCommands.CANCEL)
    markup.add(cancel_btn)
    return markup


def numeric_keyboard(count: int) -> ReplyKeyboardMarkup:
    """
    Создает клавиатуру с цифрами от 1 до `count` и кнопкой 'Отмена'.
    
    Args:
        count (int): Максимальное число для кнопок.
        
    Returns:
        ReplyKeyboardMarkup: Объект клавиатуры.
    """
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    
    # Ограничиваем количество кнопок, чтобы не перегружать клавиатуру
    limit = min(count, 10)
    buttons = [KeyboardButton(str(i)) for i in range(1, limit + 1)]
    
    # Расставляем кнопки по 5 в ряд
    for i in range(0, len(buttons), 5):
        markup.add(*buttons[i:i+5])
    
    # Добавляем кнопку отмены в самый низ
    markup.add(KeyboardButton(ActionCommands.CANCEL))
    return markup


def confirm_delete_keyboard() -> ReplyKeyboardMarkup:
    """
    Создает клавиатуру с кнопками подтверждения удаления.
    """
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    yes_btn = KeyboardButton(ActionCommands.CONFIRM_DELETE)
    cancel_btn = KeyboardButton(ActionCommands.CANCEL)
    markup.add(yes_btn, cancel_btn)
    return markup
