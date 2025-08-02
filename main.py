#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Телеграм бот для управления подписками на прокси через Marzban с оплатой через ЮКасса
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.bot_instance import bot
from bot.database import init_db
from handlers import start, payment, subscription, admin
from middlewares.auth import AuthMiddleware
from config.settings import settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска бота"""
    # Валидация настроек
    if not settings.validate():
        logger.error("Ошибка конфигурации! Проверьте файл .env")
        return

    # Инициализация базы данных
    await init_db()

    # Создание диспетчера
    dp = Dispatcher(storage=MemoryStorage())

    # Подключение middleware
    # dp.middleware.setup()
    dp.message.middleware(AuthMiddleware())
    # Регистрация роутеров
    dp.include_router(start.router)
    dp.include_router(payment.router)
    dp.include_router(subscription.router)
    dp.include_router(admin.router)

    # Пропуск накопленных обновлений
    await bot.delete_webhook(drop_pending_updates=True)

    logger.info("🚀 Бот запущен с интеграцией Marzban API!")
    logger.info(f"📡 Marzban URL: {settings.MARZBAN_API_URL}")

    try:
        # Запуск поллинга
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("⛔ Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
