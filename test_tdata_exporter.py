from tdata_session_exporter import authorize_client
import asyncio

async def main():
    client = await authorize_client("tdata")
    if client:
        print("Авторизация прошла успешно!")
        me = await client.get_me()
        print(f"Logged in as {me.first_name} (@{me.username})")
    else:
        print("Ошибка авторизации")

if __name__ == "__main__":
    asyncio.run(main())
