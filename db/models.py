# -*- coding: utf-8 -*-
"""
Модель предмета CS Market
"""
from datetime import datetime
from typing import Optional


class Item:
    """Модель предмета CS Market"""
    
    def __init__(self, id: Optional[int] = None, url: str = "", title: str = "", 
                 current_price: float = 0.0, 
                 purchase_price: float = 0.0, 
                 profit_percent: float = 0.0, created_at: Optional[datetime] = None, 
                 updated_at: Optional[datetime] = None):
        self.id = id
        self.url = url
        self.title = title
        self.current_price = current_price
        self.purchase_price = purchase_price
        self.profit_percent = profit_percent
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    def calculate_profit(self) -> tuple[float, float]:
        """
        Рассчитывает прибыль в абсолютных числах и процентах.
        Если цена закупки не задана (<=0) или текущая цена отсутствует,
        возвращает (0.0, 0.0) без выброса исключений.
        
        Returns:
            tuple[float, float]: (абсолютная_прибыль, процент_прибыли)
        """
        # Без корректной цены закупки посчитать доход невозможно
        if not self.purchase_price or self.purchase_price <= 0:
            return 0.0, 0.0

        # Если текущая цена None, считаем её равной 0 для корректного вычитания
        current_price = self.current_price or 0.0

        absolute_profit = current_price - self.purchase_price
        percent_profit = (absolute_profit / self.purchase_price) * 100

        return absolute_profit, percent_profit
    
    def to_dict(self) -> dict:
        """Преобразует объект в словарь"""
        return {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'current_price': self.current_price,
            'purchase_price': self.purchase_price,
            'profit_percent': self.profit_percent,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Item':
        """Создает объект из словаря"""
        return cls(
            id=data.get('id'),
            url=data.get('url', ''),
            title=data.get('title', ''),
            current_price=data.get('current_price', 0.0),
            purchase_price=data.get('purchase_price', 0.0),
            profit_percent=data.get('profit_percent', 0.0),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        ) 