from aiogram import types

start_button = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="Оставить заявку"), types.KeyboardButton(text="Связаться")],
        [types.KeyboardButton(text="Настройки")],
        [types.KeyboardButton(text="Полезные контакты")]
    ],
    resize_keyboard=True
)
submit_application = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="Отправить заявку"), types.KeyboardButton(text="поделиться предложением")],
        [types.KeyboardButton(text="Назад")]
    ],
    resize_keyboard=True
)
contact_us = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="Позвоните мне")],
        [types.KeyboardButton(text="Свяжитесь со мной в чат-боте")],
        [types.KeyboardButton(text="Назад")]
    ],
    resize_keyboard=True
)
get_settings = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="Поменять имя"), types.KeyboardButton(text="Поменять номер телефона")],
        [types.KeyboardButton(text="Назад")]
    ],
    resize_keyboard=True
)

inline_steps = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [types.InlineKeyboardButton(text="Пропустить", callback_data="skip")],
        [types.InlineKeyboardButton(text="Назад", callback_data="back")]
    ]
)

inline_back = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [types.InlineKeyboardButton(text="Назад", callback_data="back")]
    ]
)

confirm_phone = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [
            types.InlineKeyboardButton(text="Да, верный", callback_data="phone_correct"),
            types.InlineKeyboardButton(text="Указать другой", callback_data="phone_change")
        ]
    ]
)

end_chat = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [types.InlineKeyboardButton(text="Завершить диалог", callback_data="end_chat")]
    ]
)

reply_button = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [types.InlineKeyboardButton(text="Ответить", callback_data="reply")]
    ]
)


