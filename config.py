import os
from typing import Optional


class BotConfig:
    """Конфигурация телеграм бота"""
    
    def __init__(self):
        # Токен бота (получить от @BotFather)
        self.BOT_TOKEN: Optional[str] = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
        
        # ID администратора (для рассылки уведомлений)
        self.ADMIN_ID: Optional[int] = int(os.getenv('ADMIN_ID', '0'))  # Заглушка
        
        # Настройки базы данных
        self.DATABASE_PATH: str = 'db/cs_market.db'
        
        # Настройки парсера
        self.PARSER_WAIT_TIME: int = 5  # Время ожидания загрузки страницы
        
        # Настройки рассылки
        self.NOTIFICATION_INTERVAL_HOURS: int = 4  # Интервал рассылки в часах
        
        # Разрешенные домены для добавления ссылок
        self.ALLOWED_DOMAINS: list = [
            'market.csgo.com',
            'steamcommunity.com'
        ]
    
    def is_valid_url(self, url: str) -> bool:
        """Проверяет, является ли URL допустимым для парсинга"""
        return any(domain in url for domain in self.ALLOWED_DOMAINS)
    
    def is_admin(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь администратором"""
        return user_id == self.ADMIN_ID
        
    def validate_config(self) -> bool:
        """Проверяет корректность конфигурации"""
        if not self.BOT_TOKEN or self.BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
            print("❌ Не установлен токен бота! Получите токен от @BotFather")
            return False
            
        if not self.ADMIN_ID or self.ADMIN_ID == 0:
            print("⚠️  Не установлен ID администратора! Рассылка будет отключена")
            
        return True


# Создаем глобальный экземпляр конфигурации
config = BotConfig() 