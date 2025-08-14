# Telegram tdata Session Exporter

This library provides functionality for authenticating with Telegram using:
- TELEGRAM_SESSION string (from `.env`)
- JSON+.session bundle (new)
- Telegram Desktop `tdata` folder

## Features

- Extract session data from Telegram Desktop's `tdata` folder
- Convert tdata to Telethon session string
- Automatically save session string to `.env` file
- Simple async interface

## Requirements

- Python 3.6+
- Telethon
- opentele
- python-dotenv

## Installation

To install the library, use:

```bash
pip install git+https://github.com/stufently/session-auth-lib.git
```

### Export bundle from tdata (JSON + .session)

Python API (auto path, default output under project root):
```python
from tdata_session_exporter.auth import export_bundle_from_tdata_auto

# Сохранит в ./accounts/<basename>/<basename>.json и .session
ok = export_bundle_from_tdata_auto(
    tdata_path="/abs/path/to/+2349049675164/tdata",
    # out_base_dir="/abs/path/to/project/accounts",  # опционально, по умолчанию ./accounts
    # api_id=2040, api_hash="b18441a1ff607e10a989891a5462e627",  # опционально, по умолчанию Desktop ключи
)
print(ok)
```

Python API (explicit out dir and basename):
```python
from tdata_session_exporter.auth import export_bundle_from_tdata_sync

ok = export_bundle_from_tdata_sync(
    tdata_path="/abs/path/to/tdata",
    out_dir="/abs/path/to/out",
    basename="+2349049675164",  # имя файлов без расширения
    # api_id=2040, api_hash="b18441a1ff607e10a989891a5462e627",  # можно не указывать: стоят по умолчанию
)
print(ok)
```

## Usage

### Auth priority

1. `TELEGRAM_SESSION` env var
2. Bundle `JSON + .session` (env `BUNDLE_JSON_PATH` or explicit path)
3. `tdata` folder

### Preparing tdata folder

1. Create a `tdatas` folder in your project root
2. Copy your Telegram Desktop's `tdata` folder into it (default location is `%APPDATA%\Telegram Desktop\tdata` on Windows)

### Using the library

```python
from tdata_session_exporter import authorize_client
import asyncio

async def main():
    # Pass the name of the folder in tdatas/ containing tdata files
    client = await authorize_client("tdata")
    if client:
        print("Authorization successful!")
        # Now you can use client for Telegram operations
        me = await client.get_me()
        print(f"Logged in as {me.first_name} (@{me.username})")
    else:
        print("Authorization failed")

if __name__ == "__main__":
    asyncio.run(main())
```

### Using bundle explicitly

```python
from tdata_session_exporter.auth import MyTelegramClient
import asyncio

async def main():
    c = MyTelegramClient(bundle_json="/abs/path/accounts/+2349049675164.json")
    ok = await c.authorize()
    print(ok, c.me)

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

async def main():
    c = MyTelegramClient(bundle_json="/abs/path/to/account.json")
    ok = await c.authorize()
    print(ok, c.me)

asyncio.run(main())
```

If the JSON does not contain a string session, the library will try to use a neighboring `.session` file with the same basename as the JSON.

### Using the exported session string

After running the above code, a Telethon session string will be saved in your `.env` file under the key `TELEGRAM_SESSION`. You can use this string directly with Telethon:

```python
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv
import os
import asyncio

async def main():
    load_dotenv()
    session_string = os.getenv("TELEGRAM_SESSION")
    
    # Create client using your API credentials
    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    await client.start()
    
    # Now you can use the client
    print("Connected successfully!")

if __name__ == "__main__":
    asyncio.run(main())
```

## Troubleshooting

### No account has been loaded

If you get an error like `Unexpected Exception: No account has been loaded`, make sure:

1. Your `tdata` folder contains valid Telegram account data
2. The folder structure is correct (`tdatas/tdata/` with all Telegram Desktop files inside)
3. You're using a compatible version of Telegram Desktop (this library has been tested with TD 4.x)

### Connection issues

If you have connection problems:

1. Make sure your internet connection is stable
2. Check if your IP is not blocked by Telegram
3. Try using a different API (by modifying the code to use a different `API` from `opentele.api`)

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
