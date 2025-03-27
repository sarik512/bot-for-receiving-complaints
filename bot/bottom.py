from aiogram import types

# Пользовательская панель
start_button = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="📛Оставить заявку"), types.KeyboardButton(text="📞Связаться")],
        [types.KeyboardButton(text="⚙️Настройки")],
        [types.KeyboardButton(text="☎️Полезные контакты")]
    ],
    resize_keyboard=True
)

# Админская панель
admin_panel = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="📢 Рассылка"), types.KeyboardButton(text="👤 Информация о пользователе")],
        [types.KeyboardButton(text="🚫 Блокировка"), types.KeyboardButton(text="✅ Разблокировка")],
        [types.KeyboardButton(text="👥 Управление админами")],
        [types.KeyboardButton(text="📋 Список пользователей")],
        [types.KeyboardButton(text="🔄 Вернуться в пользовательский режим")]
    ],
    resize_keyboard=True
)

# Кнопки для управления админами (только для главного админа)
admin_management = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="➕ Добавить администратора"), types.KeyboardButton(text="➖ Удалить администратора")],
        [types.KeyboardButton(text="🔄 Вернуться в панель администратора")]
    ],
    resize_keyboard=True
)

# Пользовательская панель с кнопкой админа
user_with_admin = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="📛Оставить заявку"), types.KeyboardButton(text="📞Связаться")],
        [types.KeyboardButton(text="⚙️Настройки")],
        [types.KeyboardButton(text="☎️Полезные контакты")],
        [types.KeyboardButton(text="🔑 Панель администратора")]
    ],
    resize_keyboard=True
)

submit_application = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="📛Отправить заявку"), types.KeyboardButton(text="💡Поделиться предложением")],
        [types.KeyboardButton(text="🔙Назад")]
    ],
    resize_keyboard=True
)

contact_us = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="📞Позвоните мне")],
        [types.KeyboardButton(text="📞Свяжитесь со мной в чат-боте")],
        [types.KeyboardButton(text="🔙Назад")]
    ],
    resize_keyboard=True
)

get_settings = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="🛠Поменять имя"), types.KeyboardButton(text="🛠Поменять номер телефона")],
        [types.KeyboardButton(text="🔙Назад")]
    ],
    resize_keyboard=True
)

inline_steps = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [types.InlineKeyboardButton(text="Пропустить", callback_data="skip")],
        [types.InlineKeyboardButton(text="🔙Назад", callback_data="back")]
    ]
)

inline_back = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙Назад", callback_data="back")]
    ]
)

# Клавиатура для подтверждения телефона
confirm_phone = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [
            types.InlineKeyboardButton(text="✅Да, верно", callback_data="phone_correct"),
            types.InlineKeyboardButton(text="❌Нет, изменить", callback_data="phone_change")
        ]
    ]
)

end_chat = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [types.InlineKeyboardButton(text="❌📞Завершить диалог", callback_data="end_chat")]
    ]
)

reply_button = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [types.InlineKeyboardButton(text="Ответить", callback_data="reply")]
    ]
)


