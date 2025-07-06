import sqlite3
import json
from typing import Dict, Any, List, Optional
from datetime import datetime


class CSMarketDatabase:
    """Класс для работы с базой данных CS:GO маркета"""
    
    def __init__(self, db_path: str = 'cs_market.db'):
        """
        Инициализация базы данных
        
        Args:
            db_path: Путь к файлу базы данных
        """
        self.db_path = db_path
        self.create_tables()
    
    def create_tables(self):
        """Создает таблицы в базе данных"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Создаем таблицу для предметов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    current_price REAL,
                    avg_price REAL,
                    sales_count INTEGER,
                    purchase_price REAL DEFAULT 0,
                    profit_percent REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Создаем индекс для быстрого поиска по URL
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_url ON items(url)
            ''')
            
            conn.commit()
            print("Таблицы созданы успешно")
    
    def add_item(self, item_data: Dict[str, Any]) -> bool:
        """
        Добавляет новый предмет в базу данных
        
        Args:
            item_data: Словарь с данными о предмете
            
        Returns:
            True если добавление успешно, False если предмет уже существует
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Конвертируем цены в числа
                current_price = self._parse_price(item_data.get('price'))
                avg_price = self._parse_price(item_data.get('avg_price'))
                
                cursor.execute('''
                    INSERT OR IGNORE INTO items 
                    (url, title, current_price, avg_price, sales_count, purchase_price, profit_percent)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item_data['url'],
                    item_data['title'],
                    current_price,
                    avg_price,
                    item_data.get('sales_count', 0),
                    0,  # purchase_price по умолчанию 0
                    0   # profit_percent по умолчанию 0
                ))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    print(f"Предмет добавлен: {item_data['title']}")
                    return True
                else:
                    print(f"Предмет уже существует: {item_data['title']}")
                    return False
                    
        except Exception as e:
            print(f"Ошибка при добавлении предмета: {e}")
            return False
    
    def update_item(self, item_data: Dict[str, Any]) -> bool:
        """
        Обновляет существующий предмет в базе данных
        
        Args:
            item_data: Словарь с данными о предмете
            
        Returns:
            True если обновление успешно
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Конвертируем цены в числа
                current_price = self._parse_price(item_data.get('price'))
                avg_price = self._parse_price(item_data.get('avg_price'))
                
                # Обновляем данные предмета и сразу пересчитываем прибыль
                cursor.execute('''
                    UPDATE items 
                    SET title = ?, current_price = ?, avg_price = ?, 
                        sales_count = ?, updated_at = CURRENT_TIMESTAMP,
                        profit_percent = CASE 
                            WHEN purchase_price > 0 THEN 
                                ((? - purchase_price) / purchase_price) * 100
                            ELSE 0 
                        END
                    WHERE url = ?
                ''', (
                    item_data['title'],
                    current_price,
                    avg_price,
                    item_data.get('sales_count', 0),
                    current_price,  # Для расчета прибыли
                    item_data['url']
                ))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    # Получаем обновленные данные для отображения
                    cursor.execute('SELECT current_price, purchase_price, profit_percent FROM items WHERE url = ?', (item_data['url'],))
                    row = cursor.fetchone()
                    if row:
                        current_p, purchase_p, profit_p = row
                        if purchase_p > 0:
                            print(f"🧮 Расчет прибыли: ({current_p} - {purchase_p}) / {purchase_p} * 100 = {profit_p:.2f}%")
                            print(f"✅ Прибыль обновлена: {profit_p:.2f}%")
                    
                    print(f"Предмет обновлен: {item_data['title']}")
                    return True
                else:
                    print(f"Предмет не найден для обновления: {item_data['title']}")
                    return False
                    
        except Exception as e:
            print(f"Ошибка при обновлении предмета: {e}")
            return False
    
    def upsert_item(self, item_data: Dict[str, Any]) -> bool:
        """
        Добавляет или обновляет предмет
        
        Args:
            item_data: Словарь с данными о предмете
            
        Returns:
            True если операция успешна
        """
        # Сначала пытаемся добавить
        if not self.add_item(item_data):
            # Если не получилось добавить, обновляем
            return self.update_item(item_data)
        return True
    
    def set_purchase_price(self, url: str, purchase_price: float) -> bool:
        """
        Устанавливает цену закупки для предмета
        
        Args:
            url: URL предмета
            purchase_price: Цена закупки
            
        Returns:
            True если операция успешна
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Устанавливаем цену закупки и сразу пересчитываем прибыль
                cursor.execute('''
                    UPDATE items 
                    SET purchase_price = ?, updated_at = CURRENT_TIMESTAMP,
                        profit_percent = CASE 
                            WHEN current_price IS NOT NULL AND ? > 0 THEN 
                                ((current_price - ?) / ?) * 100
                            ELSE 0 
                        END
                    WHERE url = ?
                ''', (purchase_price, purchase_price, purchase_price, purchase_price, url))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    # Получаем обновленные данные для отображения
                    cursor.execute('SELECT current_price, purchase_price, profit_percent FROM items WHERE url = ?', (url,))
                    row = cursor.fetchone()
                    if row:
                        current_p, purchase_p, profit_p = row
                        print(f"🧮 Расчет прибыли: ({current_p} - {purchase_p}) / {purchase_p} * 100 = {profit_p:.2f}%")
                        print(f"✅ Прибыль обновлена: {profit_p:.2f}%")
                    
                    print(f"Цена закупки установлена: ${purchase_price}")
                    return True
                else:
                    print("Предмет не найден")
                    return False
                    
        except Exception as e:
            print(f"Ошибка при установке цены закупки: {e}")
            return False
    
    def set_purchase_price_by_id(self, item_id: int, purchase_price: float) -> bool:
        """
        Устанавливает цену закупки для предмета по его ID.
        
        Args:
            item_id: ID предмета
            purchase_price: Цена закупки
            
        Returns:
            True если операция успешна
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE items 
                    SET purchase_price = ?, updated_at = CURRENT_TIMESTAMP,
                        profit_percent = CASE 
                            WHEN current_price IS NOT NULL AND ? > 0 THEN 
                                ((current_price - ?) / ?) * 100
                            ELSE 0 
                        END
                    WHERE id = ?
                ''', (purchase_price, purchase_price, purchase_price, purchase_price, item_id))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    print(f"Цена закупки для ID {item_id} установлена: ${purchase_price}")
                    return True
                else:
                    print(f"Предмет с ID {item_id} не найден")
                    return False
                    
        except Exception as e:
            print(f"Ошибка при установке цены закупки по ID: {e}")
            return False
    
    def get_all_items(self) -> List[Dict[str, Any]]:
        """
        Возвращает все предметы из базы данных
        
        Returns:
            Список словарей с данными о предметах
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, url, title, current_price, avg_price, sales_count, 
                           purchase_price, profit_percent, created_at, updated_at
                    FROM items
                    ORDER BY updated_at DESC
                ''')
                
                columns = [desc[0] for desc in cursor.description]
                items = []
                
                for row in cursor.fetchall():
                    item_dict = dict(zip(columns, row))
                    items.append(item_dict)
                
                return items
                
        except Exception as e:
            print(f"Ошибка при получении предметов: {e}")
            return []
    
    def get_item_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Возвращает предмет по URL
        
        Args:
            url: URL предмета
            
        Returns:
            Словарь с данными о предмете или None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, url, title, current_price, avg_price, sales_count, 
                           purchase_price, profit_percent, created_at, updated_at
                    FROM items
                    WHERE url = ?
                ''', (url,))
                
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
                
                return None
                
        except Exception as e:
            print(f"Ошибка при поиске предмета: {e}")
            return None
    
    def get_items_by_url(self, url: str) -> List[Dict[str, Any]]:
        """
        Возвращает предметы по URL (возвращает список для совместимости)
        
        Args:
            url: URL предмета
            
        Returns:
            Список с одним элементом или пустой список
        """
        item = self.get_item_by_url(url)
        return [item] if item else []
    
    def get_item_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        """
        Возвращает предмет по ID
        
        Args:
            item_id: ID предмета
            
        Returns:
            Словарь с данными о предмете или None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, url, title, current_price, avg_price, sales_count, 
                           purchase_price, profit_percent, created_at, updated_at
                    FROM items
                    WHERE id = ?
                ''', (item_id,))
                
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
                
                return None
                
        except Exception as e:
            print(f"Ошибка при поиске предмета по ID: {e}")
            return None
    
    def remove_item(self, item_id: int) -> bool:
        """
        Удаляет предмет из базы данных
        
        Args:
            item_id: ID предмета
            
        Returns:
            True если удаление успешно
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Сначала получаем название предмета для вывода
                cursor.execute('SELECT title FROM items WHERE id = ?', (item_id,))
                row = cursor.fetchone()
                
                if not row:
                    print(f"Предмет с ID {item_id} не найден")
                    return False
                
                title = row[0]
                
                # Удаляем предмет
                cursor.execute('DELETE FROM items WHERE id = ?', (item_id,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    print(f"Предмет удален: {title}")
                    return True
                else:
                    print(f"Предмет с ID {item_id} не найден")
                    return False
                    
        except Exception as e:
            print(f"Ошибка при удалении предмета: {e}")
            return False
    
    def delete_item(self, item_id: int) -> bool:
        """
        Алиас для remove_item для единообразия API
        
        Args:
            item_id: ID предмета
            
        Returns:
            True если удаление успешно
        """
        return self.remove_item(item_id)
    
    def _parse_price(self, price_str: Any) -> Optional[float]:
        """
        Парсит строку цены в число
        
        Args:
            price_str: Строка сценой (например "$145.25")
            
        Returns:
            Число или None
        """
        if not price_str:
            return None
            
        try:
            # Убираем символы валют и пробелы
            cleaned = str(price_str).replace('$', '').replace(',', '').strip()
            return float(cleaned)
        except (ValueError, AttributeError):
            return None
    

    
    def print_items_table(self):
        """Выводит таблицу всех предметов"""
        items = self.get_all_items()
        
        if not items:
            print("Нет предметов в базе данных")
            return
        
        print("\n" + "="*120)
        print("ТРЕКИНГ ПРЕДМЕТОВ CS:GO МАРКЕТА")
        print("="*120)
        
        # Заголовки таблицы
        print(f"{'ID':<3} {'Название':<30} {'Текущая цена':<12} {'Сред. цена':<12} {'Цена закупки':<12} {'Прибыль %':<10} {'Продажи':<8}")
        print("-"*120)
        
        for item in items:
            title = item['title'][:27] + '...' if len(item['title']) > 30 else item['title']
            current_price = f"${item['current_price']:.2f}" if item['current_price'] else "N/A"
            avg_price = f"${item['avg_price']:.2f}" if item['avg_price'] else "N/A"
            purchase_price = f"${item['purchase_price']:.2f}" if item['purchase_price'] else "N/A"
            profit = f"{item['profit_percent']:.1f}%" if item['profit_percent'] else "0.0%"
            sales = item['sales_count'] if item['sales_count'] else 0
            
            print(f"{item['id']:<3} {title:<30} {current_price:<12} {avg_price:<12} {purchase_price:<12} {profit:<10} {sales:<8}")
        
        print("="*120) 