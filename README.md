# Telegram tdata Session Exporter

This library provides functionality for authenticating with Telegram using **tdata** folder and exporting the session string to `.env` file. It's particularly useful for migrating from desktop Telegram clients to Python-based Telethon applications.

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
pip install git+https://github.com/stufently/tdata-session-exporter.git
```

## Usage

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
