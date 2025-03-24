# Telegram Bot

Простой Telegram бот, созданный с использованием aiogram.

## Структура проекта

```
├── bot/
│   ├── __init__.py
│   ├── config.py
│   ├── handlers.py
│   └── main.py
├── .env
├── requirements.txt
├── README.md
└── run.py
```

## Установка

1. Клонируйте репозиторий
2. Установите зависимости:
```bash
pip install -r requirements.txt
```
3. Создайте файл .env и добавьте в него ваш токен бота:
```
BOT_TOKEN=your_bot_token_here
```

## Запуск

```bash
python run.py
```

## Доступные команды

- /start - Начать работу с ботом
- /help - Показать список доступных команд 