from setuptools import setup

setup(
    name="tdata-session-exporter",
    version="0.1.0",
    description="Export Telegram Desktop tdata sessions to Telethon string sessions",
    author="Romdevv",
    author_email="romdevv@gmail.com",
    packages=["tdata_session_exporter"],
    install_requires=[
        "telethon>=1.0",
        "opentele>=1.15.0",
        "python-dotenv>=0.19.0"
    ],
    python_requires=">=3.7",
)
