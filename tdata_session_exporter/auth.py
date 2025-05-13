import asyncio
import logging
import os
import hashlib
import json
from pathlib import Path
from telethon.sessions import StringSession
from telethon.sync import TelegramClient
from opentele.td import TDesktop
from opentele.api import API, UseCurrentSession
from dotenv import set_key, load_dotenv
from opentele.exception import TFileNotFound

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Загружаем переменные окружения
load_dotenv()

# Ключ для переменной окружения, где будет храниться строка сессии
TELEGRAM_SESSION_ENV_KEY = "TELEGRAM_SESSION"
TELEGRAM_SESSION = os.getenv(TELEGRAM_SESSION_ENV_KEY, None)

# Путь к директории tdata
SESSION_PATH = os.getenv("TDATA_PATH", "tdatas/tdata/")

def get_proxy():
    """Получить прокси-соединение из переменных окружения, если они установлены"""
    proxy_type = os.getenv("PROXY_TYPE")
    proxy_host = os.getenv("PROXY_HOST")
    proxy_port = os.getenv("PROXY_PORT")
    proxy_username = os.getenv("PROXY_USERNAME")
    proxy_password = os.getenv("PROXY_PASSWORD")
    
    if not (proxy_type and proxy_host and proxy_port):
        return None
    
    proxy_conn = {
        'proxy_type': proxy_type,
        'addr': proxy_host,
        'port': int(proxy_port),
    }
    
    if proxy_username and proxy_password:
        proxy_conn.update({
            'username': proxy_username,
            'password': proxy_password
        })
    
    return proxy_conn

class MyTelegramClient:
    def __init__(self, tdata_name=None):
        self.tdata_name = tdata_name
        self.client = None
        self.me = None
        self.proxy_conn = get_proxy()

    async def authorize(self):
        session_hash = hashlib.md5(json.dumps(self.proxy_conn or {}, sort_keys=True).encode()).hexdigest()[:8]
        session_dir = Path("sessions")
        session_dir.mkdir(exist_ok=True)
        
        if self.tdata_name:
            session_file = f"sessions/{self.tdata_name}_{session_hash}.session"
        else:
            session_file = f"sessions/tg_monitor_{session_hash}.session"

        # Сначала проверяем наличие TELEGRAM_SESSION в переменных окружения
        if TELEGRAM_SESSION:
            logger.info("🔑 Использую TELEGRAM_SESSION из переменных окружения для авторизации Telethon.")
            try:
                api = API.TelegramIOS.Generate()
                self.client = TelegramClient(StringSession(TELEGRAM_SESSION), api.api_id, api.api_hash, proxy=self.proxy_conn)
                await self.client.start()
                self.me = await self.client.get_me()
                logger.info(f"✅ Подключено как: {self.me.first_name} (@{self.me.username}) [TELEGRAM_SESSION]")
                return True
            except Exception as e:
                logger.error(f"❌ Ошибка авторизации через TELEGRAM_SESSION: {e}")
                logger.info("🔄 Пробую авторизоваться через tdata...")
                # Не возвращаем False, а продолжаем пытаться через tdata
        
        # Если нет TELEGRAM_SESSION или авторизация через него не удалась,
        # пробуем авторизоваться через tdata
        if os.path.isdir(SESSION_PATH):
            logger.info(f"🔄 Использую tdata из {SESSION_PATH} для авторизации.")
            try:
                tdesk = TDesktop(SESSION_PATH)
                if not tdesk.accounts:
                    logger.error("❌ Аккаунты не найдены в tdata")
                    return False
                
                os.makedirs(os.path.dirname(session_file), exist_ok=True)
                self.client = await tdesk.ToTelethon(
                    session_file, 
                    UseCurrentSession,
                    api=API.TelegramIOS.Generate(),
                    proxy=self.proxy_conn
                )
                await self.client.connect()
                self.me = await self.client.get_me()
                
                # Сохраняем строку сессии в .env для будущего использования
                string_session = StringSession.save(self.client.session)
                set_key(".env", TELEGRAM_SESSION_ENV_KEY, string_session)
                
                logger.info(f"✅ Подключено как: {self.me.first_name} (@{self.me.username}) [tdata]")
                logger.info("Сессия успешно сохранена в .env")
                return True
            except Exception as e:
                logger.error(f"❌ Ошибка авторизации через tdata: {e}")
                return False
        else:
            logger.error("❌ Не найден ни TELEGRAM_SESSION, ни директория tdata. Авторизация невозможна.")
            return False


async def authorize_client(tdata_name=None):
    client = MyTelegramClient(tdata_name)
    result = await client.authorize()
    if result:
        return client
    else:
        return None
