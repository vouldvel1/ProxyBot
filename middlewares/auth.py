"""
Middleware для авторизации
"""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
import logging

from bot.database import Database

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseMiddleware):
    """Middleware для автоматической регистрации пользователей"""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Получаем пользователя из события
        user: User = data.get("event_from_user")

        if user and not user.is_bot:
            try:
                # Автоматически добавляем пользователя в БД если его нет
                await Database.add_telegram_user(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name
                )
            except Exception as e:
                logger.error(f"Ошибка добавления пользователя в middleware: {e}")

        # Продолжаем выполнение
        return await handler(event, data)
