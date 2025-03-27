import sqlite3
import os
from .config import MAIN_ADMIN_ID

class Database:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            # Получаем путь к корневой директории бота (на уровень выше bot/)
            root_dir = os.path.dirname(os.path.dirname(__file__))
            self.db_path = os.path.join(root_dir, 'bot_database.db')
            print(f"Подключение к базе данных: {self.db_path}")
            
            # Создаем директорию для базы данных, если её нет
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Используем check_same_thread=False для работы в многопоточной среде
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.create_tables()
            self.init_main_admin()
            print("База данных успешно инициализирована")
            self._initialized = True

    def create_tables(self):
        cursor = self.conn.cursor()
        print("Создание таблиц в базе данных...")
        
        # Таблица пользователей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Таблица администраторов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            is_main_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Таблица заблокированных пользователей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS blocked_users (
            user_id INTEGER PRIMARY KEY,
            blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            blocked_by INTEGER,
            reason TEXT,
            FOREIGN KEY(blocked_by) REFERENCES users(user_id)
        )
        ''')
        
        self.conn.commit()
        print("Таблицы успешно созданы")

    def init_main_admin(self):
        """Инициализация главного администратора"""
        if MAIN_ADMIN_ID:
            cursor = self.conn.cursor()
            try:
                cursor.execute(
                    'INSERT OR IGNORE INTO admins (user_id, is_main_admin) VALUES (?, 1)',
                    (int(MAIN_ADMIN_ID),)
                )
                self.conn.commit()
                print(f"Главный администратор (ID: {MAIN_ADMIN_ID}) успешно инициализирован")
            except Exception as e:
                print(f"Ошибка при инициализации главного администратора: {e}")
                self.conn.rollback()
        else:
            print("ВНИМАНИЕ: MAIN_ADMIN_ID не установлен в конфигурации!")

    def is_admin(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь администратором"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
        return cursor.fetchone() is not None

    def is_main_admin(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь главным администратором"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT is_main_admin FROM admins WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result is not None and result[0] == 1

    def add_admin(self, user_id: int, username: str = None):
        """Добавляет нового администратора"""
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO admins (user_id, username) VALUES (?, ?)',
            (user_id, username)
        )
        self.conn.commit()

    def remove_admin(self, user_id: int):
        """Удаляет администратора"""
        if not self.is_main_admin(user_id):  # Нельзя удалить главного админа
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM admins WHERE user_id = ? AND is_main_admin = 0', (user_id,))
            self.conn.commit()

    def get_all_admins(self) -> list:
        """Получает список всех администраторов"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT user_id, username, is_main_admin FROM admins')
        return [
            {
                'user_id': row[0],
                'username': row[1],
                'is_main_admin': bool(row[2])
            }
            for row in cursor.fetchall()
        ]

    def add_user(self, user_id: int, username: str, full_name: str, phone: str):
        """Добавляет или обновляет пользователя"""
        cursor = self.conn.cursor()
        try:
            # Проверяем, существует ли пользователь
            cursor.execute('SELECT username, full_name, phone FROM users WHERE user_id = ?', (user_id,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                # Обновляем только если данные изменились
                if (existing_user[0] != username or 
                    existing_user[1] != full_name or 
                    existing_user[2] != phone):
                    cursor.execute('''
                        UPDATE users 
                        SET username = ?, 
                            full_name = ?, 
                            phone = ?,
                            last_updated = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    ''', (username, full_name, phone, user_id))
                    print(f"Обновлен пользователь: {full_name} (@{username})")
            else:
                # Добавляем нового пользователя
                cursor.execute('''
                    INSERT INTO users (user_id, username, full_name, phone)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, username, full_name, phone))
                print(f"Добавлен новый пользователь: {full_name} (@{username})")
            
            self.conn.commit()
        except Exception as e:
            print(f"Ошибка при добавлении/обновлении пользователя: {e}")
            self.conn.rollback()
            raise

    def get_user(self, user_id: int) -> dict:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        if result:
            return {
                'user_id': result[0],
                'username': result[1],
                'full_name': result[2],
                'phone': result[3],
                'created_at': result[4],
                'last_updated': result[5]
            }
        return None

    def get_user_by_username(self, username: str) -> dict:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        if result:
            return {
                'user_id': result[0],
                'username': result[1],
                'full_name': result[2],
                'phone': result[3],
                'created_at': result[4],
                'last_updated': result[5]
            }
        return None

    def get_all_users(self) -> list:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users')
        results = cursor.fetchall()
        return [
            {
                'user_id': row[0],
                'username': row[1],
                'full_name': row[2],
                'phone': row[3],
                'created_at': row[4],
                'last_updated': row[5]
            }
            for row in results
        ]

    def update_user_name(self, user_id: int, full_name: str):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET full_name = ? WHERE user_id = ?', (full_name, user_id))
        self.conn.commit()

    def update_user_phone(self, user_id: int, phone: str):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET phone = ? WHERE user_id = ?', (phone, user_id))
        self.conn.commit()

    def get_user_by_username_or_id(self, identifier: str) -> dict:
        """Поиск пользователя по username или ID"""
        if identifier.isdigit():
            return self.get_user(int(identifier))
        else:
            username = identifier.lstrip('@')  # Убираем @ если он есть
            return self.get_user_by_username(username)

    def block_user(self, user_id: int, blocked_by: int, reason: str = None):
        """Блокирует пользователя"""
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO blocked_users 
                (user_id, blocked_by, reason) 
                VALUES (?, ?, ?)
            ''', (user_id, blocked_by, reason))
            self.conn.commit()
            print(f"Пользователь {user_id} заблокирован администратором {blocked_by}")
        except Exception as e:
            print(f"Ошибка при блокировке пользователя: {e}")
            self.conn.rollback()
            raise

    def get_block_info(self, user_id: int) -> dict:
        """Получает информацию о блокировке пользователя"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT b.*, u.username, u.full_name 
            FROM blocked_users b 
            LEFT JOIN users u ON b.blocked_by = u.user_id 
            WHERE b.user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        if result:
            return {
                'user_id': result[0],
                'blocked_at': result[1],
                'blocked_by': result[2],
                'reason': result[3],
                'admin_username': result[4],
                'admin_name': result[5]
            }
        return None

    def get_blocked_users(self) -> list:
        """Получает список всех заблокированных пользователей с информацией"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT b.*, u.username, u.full_name, 
                   bu.username as blocked_username, bu.full_name as blocked_full_name
            FROM blocked_users b 
            LEFT JOIN users u ON b.blocked_by = u.user_id
            LEFT JOIN users bu ON b.user_id = bu.user_id
        ''')
        results = cursor.fetchall()
        return [
            {
                'user_id': row[0],
                'blocked_at': row[1],
                'blocked_by': row[2],
                'reason': row[3],
                'admin_username': row[4],
                'admin_name': row[5],
                'blocked_username': row[6],
                'blocked_full_name': row[7]
            }
            for row in results
        ]

    def unblock_user(self, user_id: int):
        """Разблокирует пользователя"""
        cursor = self.conn.cursor()
        try:
            cursor.execute('DELETE FROM blocked_users WHERE user_id = ?', (user_id,))
            self.conn.commit()
            print(f"Пользователь {user_id} разблокирован")
        except Exception as e:
            print(f"Ошибка при разблокировке пользователя: {e}")
            self.conn.rollback()
            raise

    def is_user_blocked(self, user_id: int) -> bool:
        """Проверяет, заблокирован ли пользователь"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT 1 FROM blocked_users WHERE user_id = ?', (user_id,))
        return cursor.fetchone() is not None

    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close() 