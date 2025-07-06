# -*- coding: utf-8 -*-
"""
Модель предмета CS Market
"""
from datetime import datetime
from typing import Optional


class Item:
    """Модель предмета CS Market"""
    
    def __init__(self, id: Optional[int] = None, url: str = "", title: str = "", 
                 current_price: float = 0.0, avg_price: float = 0.0, 
                 sales_count: int = 0, purchase_price: float = 0.0, 
                 profit_percent: float = 0.0, created_at: Optional[datetime] = None, 
                 updated_at: Optional[datetime] = None):
        self.id = id
        self.url = url
        self.title = title
        self.current_price = current_price
        self.avg_price = avg_price
        self.sales_count = sales_count
        self.purchase_price = purchase_price
        self.profit_percent = profit_percent
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    def calculate_profit(self) -> tuple[float, float]:
        """
        Рассчитывает прибыль в абсолютных числах и процентах
        
        Returns:
            tuple[float, float]: (абсолютная_прибыль, процент_прибыли)
        """
        if self.purchase_price <= 0:
            return 0.0, 0.0
        
        absolute_profit = self.current_price - self.purchase_price
        percent_profit = (absolute_profit / self.purchase_price) * 100
        
        return absolute_profit, percent_profit
    
    def to_dict(self) -> dict:
        """Преобразует объект в словарь"""
        return {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'current_price': self.current_price,
            'avg_price': self.avg_price,
            'sales_count': self.sales_count,
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
            avg_price=data.get('avg_price', 0.0),
            sales_count=data.get('sales_count', 0),
            purchase_price=data.get('purchase_price', 0.0),
            profit_percent=data.get('profit_percent', 0.0),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        ) 