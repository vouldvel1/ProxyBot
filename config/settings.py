"""
Настройки приложения
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class Settings:
    """Класс настроек приложения"""

    # Telegram
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_IDS: list[int] = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]

    # YooKassa
    YOOKASSA_SHOP_ID: str = os.getenv("YOOKASSA_SHOP_ID", "")
    YOOKASSA_SECRET_KEY: str = os.getenv("YOOKASSA_SECRET_KEY", "")
    YOOKASSA_PROVIDER_TOKEN: str = os.getenv("YOOKASSA_PROVIDER_TOKEN", "")

    # Marzban
    MARZBAN_API_URL: str = os.getenv("MARZBAN_API_URL", "")
    MARZBAN_USERNAME: str = os.getenv("MARZBAN_USERNAME", "")
    MARZBAN_PASSWORD: str = os.getenv("MARZBAN_PASSWORD", "")

    # База данных
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///bot_database.db")

    # Подписка
    SUBSCRIPTION_PRICE: int = int(os.getenv("SUBSCRIPTION_PRICE", "500"))
    SUBSCRIPTION_DURATION: int = int(os.getenv("SUBSCRIPTION_DURATION", "30"))

    # Валидация обязательных настроек
    def validate(self) -> bool:
        """Проверка обязательных настроек"""
        required_fields = [
            self.BOT_TOKEN,
            self.YOOKASSA_SHOP_ID,
            self.YOOKASSA_SECRET_KEY,
            self.MARZBAN_API_URL,
            self.MARZBAN_USERNAME,
            self.MARZBAN_PASSWORD
        ]
        return all(required_fields)

settings = Settings()
