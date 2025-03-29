from aiogram import types
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from .config import ADMIN_GROUP_ID
from .database import Database
from .bottom import admin_panel

class AdminStates(StatesGroup):
    waiting_for_broadcast = State()
    waiting_for_user_info = State()
    waiting_for_block_user = State()
    waiting_for_unblock_user = State()
    waiting_for_add_admin = State()
    waiting_for_remove_admin = State()
    waiting_for_block_reason = State()

class AdminPanel:
    def __init__(self):
        self.db = Database()

    def is_admin(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь администратором"""
        return self.db.is_admin(user_id) or self.is_main_admin(user_id)

    def is_main_admin(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь главным администратором"""
        return self.db.is_main_admin(user_id)

    async def handle_admin_command(self, message: types.Message, state: FSMContext):
        """Обработчик команды /admin"""
        if not self.is_admin(message.from_user.id):
            await message.reply("❌ У вас нет прав администратора.")
            return

        # Базовые кнопки для всех администраторов
        buttons = [
            [
                types.InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast"),
                types.InlineKeyboardButton(text="👤 Информация о пользователе", callback_data="admin_user_info")
            ],
            [
                types.InlineKeyboardButton(text="🚫 Заблокировать пользователя", callback_data="admin_block_user"),
                types.InlineKeyboardButton(text="✅ Разблокировать пользователя", callback_data="admin_unblock_user")
            ]
        ]

        # Дополнительные кнопки для главного администратора
        if self.is_main_admin(message.from_user.id):
            buttons.append([
                types.InlineKeyboardButton(text="➕ Добавить администратора", callback_data="admin_add_admin"),
                types.InlineKeyboardButton(text="➖ Удалить администратора", callback_data="admin_remove_admin")
            ])

        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.reply("Панель администратора:", reply_markup=keyboard)

    async def handle_admin_callback(self, callback: types.CallbackQuery, state: FSMContext):
        """Обработчик callback-запросов админ-панели"""
        if not self.is_admin(callback.from_user.id):
            await callback.answer("❌ У вас нет прав администратора.")
            return

        if callback.data == "admin_broadcast":
            await state.set_state(AdminStates.waiting_for_broadcast)
            await callback.message.reply("Введите сообщение для рассылки всем пользователям:")
        
        elif callback.data == "admin_user_info":
            await state.set_state(AdminStates.waiting_for_user_info)
            await callback.message.reply("Введите username или ID пользователя:")
        
        elif callback.data == "admin_block_user":
            await state.set_state(AdminStates.waiting_for_block_user)
            await callback.message.reply("Введите username или ID пользователя для блокировки:")
        
        elif callback.data == "admin_unblock_user":
            await state.set_state(AdminStates.waiting_for_unblock_user)
            await callback.message.reply("Введите username или ID пользователя для разблокировки:")
        
        elif callback.data == "admin_add_admin" and self.is_main_admin(callback.from_user.id):
            await state.set_state(AdminStates.waiting_for_add_admin)
            await callback.message.reply("Введите username или ID пользователя для назначения администратором:")
        
        elif callback.data == "admin_remove_admin" and self.is_main_admin(callback.from_user.id):
            await state.set_state(AdminStates.waiting_for_remove_admin)
            admins = self.db.get_all_admins()
            admin_list = "\n".join([
                f"{'👑' if admin['is_main_admin'] else '👤'} "
                f"ID: {admin['user_id']}"
                f"{f' (@{admin['username']})' if admin['username'] else ''}"
                for admin in admins
            ])
            await callback.message.reply(
                "Текущие администраторы:\n"
                f"{admin_list}\n\n"
                "Введите username или ID администратора для удаления:"
            )

        await callback.answer()

    async def handle_add_admin(self, message: types.Message, state: FSMContext):
        """Обработчик добавления администратора"""
        if not self.is_main_admin(message.from_user.id):
            await message.reply("❌ Только главный администратор может добавлять новых администраторов.")
            return

        # Ищем пользователя по username или ID
        user = self.db.get_user_by_username_or_id(message.text)
        
        if user:
            if self.db.is_admin(user['user_id']):
                await message.reply("❌ Этот пользователь уже является администратором.")
            else:
                self.db.add_admin(user['user_id'], user['username'])
                await message.reply(
                    f"✅ Пользователь {user['full_name']} (@{user['username']}) "
                    "успешно назначен администратором."
                )
        else:
            await message.reply(
                "❌ Пользователь не найден. Убедитесь, что пользователь зарегистрирован в боте "
                "и вы правильно указали его username или ID."
            )
        
        await state.clear()

    async def handle_remove_admin(self, message: types.Message, state: FSMContext):
        """Обработчик удаления администратора"""
        if not self.is_main_admin(message.from_user.id):
            await message.reply("❌ Только главный администратор может удалять администраторов.")
            return

        user_id = None
        if message.text.isdigit():
            user_id = int(message.text)
        else:
            username = message.text.lstrip('@')
            user = self.db.get_user_by_username(username)
            if user:
                user_id = user['user_id']

        if user_id:
            if self.db.is_main_admin(user_id):
                await message.reply("❌ Нельзя удалить главного администратора.")
            elif self.db.is_admin(user_id):
                self.db.remove_admin(user_id)
                await message.reply("✅ Администратор успешно удален.")
            else:
                await message.reply("❌ Этот пользователь не является администратором.")
        else:
            await message.reply("❌ Администратор не найден.")

        await state.clear()

    async def handle_broadcast(self, message: types.Message, state: FSMContext):
        """Обработчик рассылки"""
        if not self.is_admin(message.from_user.id):
            await message.reply("❌ У вас нет прав администратора.")
            return

        # Получаем всех пользователей
        users = self.db.get_all_users()
        
        # Исключаем создателя рассылки из списка получателей
        users = [user for user in users if user['user_id'] != message.from_user.id]
        
        if not users:
            await message.reply("❌ Нет пользователей для рассылки.")
            return

        # Отправляем сообщение каждому пользователю
        success_count = 0
        fail_count = 0
        
        # Отправляем сообщение о начале рассылки
        status_message = await message.reply("📤 Начинаю рассылку...")
        
        for user in users:
            try:
                if message.photo:
                    await message.bot.send_photo(
                        chat_id=user['user_id'],
                        photo=message.photo[-1].file_id,
                        caption=message.caption if message.caption else None
                    )
                elif message.video:
                    await message.bot.send_video(
                        chat_id=user['user_id'],
                        video=message.video.file_id,
                        caption=message.caption if message.caption else None
                    )
                else:
                    await message.bot.send_message(
                        chat_id=user['user_id'],
                        text=message.text
                    )
                success_count += 1
            except Exception as e:
                print(f"Ошибка при отправке сообщения пользователю {user['user_id']}: {e}")
                fail_count += 1
            
            # Обновляем статус каждые 10 сообщений
            if (success_count + fail_count) % 10 == 0:
                await status_message.edit_text(
                    f"📤 Рассылка в процессе...\n"
                    f"✅ Успешно: {success_count}\n"
                    f"❌ Ошибок: {fail_count}"
                )
        
        # Отправляем итоговый статус
        await status_message.edit_text(
            f"📤 Рассылка завершена!\n"
            f"✅ Успешно отправлено: {success_count}\n"
            f"❌ Ошибок: {fail_count}"
        )
        
        # Очищаем состояние
        await state.clear()

    async def handle_user_info(self, message: types.Message, state: FSMContext):
        """Обработчик получения информации о пользователе"""
        if not self.is_admin(message.from_user.id):
            return

        user_id = None
        if message.text.isdigit():
            user_id = int(message.text)
        else:
            username = message.text.lstrip('@')
            user = self.db.get_user_by_username(username)
            if user:
                user_id = user['user_id']

        if user_id:
            user_data = self.db.get_user(user_id)
            if user_data:
                admin_status = "👑 Главный администратор" if self.db.is_main_admin(user_id) else "👤 Администратор" if self.db.is_admin(user_id) else "👤 Пользователь"
                blocked_status = "🚫 Заблокирован" if self.db.is_user_blocked(user_id) else "✅ Активен"
                await message.reply(
                    f"Информация о пользователе:\n"
                    f"ID: {user_data['user_id']}\n"
                    f"Username: @{user_data['username']}\n"
                    f"Имя: {user_data['full_name']}\n"
                    f"Телефон: {user_data['phone']}\n"
                    f"Роль: {admin_status}\n"
                    f"Статус: {blocked_status}"
                )
            else:
                await message.reply("❌ Пользователь не найден в базе данных")
        else:
            await message.reply("❌ Пользователь не найден")

        await state.clear()

    async def handle_block_user(self, message: types.Message, state: FSMContext):
        """Обработчик блокировки пользователя"""
        if not self.is_admin(message.from_user.id):
            return

        # Ищем пользователя по username или ID
        user = self.db.get_user_by_username_or_id(message.text)
        
        if user:
            # Проверяем, не является ли пользователь администратором
            if self.is_admin(user['user_id']):
                await message.reply("❌ Нельзя заблокировать администратора.")
                return
            
            # Проверяем, не заблокирован ли уже пользователь
            if self.db.is_user_blocked(user['user_id']):
                await message.reply("❌ Этот пользователь уже заблокирован.")
                return
            
            else:
                # Запрашиваем причину блокировки
                await state.update_data(block_user_id=user['user_id'], block_user_info=user)
                await state.set_state(AdminStates.waiting_for_block_reason)
                await message.reply(
                    "Введите причину блокировки пользователя или нажмите 'Пропустить':",
                    reply_markup=types.ReplyKeyboardMarkup(
                        keyboard=[
                            [types.KeyboardButton(text="Пропустить")],
                            [types.KeyboardButton(text="🔄 Вернуться в панель администратора")]
                        ],
                        resize_keyboard=True
                    )
                )
        else:
            await message.reply(
                "❌ Пользователь не найден. Убедитесь, что пользователь зарегистрирован в боте "
                "и вы правильно указали его username или ID."
            )

    async def handle_block_reason(self, message: types.Message, state: FSMContext):
        """Обработчик причины блокировки"""
        if message.text == "🔄 Вернуться в панель администратора":
            await state.clear()
            await message.reply("Вы вернулись в панель администратора", reply_markup=admin_panel)
            return

        data = await state.get_data()
        user_id = data['block_user_id']
        user_info = data['block_user_info']
        reason = None if message.text == "Пропустить" else message.text

        try:
            self.db.block_user(user_id, message.from_user.id, reason)
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

    async def handle_unblock_user(self, message: types.Message, state: FSMContext):
        """Обработчик разблокировки пользователя"""
        if not self.is_admin(message.from_user.id):
            await message.reply("❌ У вас нет прав администратора.")
            return

        # Ищем пользователя по username или ID
        user = self.db.get_user_by_username_or_id(message.text)
        
        if user:
            user_id = user['user_id']
            if not self.db.is_user_blocked(user_id):
                await message.reply("❌ Этот пользователь не заблокирован.")
            else:
                try:
                    self.db.unblock_user(user_id)
                    await message.reply(
                        f"✅ Пользователь {user['full_name']} (@{user['username']}) разблокирован."
                    )
                except Exception as e:
                    await message.reply(f"❌ Произошла ошибка при разблокировке пользователя: {str(e)}")
        else:
            await message.reply(
                "❌ Пользователь не найден. Убедитесь, что пользователь зарегистрирован в боте "
                "и вы правильно указали его username или ID."
            )

        await state.clear()

    def is_user_blocked(self, user_id: int) -> bool:
        """Проверяет, заблокирован ли пользователь"""
        return self.db.is_user_blocked(user_id) 