from session_auth_lib import authorize_client

async def main():
    client = await authorize_client("tdata")
    if client:
        print("Авторизация прошла успешно!")
    else:
        print("Ошибка авторизации")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
