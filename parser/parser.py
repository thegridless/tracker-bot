from DrissionPage import ChromiumPage, ChromiumOptions
import time
import re
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup


class CSMarketParser:
    """Парсер для CS:GO маркета с использованием DrissionPage + BeautifulSoup4"""
    
    def __init__(self, wait_time: int = 5):
        """
        Инициализация парсера
        
        Args:
            wait_time: Время ожидания загрузки страницы в секундах
        """
        self.wait_time = wait_time
        self.page = None
        self.soup = None
    
    def __enter__(self):
        """Контекстный менеджер - вход"""
        # Создаем опции для запуска в headless-режиме, необходимом для сервера
        co = ChromiumOptions()
        co.set_argument('--headless', 'true')
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        # Указываем путь к исполняемому файлу браузера на сервере
        co.set_browser_path(path='/usr/bin/chromium-browser')
        self.page = ChromiumPage(addr_or_opts=co)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер - выход"""
        if self.page:
            self.page.quit()
    
    def parse_item_page(self, url: str) -> Dict[str, Any]:
        """
        Парсит страницу предмета на CS:GO маркете
        
        Args:
            url: URL страницы предмета
            
        Returns:
            Словарь с основными данными о предмете
        """
        if not self.page:
            raise RuntimeError("Парсер не инициализирован. Используйте контекстный менеджер.")
        
        print(f"Переходим на страницу: {url}")
        
        # Переходим на страницу
        self.page.get(url)
        
        print(f"Ждем загрузки страницы ({self.wait_time} сек)...")
        # Ждем загрузки JavaScript
        time.sleep(self.wait_time)
        
        # Получаем HTML и создаем soup
        html_content = self.page.html
        self.soup = BeautifulSoup(html_content, 'html.parser')
        print("HTML загружен в BeautifulSoup")
        
        # Извлекаем только основные данные
        result = {
            'url': url,
            'title': self._extract_title(),
            'price': self._extract_best_offer_price(),
            'avg_price': self._extract_price_info('Average price:'),
            'sales_count': self._extract_sales_count(),
        }
        
        return result
    
    def save_html(self, filename: str = 'parsed_page.html') -> None:
        """
        Сохраняет текущий HTML в файл
        
        Args:
            filename: Имя файла для сохранения
        """
        if self.page:
            html_content = self.page.html
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"HTML сохранен в файл: {filename}")
    
    def _extract_title(self) -> Optional[str]:
        """Извлекает название предмета"""
        try:
            # Пробуем разные селекторы для заголовка
            selectors = [
                'h1.name span',
                'h1.name',
                'h1 span[data-title]',
                '.name span',
                'h1'
            ]
            
            for selector in selectors:
                element = self.soup.select_one(selector)
                if element and element.get_text(strip=True):
                    return element.get_text(strip=True)
                    
        except Exception as e:
            print(f"Ошибка при извлечении названия: {e}")
        return None
    
    def _extract_best_offer_price(self) -> Optional[str]:
        """Извлекает лучшую цену предложения"""
        try:
            # Ищем элемент с классом best-offer
            selectors = [
                '.best-offer',
                '[class*="best-offer"]',
                '.price',
                '[class*="price"]'
            ]
            
            for selector in selectors:
                elements = self.soup.select(selector)
                for element in elements:
                    text = element.get_text()
                    # Ищем цену в долларах
                    price_match = re.search(r'\$(\d+(?:\.\d+)?)', text)
                    if price_match:
                        return f"${price_match.group(1)}"
                    
                    # Альтернативный поиск для долларов
                    price_match = re.search(r'(\d+(?:\.\d+)?)\s*\$', text)
                    if price_match:
                        return f"${price_match.group(1)}"
                        
        except Exception as e:
            print(f"Ошибка при извлечении цены best-offer: {e}")
        
        return None
    
    def _extract_price_info(self, label: str) -> Optional[str]:
        """
        Извлекает цену по метке (например 'Average price:')
        
        Args:
            label: Текстовая метка перед ценой
        """
        try:
            # Ищем элемент, содержащий нужную метку
            elements = self.soup.find_all(string=re.compile(label, re.IGNORECASE))
            for element in elements:
                # Ищем родительский элемент
                parent = element.parent if hasattr(element, 'parent') else None
                if parent:
                    # Ищем цену в долларах в родительском элементе или его потомках
                    price_text = parent.get_text()
                    price_match = re.search(r'\$(\d+(?:,\d+)*(?:\.\d+)?)', price_text)
                    if price_match:
                        return f"${price_match.group(1)}"
                    
                    # Поиск в соседних элементах
                    if parent.parent:
                        siblings_text = parent.parent.get_text()
                        price_match = re.search(r'\$(\d+(?:,\d+)*(?:\.\d+)?)', siblings_text)
                        if price_match:
                            return f"${price_match.group(1)}"
                            
        except Exception as e:
            print(f"Ошибка при извлечении {label}: {e}")
        
        return None
    
    def _extract_sales_count(self) -> Optional[int]:
        """Извлекает количество продаж"""
        try:
            # Ищем элемент с информацией о продажах (английская версия)
            patterns = [
                r'Sales:\s*(\d+)',
                r'Sold:\s*(\d+)',
                r'(\d+)\s*sales',
                r'(\d+)\s*sold'
            ]
            
            page_text = self.soup.get_text()
            for pattern in patterns:
                sales_match = re.search(pattern, page_text, re.IGNORECASE)
                if sales_match:
                    return int(sales_match.group(1))
                    
        except Exception as e:
            print(f"Ошибка при извлечении количества продаж: {e}")
        
        return None 