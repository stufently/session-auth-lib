from setuptools import setup

setup(
    name="tdata-session-exporter",
    version="0.2.0",
    description="Export Telegram Desktop tdata sessions to Telethon string sessions",
    author="Romdevv",
    author_email="romdevv@gmail.com",
    packages=["tdata_session_exporter"],
    install_requires=[
        "telethon>=1.43.2,<2",
        "opentele-ng @ git+https://github.com/stufently/opentele.git@main",
        "python-dotenv>=1.0.0",
        "PySocks>=1.7.1"
    ],
    python_requires=">=3.10",
)
