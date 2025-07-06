# -*- coding: utf-8 -*-
"""
Модуль для хранения констант проекта, таких как команды меню.
"""
from enum import Enum


class MainMenuCommands(str, Enum):
    """Команды главного меню."""
    ADD_ITEM = "➕ Добавить предмет"
    REMOVE_ITEM = "🗑️ Удалить предмет"
    GET_STATS = "📊 Статистика"
    EDIT_PRICE = "✏️ Редактировать цену"


class ActionCommands(str, Enum):
    """Команды для действий в процессе диалога."""
    CANCEL = "❌ Отмена"
    CONFIRM_DELETE = "✅ Да" 