import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_GROUP_ID = os.getenv('ADMIN_GROUP_ID')  # ID группы для администраторов
MAIN_ADMIN_ID = os.getenv('MAIN_ADMIN_ID')  # ID главного администратора 