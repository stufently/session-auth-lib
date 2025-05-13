import asyncio
import logging
import os
import hashlib
from telethon.sessions import StringSession
from opentele.td import TDesktop
from opentele.api import API, UseCurrentSession
from dotenv import set_key
from opentele.exception import TFileNotFound

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Ключ для переменной окружения, где будет храниться строка сессии
TELEGRAM_SESSION_ENV_KEY = "TELEGRAM_SESSION"

class MyTelegramClient:
    def __init__(self, tdata_name):
        self.tdata_name = tdata_name
        self.client = None
        self.me = None

    async def authorize(self):
        tdata_path = "tdatas/tdata/"
        if not os.path.exists(tdata_path):
            logger.error("Путь tdata не найден: %s", tdata_path)
            return False

        try:
            logger.info("Чтение tdata из %s", tdata_path)
            tdesk = TDesktop(tdata_path)
            if not tdesk.accounts:
                logger.error("Аккаунты не найдены в tdata")
                return False
        except TFileNotFound as e:
            logger.error("TFileNotFound: %s", e)
            return False

        session_hash = hashlib.md5("no_proxy".encode()).hexdigest()
        session_file = f"sessions/{self.tdata_name}_{session_hash}.session"

        try:
            logger.info("Создание сессии из tdata: %s", session_file)
            os.makedirs(os.path.dirname(session_file), exist_ok=True)
            self.client = await tdesk.ToTelethon(
                session_file,
                UseCurrentSession,
                api=API.TelegramIOS.Generate(),
                auto_reconnect=True
            )
            await self.client.connect()
            self.me = await self.client.get_me()

            string_session = StringSession.save(self.client.session)
            set_key(".env", TELEGRAM_SESSION_ENV_KEY, string_session)

            os.remove(session_file)
            logger.info("Сессия успешно сохранена в .env")
            return True

        except Exception as e:
            logger.error("Ошибка получения сессии через tdata: %s", e)
            return False


async def authorize_client(tdata_name):
    client = MyTelegramClient(tdata_name)
    result = await client.authorize()
    if result:
        return client
    else:
        return None
