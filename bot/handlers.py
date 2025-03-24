from aiogram import types
from aiogram import Dispatcher
from aiogram.filters import Command

def register_handlers(dp: Dispatcher):
    @dp.message(Command("start"))
    async def send_welcome(message: types.Message):
        reply_markup = types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="Оставить заявку"), types.KeyboardButton(text="Связаться")],
                [types.KeyboardButton(text="Настройки")],
                [types.KeyboardButton(text="Полезные контакты")]
            ],
            resize_keyboard=True
        )
        await message.reply("Привет! Я ваш новый бот. 👋", reply_markup=reply_markup)

    def get_request():
        return types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="Оставить заявку"), types.KeyboardButton(text="Поделиться предложением")],
                [types.KeyboardButton(text="Назад")]
            ],
            resize_keyboard=True
        )
    def contact_request():
        return types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="Позвоните мне")],
                [types.KeyboardButton(text="Свяжитесь со мной в чат-боте")],
                [types.KeyboardButton(text="Назад")]
            ],
            resize_keyboard=True
        )
    def get_settings():
        return types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="Поменять имя"), types.KeyboardButton(text="Сменить номер телефона")],
                [types.KeyboardButton(text="Назад")]
            ],
            resize_keyboard=True
        )
    @dp.message()
    async def handle_buttons(message: types.Message):
        if message.text == "Оставить заявку":
            await message.reply("Выберите категорию, по которой хотите оставить заявку в УК:", reply_markup=get_request())
        elif message.text == "Связаться":
            await message.reply("Выберите способ связи из нижеперечисленного списка:", reply_markup=contact_request())
        elif message.text == "Настройки":
            await message.reply("Пожалуйста, выберите опцию:")
