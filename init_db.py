from bot.database import Database

def init_database():
    print("Инициализация базы данных...")
    db = Database()
    print("База данных успешно инициализирована!")

if __name__ == "__main__":
    init_database() 