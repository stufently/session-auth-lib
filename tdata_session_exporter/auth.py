import asyncio
import logging
import os
import hashlib
import time
import json
import socket
import socks
from pathlib import Path
from telethon.sessions import StringSession
from telethon.sync import TelegramClient
from opentele.td import TDesktop
from opentele.api import API, UseCurrentSession
from dotenv import load_dotenv
from opentele.exception import TFileNotFound

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
# Уменьшаем болтливость Telethon
logging.getLogger("telethon").setLevel(logging.WARNING)

# Загружаем переменные окружения (для прокси/TDATA_PATH/BUNDLE_JSON_PATH)
load_dotenv()
# Путь к JSON бандла (если задан) — JSON + соседний .session
BUNDLE_JSON_PATH = os.getenv("BUNDLE_JSON_PATH")

# Путь к директории tdata
SESSION_PATH = os.getenv("TDATA_PATH", "tdatas/tdata/")


def _load_bundle_config(json_path: str):
    """Загружает JSON бандла и возвращает (cfg, session_path_no_ext)."""
    with open(json_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    api_id = cfg.get('app_id') or cfg.get('api_id')
    api_hash = cfg.get('app_hash')
    if not api_id or not api_hash:
        raise ValueError('В JSON отсутствуют app_id/app_hash')

    # Поддержка JSON, который содержит строковую сессию Telethon
    # Возможные ключи: string_session, session_string, telethon_string, telethon_session
    for k in ('string_session', 'session_string', 'telethon_string', 'telethon_session'):
        if cfg.get(k):
            cfg['string_session'] = cfg.get(k)
            break

    session_file = cfg.get('session_file')
    if not session_file:
        # если не указано — используем имя JSON
        session_file = os.path.splitext(os.path.basename(json_path))[0]

    session_basename = os.path.splitext(session_file)[0]
    base_dir = os.path.dirname(os.path.abspath(json_path))
    session_path_no_ext = os.path.join(base_dir, session_basename)

    cfg['app_id'] = int(api_id)
    cfg['app_hash'] = str(api_hash)
    cfg['session_file'] = session_basename
    return cfg, session_path_no_ext


def _find_bundle_in_accounts() -> str:
    """Ищет JSON+.session в папке ./accounts (в корне проекта).
    Возвращает путь к первому валидному JSON. Если не найдено — пустая строка.
    """
    base_dir = os.path.join(os.getcwd(), "accounts")
    if not os.path.isdir(base_dir):
        return ""

    # Собираем кандидаты: *.json в accounts/ и accounts/*/
    json_candidates = []
    try:
        for name in os.listdir(base_dir):
            p = os.path.join(base_dir, name)
            if os.path.isfile(p) and p.lower().endswith(".json"):
                json_candidates.append(p)
            elif os.path.isdir(p):
                for sub in os.listdir(p):
                    sp = os.path.join(p, sub)
                    if os.path.isfile(sp) and sp.lower().endswith(".json"):
                        json_candidates.append(sp)
    except Exception:
        return ""

    # Проверяем пары JSON+.session
    for json_path in json_candidates:
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            session_file = cfg.get('session_file')
            if not session_file:
                session_file = os.path.splitext(os.path.basename(json_path))[0]
            session_path = os.path.join(os.path.dirname(json_path), f"{os.path.splitext(session_file)[0]}.session")
            if os.path.isfile(session_path):
                return json_path
        except Exception:
            continue
    return ""

def get_proxy():
    """
    Получить прокси-соединение из переменных окружения (ОБЯЗАТЕЛЬНО)
    
    Формат PROXIES:
    - host:port                          (socks5 по умолчанию, без авторизации)
    - host:port:username:password        (socks5 по умолчанию, с авторизацией)
    - type:host:port                     (с указанием типа, без авторизации)
    - type:host:port:username:password   (с указанием типа и авторизацией)
    
    Примеры:
    - PROXIES=ansible.9qw.ru:8126:admin:tghyjuki
    - PROXIES=socks5:ansible.9qw.ru:8126:admin:tghyjuki
    - PROXIES=proxy.example.com:1080
    """
    proxies = os.getenv("PROXIES")
    
    # ОБЯЗАТЕЛЬНАЯ проверка наличия прокси
    if not proxies:
        raise ValueError(
            "❌ ПРОКСИ ОБЯЗАТЕЛЕН! Установите переменную окружения PROXIES\n"
            "Формат: host:port:username:password\n"
            "Пример: PROXIES=ansible.9qw.ru:8126:admin:пароль"
        )
    
    # Парсинг строки прокси
    parts = proxies.strip().split(':')
    
    if len(parts) < 2:
        raise ValueError(
            f"❌ Неверный формат PROXIES: {proxies}\n"
            "Формат: host:port или host:port:username:password"
        )
    
    # Определяем, есть ли тип прокси в начале
    valid_proxy_types = ['socks5', 'socks4', 'http', 'https']
    proxy_type = 'socks5'  # По умолчанию
    proxy_host = None
    proxy_port = None
    proxy_username = None
    proxy_password = None
    
    # Проверяем, указан ли тип прокси
    if parts[0].lower() in valid_proxy_types:
        # Формат: type:host:port[:username:password]
        if len(parts) < 3:
            raise ValueError(
                f"❌ Неверный формат PROXIES с типом: {proxies}\n"
                "Формат: type:host:port или type:host:port:username:password"
            )
        proxy_type = parts[0].lower()
        proxy_host = parts[1]
        proxy_port = parts[2]
        if len(parts) >= 5:
            proxy_username = parts[3]
            proxy_password = parts[4]
    else:
        # Формат: host:port[:username:password]
        proxy_host = parts[0]
        proxy_port = parts[1]
        if len(parts) >= 4:
            proxy_username = parts[2]
            proxy_password = parts[3]
    
    # Валидация порта
    try:
        port = int(proxy_port)
        if port < 1 or port > 65535:
            raise ValueError(f"❌ Неверный порт прокси: {port}. Должен быть от 1 до 65535")
    except ValueError as e:
        if "invalid literal" in str(e):
            raise ValueError(f"❌ Порт прокси должен быть числом: {proxy_port}")
        raise
    
    proxy_conn = {
        'proxy_type': proxy_type,
        'addr': proxy_host,
        'port': port,
    }
    
    if proxy_username and proxy_password:
        proxy_conn.update({
            'username': proxy_username,
            'password': proxy_password
        })
        logger.info(f"✅ Прокси настроен: {proxy_type}://{proxy_username}@{proxy_host}:{proxy_port}")
    else:
        logger.info(f"✅ Прокси настроен: {proxy_type}://{proxy_host}:{proxy_port}")
    
    return proxy_conn


def validate_proxy_connection(proxy_conn: dict, timeout: int = 10) -> bool:
    """
    Проверяет доступность и работоспособность прокси-сервера.
    Выполняет реальное подключение через SOCKS5/SOCKS4/HTTP прокси
    и проверяет авторизацию.
    Возвращает True, если прокси работает, иначе выбрасывает исключение.
    """
    proxy_type = proxy_conn['proxy_type']
    proxy_host = proxy_conn['addr']
    proxy_port = proxy_conn['port']
    proxy_username = proxy_conn.get('username')
    proxy_password = proxy_conn.get('password')
    
    logger.info(f"🔍 Проверка прокси {proxy_type}://{proxy_host}:{proxy_port}...")
    
    # Маппинг типов прокси для библиотеки socks
    proxy_type_map = {
        'socks5': socks.SOCKS5,
        'socks4': socks.SOCKS4,
        'http': socks.HTTP,
        'https': socks.HTTP,
    }
    
    if proxy_type not in proxy_type_map:
        raise ValueError(f"❌ Неподдерживаемый тип прокси: {proxy_type}")
    
    try:
        # Создаем сокет с прокси
        sock = socks.socksocket()
        sock.settimeout(timeout)
        
        # Настраиваем прокси
        sock.set_proxy(
            proxy_type=proxy_type_map[proxy_type],
            addr=proxy_host,
            port=proxy_port,
            username=proxy_username,
            password=proxy_password
        )
        
        # Пытаемся подключиться к публичному серверу Telegram через прокси
        # Используем один из DC серверов Telegram для проверки
        test_host = "149.154.167.50"  # Telegram DC2
        test_port = 443
        
        logger.info(f"🔌 Попытка подключения через прокси к {test_host}:{test_port}...")
        sock.connect((test_host, test_port))
        sock.close()
        
        logger.info(f"✅ Прокси работает корректно: {proxy_type}://{proxy_host}:{proxy_port}")
        return True
        
    except socks.ProxyConnectionError as e:
        raise ConnectionError(
            f"❌ Ошибка подключения к прокси {proxy_host}:{proxy_port}\n"
            f"Прокси-сервер недоступен или отклонил соединение.\n"
            f"Детали: {str(e)}"
        )
    except socks.GeneralProxyError as e:
        error_msg = str(e).lower()
        if "authentication" in error_msg or "auth" in error_msg:
            raise ConnectionError(
                f"❌ Ошибка авторизации на прокси {proxy_host}:{proxy_port}\n"
                f"Проверьте правильность username и password.\n"
                f"Детали: {str(e)}"
            )
        else:
            raise ConnectionError(
                f"❌ Ошибка работы прокси {proxy_host}:{proxy_port}\n"
                f"Прокси не смог установить соединение.\n"
                f"Детали: {str(e)}"
            )
    except socket.gaierror:
        raise ConnectionError(
            f"❌ Не удалось разрешить адрес прокси: {proxy_host}\n"
            f"Проверьте правильность хоста."
        )
    except socket.timeout:
        raise ConnectionError(
            f"❌ Превышено время ожидания подключения к прокси {proxy_host}:{proxy_port}\n"
            f"Прокси не отвечает или работает слишком медленно."
        )
    except Exception as e:
        raise ConnectionError(
            f"❌ Неожиданная ошибка при проверке прокси {proxy_host}:{proxy_port}\n"
            f"Детали: {str(e)}"
        )


class MyTelegramClient:
    def __init__(self, tdata_name=None, bundle_json: str = None, tdata_path: str = None):
        self.tdata_name = tdata_name
        # 1) Явный аргумент; 2) env; 3) auto-search в ./accounts
        auto_bundle = _find_bundle_in_accounts()
        self.bundle_json = bundle_json or BUNDLE_JSON_PATH or (auto_bundle if auto_bundle else None)
        self.tdata_path_override = tdata_path
        self.client = None
        self.me = None
        
        # ОБЯЗАТЕЛЬНАЯ проверка прокси при инициализации
        try:
            self.proxy_conn = get_proxy()
            # Проверяем доступность прокси
            validate_proxy_connection(self.proxy_conn)
        except (ValueError, ConnectionError) as e:
            logger.error(f"❌ Ошибка инициализации: {e}")
            raise

    async def authorize(self):
        session_hash = hashlib.md5(json.dumps(self.proxy_conn or {}, sort_keys=True).encode()).hexdigest()[:8]
        session_dir = Path("sessions")
        session_dir.mkdir(exist_ok=True)
        
        if self.tdata_name:
            session_file = f"sessions/{self.tdata_name}_{session_hash}.session"
        else:
            session_file = f"sessions/tg_monitor_{session_hash}.session"

        # Попытка авторизации из бандла JSON+.session
        if self.bundle_json and os.path.exists(self.bundle_json):
            try:
                cfg, session_path_no_ext = _load_bundle_config(self.bundle_json)
                logger.info(f"🔄 Использую бандл JSON+.session: {self.bundle_json}")
                # Вариант 1: строковая сессия внутри JSON
                if cfg.get('string_session'):
                    try:
                        self.client = TelegramClient(
                            StringSession(cfg['string_session']),
                            int(cfg['app_id']),
                            str(cfg['app_hash']),
                            proxy=self.proxy_conn
                        )
                        await self.client.start()
                        self.me = await self.client.get_me()
                        logger.info(f"✅ Подключено как: {self.me.first_name} (@{self.me.username}) [bundle:string_session]")
                        return True
                    except Exception as e:
                        logger.error(f"❌ Не удалось авторизоваться по string_session из JSON: {e}")
                        # Падать не будем — попробуем через .session файл

                # Вариант 2: рядом лежит .session файл того же basename
                self.client = TelegramClient(session_path_no_ext, cfg['app_id'], cfg['app_hash'], proxy=self.proxy_conn)
                async with self.client:
                    if not await self.client.is_user_authorized():
                        logger.error("❌ Сессия недействительна или отозвана [bundle]")
                        return False
                    self.me = await self.client.get_me()
                    logger.info(f"✅ Подключено как: {self.me.first_name} (@{self.me.username}) [bundle:.session]")
                    return True
            except Exception as e:
                logger.error(f"❌ Ошибка авторизации через bundle: {e}")
                # Падать не будем — попробуем tdata
        
        # Если нет бандла — пробуем tdata
        # 1) явный tdata_path; 2) env TDATA_PATH; 3) ./tdatas/tdata; 4) ./tdata
        tdata_path = self.tdata_path_override or SESSION_PATH
        if not os.path.isdir(tdata_path):
            alt_candidates = [os.path.join(os.getcwd(), 'tdatas', 'tdata'), os.path.join(os.getcwd(), 'tdata')]
            for cand in alt_candidates:
                if os.path.isdir(cand):
                    tdata_path = cand
                    break
        if os.path.isdir(tdata_path):
            logger.info(f"🔄 Использую tdata из {tdata_path} для авторизации.")
            try:
                tdesk = TDesktop(tdata_path)
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
                logger.info(f"✅ Подключено как: {self.me.first_name} (@{self.me.username}) [tdata]")
                return True
            except Exception as e:
                logger.error(f"❌ Ошибка авторизации через tdata: {e}")
                return False
        else:
            logger.error("❌ Не найден бандл в ./accounts и директория tdata. Авторизация невозможна.")
            return False


async def authorize_client(tdata_name=None):
    """
    Создает и авторизует Telegram клиента.
    ВНИМАНИЕ: Требует обязательного наличия валидного прокси в ENV.
    """
    client = MyTelegramClient(tdata_name)
    result = await client.authorize()
    if result:
        return client
    else:
        return None


def _derive_basename_from_tdata(tdata_path: str) -> str:
    # Если путь заканчивается на /tdata, берём имя родительской директории, иначе сам basename
    base = os.path.basename(os.path.normpath(tdata_path))
    if base.lower() == 'tdata':
        return os.path.basename(os.path.dirname(os.path.normpath(tdata_path))) or 'account'
    return base or 'account'


def _default_accounts_dir() -> str:
    # По умолчанию создаём в <cwd>/accounts
    return os.path.join(os.getcwd(), 'accounts')


async def export_bundle_from_tdata(tdata_path: str, out_dir: str, basename: str,
                                   api_id: int = None, api_hash: str = None) -> bool:
    """
    Экспортирует из папки tdata пару файлов: <basename>.session и <basename>.json в out_dir.
    По умолчанию использует ключи Telegram Desktop (2040/b184...).
    ВНИМАНИЕ: Требует обязательного наличия прокси в ENV.
    """
    # ОБЯЗАТЕЛЬНАЯ проверка прокси
    try:
        proxy_conn = get_proxy()
        validate_proxy_connection(proxy_conn)
    except (ValueError, ConnectionError) as e:
        logger.error(f"❌ Ошибка при экспорте: {e}")
        return False
    
    if not os.path.isdir(tdata_path):
        logger.error(f"❌ Директория tdata не найдена: {tdata_path}")
        return False

    os.makedirs(out_dir, exist_ok=True)

    try:
        tdesk = TDesktop(tdata_path)
        if not tdesk.accounts:
            logger.error("❌ Аккаунты не найдены в tdata")
            return False
    except TFileNotFound as e:
        logger.error(f"❌ TFileNotFound: {e}")
        return False

    session_path = os.path.join(out_dir, f"{basename}.session")
    json_path = os.path.join(out_dir, f"{basename}.json")

    if not api_id or not api_hash:
        api_id = 2040
        api_hash = "b18441a1ff607e10a989891a5462e627"

    # opentele ожидает класс API, поэтому формируем динамический класс
    CustomAPI = type(
        "CustomAPI",
        (API,),
        {
            "api_id": int(api_id),
            "api_hash": str(api_hash),
        },
    )

    try:
        logger.info(f"🔄 Генерация Telethon .session из tdata → {session_path}")
        # Используем прокси при экспорте
        client = await tdesk.ToTelethon(
            session_path,
            UseCurrentSession,
            api=CustomAPI,
            proxy=proxy_conn,
            auto_reconnect=False
        )
        async with client:
            me = await client.get_me()

        cfg = {
            "app_id": int(CustomAPI.api_id),
            "app_hash": str(CustomAPI.api_hash),
            "device": "tdata-export",
            "sdk": "unknown",
            "app_version": "unknown",
            "system_lang_pack": "en",
            "system_lang_code": "en",
            "lang_pack": "tdesktop",
            "lang_code": "en",
            "twoFA": None,
            "role": "",
            "id": getattr(me, 'id', None) if me else None,
            "phone": None,
            "username": getattr(me, 'username', None) if me else None,
            "date_of_birth": None,
            "date_of_birth_integrity": None,
            "is_premium": bool(getattr(me, 'premium', False)) if me else False,
            "has_profile_pic": bool(getattr(me, 'photo', None)) if me else False,
            "spamblock": None,
            "register_time": None,
            "last_check_time": int(time.time()),
            "avatar": None,
            "first_name": getattr(me, 'first_name', "") if me else "",
            "last_name": getattr(me, 'last_name', "") if me else "",
            "sex": None,
            "proxy": None,
            "ipv6": False,
            "session_file": basename
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False)

        logger.info(f"✅ Бандл сохранён: {json_path} и {session_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка экспорта бандла из tdata: {e}")
        return False


def export_bundle_from_tdata_auto(tdata_path: str,
                                  out_base_dir: str = None,
                                  api_id: int = None,
                                  api_hash: str = None) -> bool:
    """
    Упрощённый экспорт: достаточно указать только путь к tdata.
    По умолчанию сохранит в <cwd>/accounts/<basename>/{basename}.session и .json,
    где basename — это имя папки родителя над tdata (например, "+2349049675164").
    """
    basename = _derive_basename_from_tdata(tdata_path)
    base_dir = out_base_dir or _default_accounts_dir()
    out_dir = os.path.join(base_dir, basename)
    return asyncio.run(export_bundle_from_tdata(tdata_path, out_dir, basename, api_id, api_hash))


def export_bundle_from_tdata_sync(tdata_path: str, out_dir: str, basename: str,
                                  api_id: int = None, api_hash: str = None) -> bool:
    """Синхронная обёртка над export_bundle_from_tdata."""
    return asyncio.run(export_bundle_from_tdata(tdata_path, out_dir, basename, api_id, api_hash))
