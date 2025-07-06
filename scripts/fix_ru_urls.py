#!/usr/bin/env python3
"""Скрипт для исправления URL в базе данных cs_market.db.
Заменяет сегмент "/ru/" на "/en/" во всех записях таблицы items.
Запускайте ОДНОКРАТНО из корня проекта:

    python scripts/fix_ru_urls.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / 'cs_market.db'


def fix_urls(db_path: Path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Ищем записи, содержащие /ru/
    cur.execute("SELECT id, url FROM items WHERE url LIKE '%/ru/%'")
    rows = cur.fetchall()

    if not rows:
        print("В базе нет URL с '/ru/'. Нечего исправлять.")
        conn.close()
        return

    updated = 0
    for item_id, url in rows:
        new_url = url.replace('/ru/', '/en/')
        if new_url != url:
            cur.execute("UPDATE items SET url = ? WHERE id = ?", (new_url, item_id))
            updated += 1
            print(f"ID {item_id}: {url} → {new_url}")

    conn.commit()
    conn.close()

    print(f"Готово! Исправлено {updated} записей.")


if __name__ == '__main__':
    print(f"Исправляем URL в базе данных: {DB_PATH}")
    fix_urls(DB_PATH) 