from aiogram import types
from aiogram import Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, StateFilter
from .bottom import (
    start_button, admin_panel, admin_management, user_with_admin,
    submit_application, contact_us, get_settings, inline_steps,
    inline_back, confirm_phone, end_chat, reply_button
)
from .config import ADMIN_GROUP_ID
from .database import Database
from .admin import AdminPanel, AdminStates
import os
import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

class UserStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_application = State()
    waiting_for_contact = State()
    waiting_for_settings = State()
    waiting_for_contacts = State()
    # Состояния для подачи заявки
    waiting_for_address = State()
    waiting_for_photo = State()
    waiting_for_description = State()
    # Состояния для подтверждения телефона
    waiting_for_call_phone = State()
    # Состояние для чата с администратором
    in_admin_chat = State()
    # Состояния для ответа администратора
    waiting_for_reply = State()
    waiting_for_reply_text = State()
    # Состояния для настроек
    waiting_for_change_name = State()
    waiting_for_change_phone = State()

def register_handlers(dp: Dispatcher):
    # Инициализируем базу данных и админ-панель
    db = Database()
    admin_manager = AdminPanel()
    
    # Словарь для хранения последних сообщений от пользователей
    # Формат: {admin_msg_id: {'user_id': user_id, 'username': username}}
    last_messages = {}
    
    # Читаем содержимое файла contacts.txt
    with open(os.path.join(os.path.dirname(__file__), 'contacts.txt'), 'r', encoding='utf-8') as f:
        CONTACTS_TEXT = f.read().strip()

    # Словарь для определения предыдущего состояния
    previous_states = {
        UserStates.waiting_for_name: None,  # Возврат к старту
        UserStates.waiting_for_phone: UserStates.waiting_for_name,
        UserStates.waiting_for_application: None,  # Возврат в главное меню
        UserStates.waiting_for_address: UserStates.waiting_for_application,
        UserStates.waiting_for_photo: UserStates.waiting_for_address,
        UserStates.waiting_for_description: UserStates.waiting_for_photo,
        UserStates.waiting_for_contact: None,  # Возврат в главное меню
        UserStates.waiting_for_settings: None,  # Возврат в главное меню
        UserStates.waiting_for_contacts: None,  # Возврат в главное меню
        UserStates.waiting_for_call_phone: UserStates.waiting_for_contact,
        UserStates.waiting_for_change_name: UserStates.waiting_for_settings,
        UserStates.waiting_for_change_phone: UserStates.waiting_for_settings,
        UserStates.in_admin_chat: UserStates.waiting_for_contact,
    }

    async def handle_back_button(message: types.Message, state: FSMContext):
        current_state = await state.get_state()
        if current_state in previous_states:
            prev_state = previous_states[current_state]
            if prev_state is None:
                await state.clear()
                await message.reply("Выберите нужное действие:", reply_markup=start_button)
            else:
                await state.set_state(prev_state)
                if prev_state == UserStates.waiting_for_application:
                    await message.reply("Выберите категорию:", reply_markup=submit_application)
                elif prev_state == UserStates.waiting_for_settings:
                    await message.reply("Пожалуйста, выберите опцию:", reply_markup=get_settings)
                elif prev_state == UserStates.waiting_for_contact:
                    await message.reply("Выберите способ связи:", reply_markup=contact_us)
                elif prev_state == UserStates.waiting_for_address:
                    await message.reply(
                        "Шаг 1/3: Напишите адрес или примерную проблемную улицу, номер дома, подъезд, этаж и квартиру или пропустите этот пункт:",
                        reply_markup=inline_steps
                    )
                elif prev_state == UserStates.waiting_for_photo:
                    await message.reply(
                        "Шаг 2/3: Прикрепите фотографию или видео к своей заявке или пропустите этот пункт:",
                        reply_markup=inline_steps
                    )
                elif prev_state == UserStates.waiting_for_name:
                    await message.reply(
                        "Введите ваше имя и фамилию:",
                        reply_markup=types.ReplyKeyboardRemove()
                    )

    # Добавляем общий обработчик для кнопки "Назад"
    @dp.message(lambda message: message.text == "🔙Назад")
    async def universal_back_handler(message: types.Message, state: FSMContext):
        await handle_back_button(message, state)

    @dp.message(Command("start"))
    async def send_welcome(message: types.Message, state: FSMContext):
        # Проверяем, есть ли пользователь в базе
        user_data = db.get_user(message.from_user.id)
        
        if user_data:
            # Если пользователь уже зарегистрирован, сохраняем его данные в состояние
            await state.update_data(full_name=user_data['full_name'], phone=user_data['phone'])
            
            # Проверяем, является ли пользователь администратором
            if admin_manager.is_admin(message.from_user.id):
                await message.reply(
                    '✈️Добро пожаловать в главное меню чат-бота Управляющей компании "УЭР-ЮГ". Здесь Вы можете оставить заявку для управляющей компании или направить свое предложение по управлению домом. Просто воспользуйтесь кнопками меню, чтобы взаимодействовать с функциями бота:',
                    reply_markup=user_with_admin
                )
            else:
                await message.reply(
                    '✈️Добро пожаловать в главное меню чат-бота Управляющей компании "УЭР-ЮГ". Здесь Вы можете оставить заявку для управляющей компании или направить свое предложение по управлению домом. Просто воспользуйтесь кнопками меню, чтобы взаимодействовать с функциями бота:',
                    reply_markup=start_button
                )
        else:
            # Если пользователь новый, начинаем регистрацию
            await state.set_state(UserStates.waiting_for_name)
            await message.reply(
                "🌞Доброго времени суток, бот создан, чтобы обрабатывать заявки и обращения пользователей. Чтобы воспользоваться этим, пришлите для начала Ваше Имя и Фамилию",
                reply_markup=types.ReplyKeyboardRemove()
            )

    @dp.message(StateFilter(UserStates.waiting_for_name))
    async def handle_name(message: types.Message, state: FSMContext):
        # Проверяем формат имени (должно содержать хотя бы два слова)
        name_parts = message.text.strip().split()
        if len(name_parts) < 2:
            await message.reply(
                "⛔️📛Имя и Фамилия должны быть введены через один пробел, и должны быть написаны через кириллицу. Также должны быть заглавные буквы. Учтите формат и попробуйте снова:",
                reply_markup=types.ReplyKeyboardRemove()
            )
            return

        await state.update_data(full_name=message.text)
        await state.set_state(UserStates.waiting_for_phone)
        await message.reply(
            "Теперь отправьте Ваш номер телефона через +7 следующим сообщением:",
            reply_markup=types.ReplyKeyboardRemove()
        )

    @dp.message(StateFilter(UserStates.waiting_for_phone))
    async def handle_phone(message: types.Message, state: FSMContext):
        # Простая валидация номера телефона
        phone = message.text.strip()
        if not phone.startswith('+7') or len(phone) != 12 or not phone[1:].isdigit():
            await message.reply(
                "⛔️📛⛔️Номер телефона должен содержать 11 цифр и должен обязательно содержать в начале +7. Учтите формат и попробуйте снова:",
                reply_markup=types.ReplyKeyboardRemove()
            )
            return

        # Сохраняем данные пользователя
        data = await state.update_data(phone=phone)
        
        # Сохраняем пользователя в базу данных
        db.add_user(
            user_id=message.from_user.id,
            username=message.from_user.username,
            full_name=data['full_name'],
            phone=phone
        )
        
        await state.clear()  # Очищаем состояние для перехода в главное меню
        
        # Проверяем, является ли пользователь администратором
        if admin_manager.is_admin(message.from_user.id):
            await message.reply(reply_markup=user_with_admin)
        else:
            await message.reply(reply_markup=start_button)

    @dp.message(StateFilter(None))
    async def handle_main_menu(message: types.Message, state: FSMContext):
        if message.text == "🔑 Панель администратора":
            if admin_manager.is_admin(message.from_user.id):
                await message.reply("Панель администратора:", reply_markup=admin_panel)
            else:
                await message.reply("❌ У вас нет прав администратора.")
        
        elif message.text == "🔄 Вернуться в пользовательский режим":
            if admin_manager.is_admin(message.from_user.id):
                await message.reply("Пользовательский режим:", reply_markup=user_with_admin)
            else:
                await message.reply("Выберите действие:", reply_markup=start_button)
        
        elif message.text == "🔄 Вернуться в панель администратора":
            if admin_manager.is_admin(message.from_user.id):
                await message.reply("Панель администратора:", reply_markup=admin_panel)
            else:
                await message.reply("❌ У вас нет прав администратора.")
        
        elif message.text == "👥 Управление админами":
            if admin_manager.is_main_admin(message.from_user.id):
                await message.reply("Управление администраторами:", reply_markup=admin_management)
            else:
                await message.reply("❌ Только главный администратор имеет доступ к управлению администраторами.")
        
        elif message.text == "📋 Список пользователей":
            if admin_manager.is_admin(message.from_user.id):
                users = db.get_all_users()
                if not users:
                    await message.reply("В базе данных пока нет пользователей.")
                    return
                
                user_list = "📋 Список пользователей:\n\n"
                for user in users:
                    user_list += (
                        f"👤 ID: {user['user_id']}\n"
                        f"Имя: {user['full_name']}\n"
                        f"Телефон: {user['phone']}\n"
                        f"Username: @{user['username'] if user['username'] else 'Не указан'}\n"
                        f"{'🚫 Заблокирован' if admin_manager.is_user_blocked(user['user_id']) else '✅ Активен'}\n"
                        f"{'👑 Администратор' if admin_manager.is_admin(user['user_id']) else '👤 Пользователь'}\n"
                        f"{'⭐️ Главный администратор' if admin_manager.is_main_admin(user['user_id']) else ''}\n"
                        "-------------------\n"
                    )
                
                # Разбиваем длинное сообщение на части, если оно превышает лимит Telegram
                max_length = 4000
                for i in range(0, len(user_list), max_length):
                    chunk = user_list[i:i + max_length]
                    await message.reply(chunk)
            else:
                await message.reply("❌ У вас нет прав администратора.")
        
        elif message.text == "📢 Рассылка":
            if admin_manager.is_admin(message.from_user.id):
                await state.set_state(AdminStates.waiting_for_broadcast)
                await message.reply("Введите сообщение для рассылки всем пользователям:", reply_markup=types.ReplyKeyboardMarkup(
                    keyboard=[[types.KeyboardButton(text="🔄 Вернуться в панель администратора")]],
                    resize_keyboard=True
                ))
        
        elif message.text == "👤 Информация о пользователе":
            if admin_manager.is_admin(message.from_user.id):
                await state.set_state(AdminStates.waiting_for_user_info)
                await message.reply("Введите username или ID пользователя:", reply_markup=types.ReplyKeyboardMarkup(
                    keyboard=[[types.KeyboardButton(text="🔄 Вернуться в панель администратора")]],
                    resize_keyboard=True
                ))
        
        elif message.text == "🚫 Блокировка":
            if admin_manager.is_admin(message.from_user.id):
                await state.set_state(AdminStates.waiting_for_block_user)
                await message.reply("Введите username или ID пользователя для блокировки:", reply_markup=types.ReplyKeyboardMarkup(
                    keyboard=[[types.KeyboardButton(text="🔄 Вернуться в панель администратора")]],
                    resize_keyboard=True
                ))
        
        elif message.text == "✅ Разблокировка":
            if admin_manager.is_admin(message.from_user.id):
                await state.set_state(AdminStates.waiting_for_unblock_user)
                await message.reply("Введите username или ID пользователя для разблокировки:", reply_markup=types.ReplyKeyboardMarkup(
                    keyboard=[[types.KeyboardButton(text="🔄 Вернуться в панель администратора")]],
                    resize_keyboard=True
                ))
        
        elif message.text == "➕ Добавить администратора":
            if admin_manager.is_main_admin(message.from_user.id):
                await state.set_state(AdminStates.waiting_for_add_admin)
                await message.reply("Введите username или ID пользователя для назначения администратором:", reply_markup=types.ReplyKeyboardMarkup(
                    keyboard=[[types.KeyboardButton(text="🔄 Вернуться в панель администратора")]],
                    resize_keyboard=True
                ))
        
        elif message.text == "➖ Удалить администратора":
            if admin_manager.is_main_admin(message.from_user.id):
                await state.set_state(AdminStates.waiting_for_remove_admin)
                admins = db.get_all_admins()
                admin_list = "\n".join([
                    f"{'👑' if admin['is_main_admin'] else '👤'} "
                    f"ID: {admin['user_id']}"
                    f"{f' (@{admin['username']})' if admin['username'] else ''}"
                    for admin in admins
                ])
                await message.reply(
                    "Текущие администраторы:\n"
                    f"{admin_list}\n\n"
                    "Введите username или ID администратора для удаления:",
                    reply_markup=types.ReplyKeyboardMarkup(
                        keyboard=[[types.KeyboardButton(text="🔄 Вернуться в панель администратора")]],
                        resize_keyboard=True
                    )
                )
        
        elif message.text == "📛Оставить заявку":
            await state.set_state(UserStates.waiting_for_application)
            await message.reply("📛👇📛Выберите категорию, по которой Вы хотите оставить заявку в УК:", reply_markup=submit_application)
        elif message.text == "📞Связаться":
            await state.set_state(UserStates.waiting_for_contact)
            await message.reply("Выберите способ связи из нижеперечисленного списка:", reply_markup=contact_us)
        elif message.text == "⚙️Настройки":
            await state.set_state(UserStates.waiting_for_settings)
            await message.reply("Пожалуйста, выберите опцию:", reply_markup=get_settings)
        elif message.text == "☎️Полезные контакты":
            await state.set_state(UserStates.waiting_for_contacts)
            await message.reply(CONTACTS_TEXT, parse_mode="MarkdownV2")

    @dp.message(StateFilter(UserStates.waiting_for_application))
    async def handle_application(message: types.Message, state: FSMContext):
        if message.text == "📛Отправить заявку":
            # Получаем данные пользователя из базы
            user_data = db.get_user(message.from_user.id)
            if user_data:
                # Сохраняем данные пользователя в состояние
                await state.update_data(full_name=user_data['full_name'], phone=user_data['phone'])
            
            await state.set_state(UserStates.waiting_for_address)
            await message.answer(
                "Шаг 1/3: Напишите адрес или примерную проблемную улицу, номер дома, подъезд, этаж и квартиру или пропустите этот пункт:",
                reply_markup=types.ReplyKeyboardRemove(),
            )
            await message.answer(
                "Используйте кнопки ниже:",
                reply_markup=inline_steps
            )
        elif message.text == "💡Поделиться предложением":
            # Получаем данные пользователя из базы
            user_data = db.get_user(message.from_user.id)
            if user_data:
                # Сохраняем данные пользователя в состояние
                await state.update_data(
                    full_name=user_data['full_name'],
                    phone=user_data['phone'],
                    is_suggestion=True
                )
            await state.set_state(UserStates.waiting_for_description)
            await message.answer(
                "💡Распишите Ваше предложение в подробностях: (Добавьте фотографию, если есть)",
                reply_markup=types.ReplyKeyboardRemove()
            )
            await message.answer(
                "Используйте кнопки ниже:",
                reply_markup=inline_back
            )
        elif message.text == "🔙Назад":
            await state.clear()
            await message.answer(
                "Выберите действие:",
                reply_markup=submit_application
            )

    @dp.callback_query()
    async def handle_callback(callback: types.CallbackQuery, state: FSMContext):
        current_state = await state.get_state()
        
        if callback.data == "back":
            data = await state.get_data()
            # Если это предложение, возвращаемся в главное меню
            if data.get('is_suggestion'):
                await state.clear()
                await callback.message.delete()
                await callback.message.answer(
                    "Выберите действие:",
                    reply_markup=start_button
                )
                return
                
            if current_state == UserStates.waiting_for_call_phone:
                await state.set_state(UserStates.waiting_for_contact)
                await callback.message.delete()
                await callback.message.answer(
                    "Выберите способ связи:",
                    reply_markup=contact_us
                )
            elif current_state in previous_states:
                prev_state = previous_states[current_state]
                if prev_state is None:
                    # Возвращаемся в главное меню
                    await state.clear()
                    await callback.message.delete()
                    await callback.message.answer(
                        "Выберите действие:",
                        reply_markup=start_button
                    )
                else:
                    await state.set_state(prev_state)
                    if prev_state == UserStates.waiting_for_application:
                        await callback.message.delete()
                        await callback.message.answer(
                            "Выберите категорию:",
                            reply_markup=submit_application
                        )
                    elif prev_state == UserStates.waiting_for_address:
                        await callback.message.delete()
                        await callback.message.answer(
                            "Шаг 1/3: Напишите адрес или примерную проблемную улицу, номер дома, подъезд, этаж и квартиру или пропустите этот пункт:",
                            reply_markup=types.ReplyKeyboardRemove()
                        )
                        await callback.message.answer(
                            "Используйте кнопки ниже:",
                            reply_markup=inline_steps
                        )
                    elif prev_state == UserStates.waiting_for_photo:
                        await callback.message.delete()
                        await callback.message.answer(
                            "Шаг 2/3: Прикрепите фотографию или видео к своей заявке или пропустите этот пункт:",
                            reply_markup=types.ReplyKeyboardRemove()
                        )
                        await callback.message.answer(
                            "Используйте кнопки ниже:",
                            reply_markup=inline_steps
                        )
                    elif prev_state == UserStates.waiting_for_description:
                        await callback.message.delete()
                        await callback.message.answer(
                            "Шаг 3/3: Напишите причину обращения в подробностях:",
                            reply_markup=types.ReplyKeyboardRemove()
                        )
                        await callback.message.answer(
                            "Используйте кнопки ниже:",
                            reply_markup=inline_back
                        )
        
        elif callback.data == "skip":
            if current_state == UserStates.waiting_for_address:
                await state.update_data(address="Не указан")
                await state.set_state(UserStates.waiting_for_photo)
                await callback.message.delete()
                await callback.message.answer(
                    "Шаг 2/3: Прикрепите фотографию или видео к своей заявке или пропустите этот пункт:",
                    reply_markup=types.ReplyKeyboardRemove()
                )
                await callback.message.answer(
                    "Используйте кнопки ниже:",
                    reply_markup=inline_steps
                )
            elif current_state == UserStates.waiting_for_photo:
                await state.update_data(media_type=None, media_id=None)
                await state.set_state(UserStates.waiting_for_description)
                await callback.message.delete()
                await callback.message.answer(
                    "Шаг 3/3: Напишите причину обращения в подробностях:",
                    reply_markup=types.ReplyKeyboardRemove()
                )
                await callback.message.answer(
                    "Используйте кнопки ниже:",
                    reply_markup=inline_back
                )
        
        elif callback.data == "submit":
            await state.set_state(UserStates.waiting_for_address)
            await callback.message.edit_text(
                "Шаг 1/3: Напишите адрес или примерную проблемную улицу, номер дома, подъезд, этаж и квартиру или пропустите этот пункт:",
                reply_markup=inline_steps
            )
        
        elif callback.data == "suggestion":
            await state.set_state(UserStates.waiting_for_description)
            await callback.message.edit_text(
                "💡Распишите Ваше предложение в подробностях: (Добавьте фотографию, если есть)",
                reply_markup=inline_back
            )
            
        elif callback.data == "phone_correct":
            # Получаем данные пользователя из базы
            user_data = db.get_user(callback.from_user.id)
            # Отправляем сообщение в админ группу
            admin_message = (
                "📞 Запрос на звонок:\n"
                f"Имя: {user_data['full_name']}\n"
                f"Телефон: {user_data['phone']}\n"
                f"Username: @{callback.from_user.username}"
            )
            await callback.bot.send_message(chat_id=ADMIN_GROUP_ID, text=admin_message)
            # Отвечаем пользователю
            await callback.message.edit_text(
                "✅Отлично! Наш диспетчер перезвонит Вам в ближайшее время."
            )
            await callback.message.answer("Выберите нужное действие:", reply_markup=start_button)
            await state.clear()
        
        elif callback.data in ["phone_change"]:
            if callback.data == "phone_change":
                await callback.message.edit_text(
                    "Пожалуйста, введите ваш актуальный номер телефона в формате +7XXXXXXXXXX:"
                )
                await state.set_state(UserStates.waiting_for_call_phone)
        
        elif callback.data == "reply":
            # Получаем информацию о пользователе из сохраненных данных
            user_info = last_messages.get(callback.message.message_id)
            if user_info:
                await state.set_state(UserStates.waiting_for_reply_text)
                await state.update_data(
                    reply_to_user_id=user_info['user_id'],
                    reply_to_full_name=user_info['full_name']
                )
                await callback.message.reply(
                    f"Введите ответ для пользователя {user_info['full_name']}:",
                    reply_markup=types.ReplyKeyboardMarkup(
                        keyboard=[[types.KeyboardButton(text="🔄 Вернуться в панель администратора")]],
                        resize_keyboard=True
                    )
                )
            else:
                await callback.answer("❌ Ошибка: информация о пользователе не найдена")
        
        elif callback.data == "end_chat":
            if current_state == UserStates.in_admin_chat:
                await state.clear()
                await callback.message.delete()  # Удаляем сообщение с inline кнопками
                await callback.message.answer(
                    "✅ Диалог завершен. Выберите нужное действие:",
                    reply_markup=start_button
                )
            else:
                await callback.answer("❌ Ошибка: диалог уже завершен")
        
        await callback.answer()

    @dp.message(StateFilter(UserStates.waiting_for_address))
    async def handle_address(message: types.Message, state: FSMContext):
        if message.text == "🔙Назад":
            await state.set_state(UserStates.waiting_for_application)
            await message.answer("Выберите категорию:", reply_markup=submit_application)
            return
            
        # Сохраняем адрес в данных состояния
        await state.update_data(address=message.text)
        await state.set_state(UserStates.waiting_for_photo)
        await message.answer(
            "Шаг 2/3: Прикрепите фотографию или видео к своей заявке или пропустите этот пункт:",
            reply_markup=inline_steps
        )

    @dp.message(StateFilter(UserStates.waiting_for_photo))
    async def handle_photo(message: types.Message, state: FSMContext):
        if message.text == "🔙Назад":
            await state.set_state(UserStates.waiting_for_address)
            await message.answer(
                "Шаг 1/3: Напишите адрес или примерную проблемную улицу, номер дома, подъезд, этаж и квартиру или пропустите этот пункт:",
                reply_markup=inline_steps
            )
            return
            
        if message.photo or message.video:
            # Сохраняем медиафайл в данных состояния
            media_type = "photo" if message.photo else "video"
            media_id = message.photo[-1].file_id if message.photo else message.video.file_id
            await state.update_data(media_type=media_type, media_id=media_id)
            await state.set_state(UserStates.waiting_for_description)
            await message.answer(
                "Шаг 3/3: Напишите причину обращения в подробностях:",
                reply_markup=inline_back
            )
        else:
            await message.answer(
                "❌В данном пункте нужно обязательно отправить фотографию или видео в виде медиа-сообщения. Попробуйте еще раз.",
                reply_markup=inline_steps
            )

    @dp.message(StateFilter(UserStates.waiting_for_description))
    async def handle_description(message: types.Message, state: FSMContext):
        if message.text == "🔙Назад":
            await state.set_state(UserStates.waiting_for_photo)
            await message.answer(
                "Шаг 2/3: Прикрепите фотографию или видео к своей заявке или пропустите этот пункт:",
                reply_markup=inline_steps
            )
            return

        # Сохраняем описание в данных состояния
        await state.update_data(description=message.text)
        
        # Получаем все данные состояния
        data = await state.get_data()
        
        # Получаем данные пользователя из базы
        user_data = db.get_user(message.from_user.id)
        
        if user_data:
            # Формируем сообщение для отправки администратору
            admin_message = (
                f"📝 Новая заявка!\n\n"
                f"👤 От: {user_data['full_name']}\n"
                f"📞 Телефон: {user_data['phone']}\n"
                f"📍 Адрес: {data.get('address', 'Не указан')}\n"
                f"📄 Описание: {data['description']}"
            )
            
            # Отправляем сообщение администратору
            if data.get('media_type') == 'photo':
                await message.bot.send_photo(
                    ADMIN_GROUP_ID,
                    data['media_id'],
                    caption=admin_message,
                    reply_markup=reply_button
                )
            elif data.get('media_type') == 'video':
                await message.bot.send_video(
                    ADMIN_GROUP_ID,
                    data['media_id'],
                    caption=admin_message,
                    reply_markup=reply_button
                )
            else:
                await message.bot.send_message(
                    ADMIN_GROUP_ID,
                    admin_message,
                    reply_markup=reply_button
                )
            
            # Отправляем подтверждение пользователю
            await message.answer(
                "✅ Ваша заявка успешно отправлена!\n"
                "Мы рассмотрим её в ближайшее время.\n\n"
                "Вы можете отправить еще одну заявку или вернуться в главное меню:",
                reply_markup=start_button
            )
            
            # Очищаем состояние
            await state.clear()
        else:
            await message.answer(
                "❌ Произошла ошибка при отправке заявки. Пожалуйста, попробуйте позже.",
                reply_markup=start_button
            )
            await state.clear()

    @dp.message(StateFilter(UserStates.waiting_for_contact))
    async def handle_contact(message: types.Message, state: FSMContext):
        if message.text == "📞Позвоните мне":
            # Получаем данные пользователя из базы
            user_data = db.get_user(message.from_user.id)
            if user_data:
                await state.set_state(UserStates.waiting_for_call_phone)
                await message.answer(
                    f"Это Ваш верный номер телефона {user_data['phone']}?",
                    reply_markup=confirm_phone
                )
        elif message.text == "📞Свяжитесь со мной в чат-боте":
            # Получаем данные пользователя из базы
            user_data = db.get_user(message.from_user.id)
            if user_data:
                await state.update_data(
                    full_name=user_data['full_name'],
                    phone=user_data['phone']
                )
                await state.set_state(UserStates.in_admin_chat)
                await message.answer(
                    "✅📞✅Добрый день! Я - диспетчер управляющей компании \"УЭР-ЮГ\", готов помочь Вам. "
                    "Напишите, пожалуйста, интересующий Вас вопрос и ожидайте нашего ответа\n\n"
                    "Для завершения диалога нажмите кнопку ниже:",
                    reply_markup=end_chat
                )

    @dp.message(StateFilter(UserStates.waiting_for_call_phone))
    async def handle_new_phone(message: types.Message, state: FSMContext):
        # Проверяем формат номера телефона
        phone = message.text.strip()
        if not phone.startswith('+7') or len(phone) != 12 or not phone[1:].isdigit():
            await message.reply(
                "❌ Номер телефона должен содержать 11 цифр и начинаться с +7. Попробуйте снова:",
                reply_markup=None
            )
            return

        # Отправляем сообщение в админ группу
        admin_message = (
            "📞 Запрос на звонок:\n"
            f"Имя: {(await state.get_data()).get('full_name')}\n"
            f"Телефон: {phone}\n"
            f"Username: @{message.from_user.username}"
        )
        await message.bot.send_message(chat_id=ADMIN_GROUP_ID, text=admin_message)
        
        # Обновляем номер телефона в базе данных
        db.update_user_phone(message.from_user.id, phone)
        
        # Отвечаем пользователю
        await message.reply(
            "✅ Ваш запрос на звонок принят. Мы свяжемся с вами в ближайшее время.",
            reply_markup=start_button
        )
        await state.clear()

    @dp.message(StateFilter(UserStates.waiting_for_settings))
    async def handle_settings(message: types.Message, state: FSMContext):
        if message.text == "🛠Поменять имя":
            await state.set_state(UserStates.waiting_for_change_name)
            await message.reply(
                "🛠Отправьте своё Имя и Фамилию, чтобы поменять настройки:",
                reply_markup=types.ReplyKeyboardMarkup(
                    keyboard=[[types.KeyboardButton(text="🔙Назад")]],
                    resize_keyboard=True
                )
            )
        elif message.text == "🛠Поменять номер телефона":
            await state.set_state(UserStates.waiting_for_change_phone)
            await message.reply(
                "🛠Отправьте свой номер телефона, чтобы поменять настройки:",
                reply_markup=types.ReplyKeyboardMarkup(
                    keyboard=[[types.KeyboardButton(text="🔙Назад")]],
                    resize_keyboard=True
                )
            )

    @dp.message(StateFilter(UserStates.waiting_for_change_name))
    async def handle_change_name(message: types.Message, state: FSMContext):
        # Проверяем формат имени (должно содержать хотя бы два слова)
        name_parts = message.text.strip().split()
        if len(name_parts) < 2:
            await message.reply(
                "❌ Имя и Фамилия должны быть введены через пробел. Попробуйте снова:",
                reply_markup=types.ReplyKeyboardMarkup(
                    keyboard=[[types.KeyboardButton(text="🔙Назад")]],
                    resize_keyboard=True
                )
            )
            return

        # Обновляем имя в базе данных
        db.update_user_name(message.from_user.id, message.text)
        
        # Отправляем подтверждение
        await message.reply(
            "✅ Настройки имени успешно применены!",
            reply_markup=start_button
        )
        await state.clear()

    @dp.message(StateFilter(UserStates.waiting_for_change_phone))
    async def handle_change_phone(message: types.Message, state: FSMContext):
        # Проверяем формат номера телефона
        phone = message.text.strip()
        if not phone.startswith('+7') or len(phone) != 12 or not phone[1:].isdigit():
            await message.reply(
                "❌ Номер телефона должен содержать 11 цифр и начинаться с +7. Попробуйте снова:",
                reply_markup=types.ReplyKeyboardMarkup(
                    keyboard=[[types.KeyboardButton(text="🔙Назад")]],
                    resize_keyboard=True
                )
            )
            return

        # Обновляем номер телефона в базе данных
        db.update_user_phone(message.from_user.id, phone)
        
        # Отправляем подтверждение
        await message.reply(
            "✅ Настройки номера успешно применены!",
            reply_markup=start_button
        )
        await state.clear()

    @dp.message(StateFilter(UserStates.waiting_for_contacts))
    async def handle_contacts(message: types.Message, state: FSMContext):
        if message.text == "🔙Назад":
            await state.clear()
            await message.reply("Выберите опцию:", reply_markup=start_button)

    @dp.message(StateFilter(UserStates.in_admin_chat))
    async def handle_admin_chat(message: types.Message, state: FSMContext):
        # Получаем данные пользователя
        data = await state.get_data()
        
        # Формируем сообщение для админов
        admin_message = (
            "💬 Новое сообщение в чате:\n\n"
            f"От: {data.get('full_name')}\n"
            f"Телефон: {data.get('phone')}\n"
            f"Username: @{message.from_user.username}\n"
            f"Сообщение: {message.text if message.text else ''}"
        )
        
        # Отправляем сообщение в админ группу и сохраняем его ID
        sent_message = None
        try:
            if message.photo:
                sent_message = await message.bot.send_photo(
                    chat_id=ADMIN_GROUP_ID,
                    photo=message.photo[-1].file_id,
                    caption=admin_message if message.caption else None,
                    reply_markup=reply_button
                )
            elif message.video:
                sent_message = await message.bot.send_video(
                    chat_id=ADMIN_GROUP_ID,
                    video=message.video.file_id,
                    caption=admin_message if message.caption else None,
                    reply_markup=reply_button
                )
            else:
                sent_message = await message.bot.send_message(
                    chat_id=ADMIN_GROUP_ID,
                    text=admin_message,
                    reply_markup=reply_button
                )
            
            # Сохраняем информацию о сообщении
            if sent_message:
                last_messages[sent_message.message_id] = {
                    'user_id': message.from_user.id,
                    'username': message.from_user.username,
                    'full_name': data.get('full_name')
                }
            
            # Отправляем подтверждение пользователю
            await message.reply(
                "✅ Ваше сообщение отправлено. Ожидайте ответа от диспетчера.",
                reply_markup=end_chat
            )
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {e}")
            await message.reply(
                "❌ Произошла ошибка при отправке сообщения. Пожалуйста, попробуйте позже.",
                reply_markup=end_chat
            )

    @dp.message(StateFilter(UserStates.waiting_for_reply_text))
    async def handle_reply_text(message: types.Message, state: FSMContext):
        # Получаем данные о пользователе
        data = await state.get_data()
        user_id = data.get('reply_to_user_id')
        user_full_name = data.get('reply_to_full_name')
        
        try:
            # Формируем ответ для пользователя
            response = (
                "👨‍💼 Ответ от диспетчера:\n\n"
                f"{message.text}"
            )
            
            # Отправляем ответ пользователю
            if message.photo:
                await message.bot.send_photo(
                    chat_id=user_id,
                    photo=message.photo[-1].file_id,
                    caption=response
                )
            elif message.video:
                await message.bot.send_video(
                    chat_id=user_id,
                    video=message.video.file_id,
                    caption=response
                )
            else:
                await message.bot.send_message(
                    chat_id=user_id,
                    text=response
                )
            
            # Подтверждаем отправку администратору
            await message.reply(
                f"✅ Ответ успешно отправлен пользователю {user_full_name}."
            )
            
            # Очищаем состояние
            await state.clear()
            
        except Exception as e:
            await message.reply(
                f"❌ Не удалось отправить ответ пользователю. "
                f"Возможно, пользователь заблокировал бота или произошла другая ошибка."
            )
            await state.clear()

    # Добавляем обработчики для админ-панели
    @dp.message(Command("admin"))
    async def admin_command(message: types.Message, state: FSMContext):
        """Обработчик команды /admin"""
        await admin_panel.handle_admin_command(message, state)

    @dp.callback_query(lambda c: c.data and c.data.startswith('admin_'))
    async def admin_callback(callback: types.CallbackQuery, state: FSMContext):
        """Обработчик callback-запросов админ-панели"""
        await admin_panel.handle_admin_callback(callback, state)

    @dp.message(StateFilter(AdminStates.waiting_for_broadcast))
    async def handle_broadcast(message: types.Message, state: FSMContext):
        if message.text == "🔄 Вернуться в панель администратора":
            await state.clear()
            await message.reply("Вы вернулись в панель администратора", reply_markup=admin_panel)
            return
        await admin_manager.handle_broadcast(message, state)

    @dp.message(StateFilter(AdminStates.waiting_for_user_info))
    async def handle_user_info(message: types.Message, state: FSMContext):
        if message.text == "🔄 Вернуться в панель администратора":
            await state.clear()
            await message.reply("Вы вернулись в панель администратора", reply_markup=admin_panel)
            return
        await admin_manager.handle_user_info(message, state)

    @dp.message(StateFilter(AdminStates.waiting_for_block_user))
    async def handle_block_user(message: types.Message, state: FSMContext):
        if message.text == "🔄 Вернуться в панель администратора":
            await state.clear()
            await message.reply("Вы вернулись в панель администратора", reply_markup=admin_panel)
            return
        await admin_manager.handle_block_user(message, state)

    @dp.message(StateFilter(AdminStates.waiting_for_unblock_user))
    async def handle_unblock_user(message: types.Message, state: FSMContext):
        if message.text == "🔄 Вернуться в панель администратора":
            await state.clear()
            await message.reply("Вы вернулись в панель администратора", reply_markup=admin_panel)
            return
        await admin_manager.handle_unblock_user(message, state)

    @dp.message(StateFilter(AdminStates.waiting_for_add_admin))
    async def handle_add_admin(message: types.Message, state: FSMContext):
        if message.text == "🔄 Вернуться в панель администратора":
            await state.clear()
            await message.reply("Вы вернулись в панель администратора", reply_markup=admin_panel)
            return
        await admin_manager.handle_add_admin(message, state)

    @dp.message(StateFilter(AdminStates.waiting_for_remove_admin))
    async def handle_remove_admin(message: types.Message, state: FSMContext):
        if message.text == "🔄 Вернуться в панель администратора":
            await state.clear()
            await message.reply("Вы вернулись в панель администратора", reply_markup=admin_panel)
            return
        await admin_manager.handle_remove_admin(message, state)

    @dp.message(AdminStates.waiting_for_block_reason)
    async def handle_block_reason(message: types.Message, state: FSMContext):
        if message.text == "🔄 Вернуться в панель администратора":
            await state.clear()
            await message.reply("Вы вернулись в панель администратора", reply_markup=admin_panel)
            return
            
        async with state.proxy() as data:
            user_id = data['block_user_id']
            user_info = data['block_user_info']
            reason = None if message.text == "Пропустить" else message.text

        try:
            admin_manager.block_user(user_id, message.from_user.id, reason)
            response = f"✅ Пользователь {user_info['full_name']} (@{user_info['username']}) заблокирован."
            if reason:
                response += f"\nПричина: {reason}"
            await message.reply(response, reply_markup=admin_panel)
        except Exception as e:
            await message.reply(
                f"❌ Произошла ошибка при блокировке пользователя: {str(e)}",
                reply_markup=admin_panel
            )

        await state.clear()

    # Добавляем проверку на блокировку пользователя во все обработчики сообщений
    @dp.message()
    async def check_user_blocked(message: types.Message, state: FSMContext):
        if db.is_user_blocked(message.from_user.id):
            await message.reply("🚫 Вы заблокированы администратором.")
            return True
        return False

            
            
