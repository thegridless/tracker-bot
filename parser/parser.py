from DrissionPage import ChromiumPage, ChromiumOptions
import time
import re
import subprocess
import shutil
import os
import tempfile
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
    
    @staticmethod
    def _find_browser_path() -> Optional[str]:
        """
        Находит путь к установленному браузеру Chromium/Chrome
        
        Returns:
            Путь к исполняемому файлу браузера или None, если не найден
        """
        # Список возможных путей и команд для поиска браузера
        possible_paths = [
            '/usr/bin/chromium-browser',
            '/usr/bin/chromium',
            '/usr/bin/google-chrome',
            '/snap/bin/chromium',
        ]
        
        # Проверяем стандартные пути
        for path in possible_paths:
            if shutil.which(path.split('/')[-1]) or os.path.exists(path):
                # Проверяем, что это действительно исполняемый файл браузера
                try:
                    result = subprocess.run(
                        [path, '--version'],
                        capture_output=True,
                        timeout=5,
                        text=True
                    )
                    if result.returncode == 0 or 'Chromium' in result.stdout or 'Chrome' in result.stdout:
                        return path
                except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
                    continue
        
        # Пробуем найти через which
        for cmd in ['chromium-browser', 'chromium', 'google-chrome']:
            path = shutil.which(cmd)
            if path:
                return path
        
        return None
    
    def __enter__(self):
        """Контекстный менеджер - вход"""
        # Создаем опции для запуска в headless-режиме, необходимом для сервера
        co = ChromiumOptions()
        # Устанавливаем headless режим (новый формат для Chrome/Chromium)
        co.set_argument('--headless=new')
        # Параметры для Linux систем без GUI (решают проблему подключения к браузеру)
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        co.set_argument('--disable-gpu')
        co.set_argument('--disable-software-rasterizer')
        # Автоматически находим путь к браузеру
        browser_path = self._find_browser_path()
        if browser_path:
            co.set_browser_path(path=browser_path)
            print(f"Используется браузер: {browser_path}")
        else:
            print("⚠️  Браузер не найден автоматически. Установите Chromium: sudo snap install chromium")
            # Пробуем без указания пути - DrissionPage может найти сам
        # Выделяем отдельный профиль и порт, чтобы избежать конфликтов подключения
        profile_dir = os.path.join(tempfile.gettempdir(), f"drission_profile_{os.getpid()}")
        os.makedirs(profile_dir, exist_ok=True)
        co.set_user_data_path(profile_dir)
        co.auto_port()
        # Инициализируем страницу с опциями (DrissionPage сам управляет портом)
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