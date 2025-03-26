import sqlite3
import os

class Database:
    def __init__(self):
        # Получаем путь к текущей директории
        db_path = os.path.join(os.path.dirname(__file__), 'users.db')
        self.conn = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL
        )
        ''')
        self.conn.commit()

    def add_user(self, user_id: int, username: str, full_name: str, phone: str):
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO users (user_id, username, full_name, phone) VALUES (?, ?, ?, ?)',
            (user_id, username, full_name, phone)
        )
        self.conn.commit()

    def get_user(self, user_id: int):
        cursor = self.conn.cursor()
        cursor.execute('SELECT full_name, phone FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        if result:
            return {'full_name': result[0], 'phone': result[1]}
        return None

    def update_user_phone(self, user_id: int, phone: str):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET phone = ? WHERE user_id = ?', (phone, user_id))
        self.conn.commit()

    def update_user_name(self, user_id: int, full_name: str):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET full_name = ? WHERE user_id = ?', (full_name, user_id))
        self.conn.commit()

    def close(self):
        self.conn.close() 