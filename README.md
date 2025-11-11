# Telegram tdata Session Exporter

This library provides functionality for authenticating with Telegram using:
- JSON+.session bundle (new)
- Telegram Desktop `tdata` folder

## Features

- Extract session data from Telegram Desktop's `tdata` folder
- Convert tdata to Telethon session string
- Simple async interface

## Requirements

- Python 3.6+
- Telethon
- opentele
- python-dotenv

## ⚠️ ВАЖНО: Обязательное использование прокси

**Библиотека работает ТОЛЬКО через прокси!** Без настроенного прокси работа невозможна.

### Настройка прокси через переменные окружения

Создайте файл `.env` в корне вашего проекта и укажите прокси в одной строке:

```env
PROXIES=ansible.9qw.ru:8126:admin:tghyjuki
```

#### Поддерживаемые форматы:

1. **С авторизацией (socks5 по умолчанию):**
   ```env
   PROXIES=host:port:username:password
   ```
   Пример: `PROXIES=ansible.9qw.ru:8126:admin:tghyjuki`

2. **Без авторизации (socks5 по умолчанию):**
   ```env
   PROXIES=host:port
   ```
   Пример: `PROXIES=proxy.example.com:1080`

3. **С указанием типа прокси:**
   ```env
   PROXIES=type:host:port:username:password
   ```
   Пример: `PROXIES=socks5:ansible.9qw.ru:8126:admin:tghyjuki`

**Поддерживаемые типы прокси:** `socks5`, `socks4`, `http`, `https` (по умолчанию: `socks5`)

### Проверка прокси

Библиотека автоматически проверяет:
- ✅ Наличие переменной окружения `PROXIES`
- ✅ Корректность формата прокси
- ✅ Валидность типа прокси
- ✅ Доступность прокси-сервера (пытается подключиться к указанному хосту и порту)

### Возможные ошибки

- **`❌ ПРОКСИ ОБЯЗАТЕЛЕН!`** - не указана переменная окружения `PROXIES`
- **`❌ Неверный формат PROXIES`** - неправильный формат строки прокси
- **`❌ Неверный тип прокси`** - указан неподдерживаемый тип прокси
- **`❌ Не удалось подключиться к прокси`** - прокси-сервер недоступен или указаны неверные данные
- **`❌ Превышено время ожидания подключения к прокси`** - прокси не отвечает

Если возникают ошибки с прокси - библиотека **не запустится** и выдаст соответствующее сообщение об ошибке.

## Installation

To install the library, use:

```bash
pip install git+https://github.com/stufently/session-auth-lib.git
```

### Export bundle from tdata (JSON + .session)

**⚠️ ВАЖНО:** Для экспорта также требуется настроенный прокси!

Python API (auto path, default output under project root):
```python
from tdata_session_exporter.auth import export_bundle_from_tdata_auto
from dotenv import load_dotenv

# Загружаем переменные окружения (включая прокси)
load_dotenv()

try:
    # Сохранит в ./accounts/<basename>/<basename>.json и .session
    # Автоматически проверит прокси перед началом работы
    ok = export_bundle_from_tdata_auto(
        tdata_path="/abs/path/to/+2349049675164/tdata",
        # out_base_dir="/abs/path/to/project/accounts",  # опционально, по умолчанию ./accounts
        # api_id=2040, api_hash="b18441a1ff607e10a989891a5462e627",  # опционально, по умолчанию Desktop ключи
    )
    print("✅ Экспорт успешен!" if ok else "❌ Экспорт не удался")
except (ValueError, ConnectionError) as e:
    print(f"❌ Ошибка: {e}")
```

Python API (explicit out dir and basename):
```python
from tdata_session_exporter.auth import export_bundle_from_tdata_sync
from dotenv import load_dotenv

# Загружаем переменные окружения (включая прокси)
load_dotenv()

try:
    ok = export_bundle_from_tdata_sync(
        tdata_path="/abs/path/to/tdata",
        out_dir="/abs/path/to/out",
        basename="+2349049675164",  # имя файлов без расширения
        # api_id=2040, api_hash="b18441a1ff607e10a989891a5462e627",  # можно не указывать: стоят по умолчанию
    )
    print("✅ Экспорт успешен!" if ok else "❌ Экспорт не удался")
except (ValueError, ConnectionError) as e:
    print(f"❌ Ошибка: {e}")
```

## Usage

### Auth priority

1. Bundle `JSON + .session` (env `BUNDLE_JSON_PATH` or auto-search in `./accounts`)
2. `tdata` folder

### Preparing tdata folder

1. Create a `tdatas` folder in your project root
2. Copy your Telegram Desktop's `tdata` folder into it (default location is `%APPDATA%\Telegram Desktop\tdata` on Windows)

### Using the library

**ВАЖНО:** Перед использованием убедитесь, что настроили переменные окружения для прокси!

```python
from tdata_session_exporter import authorize_client
import asyncio
from dotenv import load_dotenv

# Загружаем переменные окружения (включая данные прокси)
load_dotenv()

async def main():
    try:
        # Pass the name of the folder in tdatas/ containing tdata files
        # Автоматически проверит и использует прокси из ENV
        client = await authorize_client("tdata")
        if client:
            print("Authorization successful!")
            # Now you can use client for Telegram operations
            me = await client.get_me()
            print(f"Logged in as {me.first_name} (@{me.username})")
        else:
            print("Authorization failed")
    except (ValueError, ConnectionError) as e:
        print(f"Ошибка: {e}")
        print("Проверьте настройки прокси в .env файле!")

if __name__ == "__main__":
    asyncio.run(main())
```

### Using bundle explicitly

```python
from tdata_session_exporter.auth import MyTelegramClient
import asyncio
from dotenv import load_dotenv

# Загружаем переменные окружения (включая прокси)
load_dotenv()

async def main():
    try:
        # Автоматически проверит прокси при инициализации
        c = MyTelegramClient(bundle_json="/abs/path/accounts/+2349049675164.json")
        ok = await c.authorize()
        print(ok, c.me)
    except (ValueError, ConnectionError) as e:
        print(f"❌ Ошибка: {e}")

asyncio.run(main())
```

### JSON session (string_session inside JSON)

You can authorize using a JSON file that contains `app_id`, `app_hash` and a Telethon string session. The library accepts any of these keys for the string session: `string_session`, `session_string`, `telethon_string`, `telethon_session`.

Example JSON file:

```json
{
  "app_id": 2040,
  "app_hash": "b18441a1ff607e10a989891a5462e627",
  "string_session": "1A...your-telethon-string-session...=="
}
```

Usage via environment variable:

```bash
export BUNDLE_JSON_PATH="/abs/path/to/account.json"
```

Or pass the path explicitly:

```python
from tdata_session_exporter.auth import MyTelegramClient
import asyncio
from dotenv import load_dotenv

# Загружаем переменные окружения (включая прокси)
load_dotenv()

async def main():
    try:
        # Автоматически проверит прокси при инициализации
        c = MyTelegramClient(bundle_json="/abs/path/to/account.json")
        ok = await c.authorize()
        print(ok, c.me)
    except (ValueError, ConnectionError) as e:
        print(f"❌ Ошибка: {e}")

asyncio.run(main())
```

If the JSON does not contain a string session, the library will try to use a neighboring `.session` file with the same basename as the JSON.

## Troubleshooting

### Ошибки прокси (самые частые)

#### ❌ ПРОКСИ ОБЯЗАТЕЛЕН!

Библиотека не может работать без прокси. Создайте файл `.env` и укажите данные прокси:

```env
PROXIES=ansible.9qw.ru:8126:admin:tghyjuki
```

Или без авторизации:
```env
PROXIES=proxy.example.com:1080
```

#### ❌ Неверный формат PROXIES

Проверьте правильность формата. Поддерживаемые форматы:
- `host:port` - без авторизации
- `host:port:username:password` - с авторизацией
- `type:host:port:username:password` - с указанием типа

Пример правильного формата:
```env
PROXIES=ansible.9qw.ru:8126:admin:tghyjuki
```

#### ❌ Не удалось подключиться к прокси

Возможные причины:
1. Прокси-сервер выключен или недоступен
2. Неверный хост или порт
3. Прокси требует авторизацию, а вы не указали username и password
4. Файрвол блокирует подключение к прокси

Решение:
- Проверьте работоспособность прокси в браузере или другом приложении
- Убедитесь, что данные прокси указаны правильно
- Проверьте, что прокси-сервер работает
- Убедитесь, что формат: `host:port:username:password`

#### ❌ Неверный тип прокси

Поддерживаются только: `socks5`, `socks4`, `http`, `https`

Если вы указываете тип явно, используйте формат:
```env
PROXIES=socks5:ansible.9qw.ru:8126:admin:tghyjuki
```

### No account has been loaded

If you get an error like `Unexpected Exception: No account has been loaded`, make sure:

1. Your `tdata` folder contains valid Telegram account data
2. The folder structure is correct (`tdatas/tdata/` with all Telegram Desktop files inside)
3. You're using a compatible version of Telegram Desktop (this library has been tested with TD 4.x)
4. **Прокси настроен правильно** (см. выше)

### Connection issues

If you have connection problems:

1. **Убедитесь, что прокси настроен и работает корректно** (это обязательное требование!)
2. Make sure your internet connection is stable
3. Check if your IP is not blocked by Telegram (или IP вашего прокси)
4. Try using a different API (by modifying the code to use a different `API` from `opentele.api`)

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
