from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from .config import BOT_TOKEN
from .handlers import register_handlers

async def main():
    # Инициализация бота и диспетчера
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Регистрация обработчиков
    register_handlers(dp)

    # Запуск бота
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main()) 