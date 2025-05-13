import os
import asyncio
import hashlib
import json
from pathlib import Path
from dotenv import load_dotenv, set_key
from telethon.sessions import StringSession
from opentele.td import TDesktop
from opentele.api import API, UseCurrentSession
from tdata_session_exporter import authorize_client
from tdata_session_exporter.auth import get_proxy

# Загружаем переменные окружения
load_dotenv()

# Константы
TELEGRAM_SESSION_ENV_KEY = "TELEGRAM_SESSION"
SESSION_PATH = os.getenv("TDATA_PATH", "tdatas/tdata/")

async def extract_session_from_tdata():
    """Извлечение строки сессии из tdata и сохранение в .env"""
    print(f"🔄 Извлечение сессии из {SESSION_PATH}...")
    
    if not os.path.isdir(SESSION_PATH):
        print(f"❌ Директория {SESSION_PATH} не найдена")
        return False
    
    try:
        # Получаем настройки прокси для использовауния в хеше и авторизации
        proxy_conn = get_proxy()
        
        # Создаем хеш на основе настроек прокси для имени файла сессии
        session_hash = hashlib.md5(json.dumps(proxy_conn or {}, sort_keys=True).encode()).hexdigest()[:8]
        session_dir = Path("sessions")
        session_dir.mkdir(exist_ok=True)
        session_file = f"sessions/extract_test_{session_hash}.session"
        
        # Инициализация TDesktop и проверка наличия аккаунтов
        tdesk = TDesktop(SESSION_PATH)
        if not tdesk.accounts:
            print("❌ Аккаунты не найдены в tdata")
            return False
        
        # Создаем Telethon клиент из tdata
        client = await tdesk.ToTelethon(
            session_file,
            UseCurrentSession,
            api=API.TelegramIOS.Generate(),
            proxy=proxy_conn
        )
        
        # Подключаемся и получаем строку сессии
        await client.connect()
        me = await client.get_me()
        print(f"✅ Сессия извлечена для: {me.first_name} (@{me.username})")
        
        # Сохраняем строку сессии в .env
        string_session = StringSession.save(client.session)
        set_key(".env", TELEGRAM_SESSION_ENV_KEY, string_session)
        print("💾 Строка сессии сохранена в .env")
        
        # Закрываем соединение
        await client.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при извлечении сессии: {e}")
        return False

async def test_authorization():
    """Тестирование авторизации с использованием извлеченной сессии"""
    print("\n🔑 Тестирование авторизации через TELEGRAM_SESSION...")
    
    client = await authorize_client()
    if client and client.me:
        print(f"✅ Успешная авторизация как: {client.me.first_name} (@{client.me.username})")
        proxy_status = "Используется" if client.proxy_conn else "Не используется"
        print(f"📡 Прокси: {proxy_status}")
        await client.client.disconnect()
        return True
    else:
        print("❌ Ошибка авторизации")
        return False

async def main():
    """Основная функция для тестирования: извлечение сессии, затем авторизация"""
    print("🚀 Начало тестирования: извлечение сессии -> авторизация")
    
    # Шаг 1: Извлечение сессии из tdata
    extraction_success = await extract_session_from_tdata()
    if not extraction_success:
        print("❌ Не удалось извлечь сессию, тестирование прервано")
        return
    
    # Шаг 2: Тестирование авторизации через извлеченную сессию
    auth_success = await test_authorization()
    
    # Вывод итогового результата
    if extraction_success and auth_success:
        print("\n✅ Тестирование завершено успешно! Оба этапа пройдены.")
    else:
        print("\n⚠️ Тестирование завершено с ошибками.")

if __name__ == "__main__":
    asyncio.run(main())
