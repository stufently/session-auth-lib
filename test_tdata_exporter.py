from tdata_session_exporter import authorize_client
import asyncio

async def main():
    client = await authorize_client("tdata")
    if client:
        print("Авторизация прошла успешно!")
        # The client.me property already contains user info after authorization
        if client.me:
            print(f"Logged in as {client.me.first_name} (@{client.me.username})")
    else:
        print("Ошибка авторизации")

if __name__ == "__main__":
    asyncio.run(main())
