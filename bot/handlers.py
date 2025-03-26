from aiogram import types
from aiogram import Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, StateFilter
from .bottom import *
from .config import ADMIN_GROUP_ID
from .database import Database
import os
import re

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
    # Инициализируем базу данных
    db = Database()
    
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
    @dp.message(lambda message: message.text == "Назад")
    async def universal_back_handler(message: types.Message, state: FSMContext):
        await handle_back_button(message, state)

    @dp.message(Command("start"))
    async def send_welcome(message: types.Message, state: FSMContext):
        # Проверяем, есть ли пользователь в базе
        user_data = db.get_user(message.from_user.id)
        
        if user_data:
            # Если пользователь уже зарегистрирован, сохраняем его данные в состояние
            await state.update_data(full_name=user_data['full_name'], phone=user_data['phone'])
            await message.reply(
                f"С возвращением, {user_data['full_name']}! 👋\n"
                "Выберите нужное действие:",
                reply_markup=start_button
            )
        else:
            # Если пользователь новый, начинаем регистрацию
            await state.set_state(UserStates.waiting_for_name)
            await message.reply(
                "Добрый день! Для начала работы с ботом, пожалуйста, представьтесь.\n"
                "Введите ваше имя и фамилию:",
                reply_markup=types.ReplyKeyboardRemove()
            )

    @dp.message(StateFilter(UserStates.waiting_for_name))
    async def handle_name(message: types.Message, state: FSMContext):
        # Проверяем формат имени (должно содержать хотя бы два слова)
        name_parts = message.text.strip().split()
        if len(name_parts) < 2:
            await message.reply(
                "❌ Имя и Фамилия должны быть введены через пробел. Попробуйте снова:",
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
                "❌ Номер телефона должен содержать 11 цифр и должен обязательно содержать в начале +7. Укажите формат и попробуйте снова:",
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
        
        # Отправляем приветственное сообщение с главным меню
        await message.reply(
            "✅ Регистрация успешно завершена!\n"
            "Теперь вы можете пользоваться всеми функциями бота.",
            reply_markup=start_button
        )

    @dp.message(StateFilter(None))
    async def handle_main_menu(message: types.Message, state: FSMContext):
        if message.text == "Оставить заявку":
            await state.set_state(UserStates.waiting_for_application)
            await message.reply("Выберите категорию, по которой хотите оставить заявку в УК:", reply_markup=submit_application)
        elif message.text == "Связаться":
            await state.set_state(UserStates.waiting_for_contact)
            await message.reply("Выберите способ связи из нижеперечисленного списка:", reply_markup=contact_us)
        elif message.text == "Настройки":
            await state.set_state(UserStates.waiting_for_settings)
            await message.reply("Пожалуйста, выберите опцию:", reply_markup=get_settings)
        elif message.text == "Полезные контакты":
            await state.set_state(UserStates.waiting_for_contacts)
            await message.reply(CONTACTS_TEXT, parse_mode="MarkdownV2")

    @dp.message(StateFilter(UserStates.waiting_for_application))
    async def handle_application(message: types.Message, state: FSMContext):
        if message.text == "Отправить заявку":
            # Получаем данные пользователя из базы
            user_data = db.get_user(message.from_user.id)
            if user_data:
                # Сохраняем данные пользователя в состояние
                await state.update_data(full_name=user_data['full_name'], phone=user_data['phone'])
            
            await state.set_state(UserStates.waiting_for_address)
            await message.reply(
                "Шаг 1/3: Напишите адрес или примерную проблемную улицу, номер дома, подъезд, этаж и квартиру или пропустите этот пункт:",
                reply_markup=inline_steps
            )
        elif message.text == "поделиться предложением":
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
            await message.reply("💡Распишите Ваше предложение в подробностях: (Добавьте фотографию, если есть)", reply_markup=inline_back)

    @dp.callback_query()
    async def handle_callback(callback: types.CallbackQuery, state: FSMContext):
        current_state = await state.get_state()
        
        if callback.data == "back":
            if current_state == UserStates.waiting_for_address:
                await state.set_state(UserStates.waiting_for_application)
                await callback.message.edit_text("Выберите категорию:", reply_markup=submit_application)
            elif current_state == UserStates.waiting_for_photo:
                await state.set_state(UserStates.waiting_for_address)
                await callback.message.edit_text(
                    "Шаг 1/3: Напишите адрес или примерную проблемную улицу, номер дома, подъезд, этаж и квартиру или пропустите этот пункт:",
                    reply_markup=inline_steps
                )
            elif current_state == UserStates.waiting_for_description:
                await state.set_state(UserStates.waiting_for_photo)
                await callback.message.edit_text(
                    "Шаг 2/3: Прикрепите фотографию или видео к своей заявке или пропустите этот пункт:",
                    reply_markup=inline_steps
                )
        
        elif callback.data == "skip":
            if current_state == UserStates.waiting_for_address:
                await state.update_data(address="Не указан")
                await state.set_state(UserStates.waiting_for_photo)
                await callback.message.edit_text(
                    "Шаг 2/3: Прикрепите фотографию или видео к своей заявке или пропустите этот пункт:",
                    reply_markup=inline_steps
                )
            elif current_state == UserStates.waiting_for_photo:
                await state.update_data(media_type=None, media_id=None)
                await state.set_state(UserStates.waiting_for_description)
                await callback.message.edit_text(
                    "Шаг 3/3: Напишите причину обращения в подробностях:",
                    reply_markup=inline_back
                )
        
        elif callback.data == "reply":
            # Проверяем, что сообщение из админ-группы
            if str(callback.message.chat.id) != str(ADMIN_GROUP_ID):
                return
                
            # Получаем информацию о сообщении
            message_id = callback.message.message_id
            if message_id not in last_messages:
                await callback.answer("❌ Не удалось найти пользователя для ответа.")
                return
                
            user_info = last_messages[message_id]
            
            # Сохраняем информацию о пользователе в состояние
            await state.update_data(
                reply_to_user_id=user_info['user_id'],
                reply_to_username=user_info['username'],
                reply_to_full_name=user_info['full_name']
            )
            
            # Устанавливаем состояние ожидания ответа
            await state.set_state(UserStates.waiting_for_reply_text)
            
            # Отправляем сообщение администратору
            await callback.message.reply(
                f"Введите ответ для пользователя {user_info['full_name']} (@{user_info['username']}):"
            )
        
        elif callback.data in ["phone_correct", "phone_change", "end_chat"]:
            if callback.data == "phone_correct":
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
                    "✅ Ваш запрос на звонок принят. Мы свяжемся с вами в ближайшее время.",
                    reply_markup=None
                )
                await state.clear()
            elif callback.data == "phone_change":
                await callback.message.edit_text(
                    "Пожалуйста, введите ваш актуальный номер телефона в формате +7XXXXXXXXXX:",
                    reply_markup=None
                )
            elif callback.data == "end_chat":
                await state.clear()
                await callback.message.edit_text(
                    "Чат завершен. Спасибо за обращение!"
                )
                await callback.message.answer("Выберите нужное действие:", reply_markup=start_button)
        
        await callback.answer()

    @dp.message(StateFilter(UserStates.waiting_for_address))
    async def handle_address(message: types.Message, state: FSMContext):
        # Сохраняем адрес в данных состояния
        await state.update_data(address=message.text)
        await state.set_state(UserStates.waiting_for_photo)
        await message.reply(
            "Шаг 2/3: Прикрепите фотографию или видео к своей заявке или пропустите этот пункт:",
            reply_markup=inline_steps
        )

    @dp.message(StateFilter(UserStates.waiting_for_photo))
    async def handle_photo(message: types.Message, state: FSMContext):
        if message.photo or message.video:
            # Сохраняем медиафайл в данных состояния
            media_type = "photo" if message.photo else "video"
            media_id = message.photo[-1].file_id if message.photo else message.video.file_id
            await state.update_data(media_type=media_type, media_id=media_id)
            await state.set_state(UserStates.waiting_for_description)
            await message.reply(
                "Шаг 3/3: Напишите причину обращения в подробностях:",
                reply_markup=inline_back
            )
        else:
            await message.reply(
                "❌В данном пункте нужно обязательно отправить фотографию или видео в виде медиа-сообщения. Попробуйте еще раз.",
                reply_markup=inline_steps
            )

    @dp.message(StateFilter(UserStates.waiting_for_description))
    async def handle_description(message: types.Message, state: FSMContext):
        # Получаем все данные заявки и пользователя
        data = await state.get_data()
        
        # Определяем тип сообщения (жалоба или предложение)
        message_type = "предложение" if data.get('is_suggestion') else "жалоба"
        
        # Формируем сообщение для пользователя
        user_response = f"✅ Ваше {message_type} отправлено администрации. Спасибо за обращение!"
        
        # Формируем сообщение для группы администраторов
        admin_response = (
            f"❗️Поступило новое {message_type}:\n\n"
            f"username: @{message.from_user.username}\n"
            f"Имя и Фамилия: {data.get('full_name')}\n"
            f"Номер телефона: {data.get('phone')}\n"
        )
        
        if not data.get('is_suggestion'):
            admin_response += f"Адрес: {data.get('address', 'Не указан')}\n"
        
        admin_response += f"Содержание: {message.text}"

        # Отправляем сообщение в группу администраторов
        if data.get('media_type') == 'photo':
            await message.bot.send_photo(
                chat_id=ADMIN_GROUP_ID,
                photo=data['media_id'],
                caption=admin_response
            )
        elif data.get('media_type') == 'video':
            await message.bot.send_video(
                chat_id=ADMIN_GROUP_ID,
                video=data['media_id'],
                caption=admin_response
            )
        else:
            await message.bot.send_message(
                chat_id=ADMIN_GROUP_ID,
                text=admin_response
            )
        
        # Отправляем подтверждение пользователю
        await message.reply(user_response, reply_markup=start_button)
        
        # Очищаем состояние
        await state.clear()

    @dp.message(StateFilter(UserStates.waiting_for_contact))
    async def handle_contact(message: types.Message, state: FSMContext):
        if message.text == "Позвоните мне":
            # Получаем данные пользователя из базы
            user_data = db.get_user(message.from_user.id)
            if user_data:
                await state.set_state(UserStates.waiting_for_call_phone)
                await message.reply(
                    f"Это Ваш верный номер телефона {user_data['phone']}? Если да, нажмите соответствующую кнопку, если нет, впишите свой актуальный номер телефона здесь",
                    reply_markup=confirm_phone
                )
        elif message.text == "Свяжитесь со мной в чат-боте":
            # Получаем данные пользователя из базы
            user_data = db.get_user(message.from_user.id)
            if user_data:
                await state.update_data(
                    full_name=user_data['full_name'],
                    phone=user_data['phone']
                )
                await state.set_state(UserStates.in_admin_chat)
                await message.reply(
                    "✅📞✅Добрый день! Я - диспетчер управляющей компании \"УЭР-ЮГ\", готов помочь Вам. "
                    "Напишите, пожалуйста, интересующий Вас вопрос и ожидайте нашего ответа",
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

        # Обновляем номер телефона в базе данных
        db.update_user_phone(message.from_user.id, phone)
        
        # Отправляем сообщение в админ группу
        admin_message = (
            "📞 Запрос на звонок:\n"
            f"Имя: {(await state.get_data()).get('full_name')}\n"
            f"Телефон: {phone}\n"
            f"Username: @{message.from_user.username}"
        )
        await message.bot.send_message(chat_id=ADMIN_GROUP_ID, text=admin_message)
        
        # Отвечаем пользователю
        await message.reply(
            "✅ Ваш запрос на звонок принят. Мы свяжемся с вами в ближайшее время.",
            reply_markup=start_button
        )
        await state.clear()

    @dp.message(StateFilter(UserStates.waiting_for_settings))
    async def handle_settings(message: types.Message, state: FSMContext):
        if message.text == "Поменять имя":
            await state.set_state(UserStates.waiting_for_change_name)
            await message.reply(
                "Отправьте своё Имя и Фамилию, чтобы поменять настройки:",
                reply_markup=types.ReplyKeyboardMarkup(
                    keyboard=[[types.KeyboardButton(text="Назад")]],
                    resize_keyboard=True
                )
            )
        elif message.text == "Поменять номер телефона":
            await state.set_state(UserStates.waiting_for_change_phone)
            await message.reply(
                "Отправьте свой номер телефона, чтобы поменять настройки:",
                reply_markup=types.ReplyKeyboardMarkup(
                    keyboard=[[types.KeyboardButton(text="Назад")]],
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
                    keyboard=[[types.KeyboardButton(text="Назад")]],
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
                    keyboard=[[types.KeyboardButton(text="Назад")]],
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
        if message.text == "Назад":
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
            f"Сообщение: {message.text}"
        )
        
        # Отправляем сообщение в админ группу и сохраняем его ID
        sent_message = None
        if message.photo:
            sent_message = await message.bot.send_photo(
                chat_id=ADMIN_GROUP_ID,
                photo=message.photo[-1].file_id,
                caption=admin_message,
                reply_markup=reply_button
            )
        elif message.video:
            sent_message = await message.bot.send_video(
                chat_id=ADMIN_GROUP_ID,
                video=message.video.file_id,
                caption=admin_message,
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

            
            
