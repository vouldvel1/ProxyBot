"""
Работа с базой данных и интеграция с Marzban API
"""

import aiosqlite
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

DATABASE_PATH = "bot_database.db"

async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Таблица для связи Telegram пользователей с Marzban пользователями
        await db.execute("""
            CREATE TABLE IF NOT EXISTS telegram_users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                marzban_username TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)

        # Таблица для хранения платежей (ЮКасса)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                marzban_username TEXT,
                yookassa_payment_id TEXT UNIQUE,
                amount INTEGER,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (telegram_id) REFERENCES telegram_users (telegram_id)
            )
        """)

        # Таблица для настроек и конфигурации
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.commit()
        logger.info("База данных бота инициализирована")

class Database:
    """Класс для работы с локальной БД бота и Marzban API"""

    @staticmethod
    async def add_telegram_user(telegram_id: int, username: str = None, first_name: str = None, last_name: str = None):
        """Добавить Telegram пользователя"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                "INSERT OR IGNORE INTO telegram_users (telegram_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
                (telegram_id, username, first_name, last_name)
            )
            await db.commit()

    @staticmethod
    async def get_telegram_user(telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получить Telegram пользователя"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM telegram_users WHERE telegram_id = ?", (telegram_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    async def link_marzban_user(telegram_id: int, marzban_username: str):
        """Связать Telegram пользователя с Marzban пользователем"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                "UPDATE telegram_users SET marzban_username = ? WHERE telegram_id = ?",
                (marzban_username, telegram_id)
            )
            await db.commit()

    @staticmethod
    async def get_user_subscription_from_marzban(telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получить подписку пользователя из Marzban API"""
        from utils.marzban_api import marzban_api

        # Сначала получаем связанного пользователя Marzban
        telegram_user = await Database.get_telegram_user(telegram_id)
        if not telegram_user or not telegram_user.get('marzban_username'):
            return None

        try:
            # Получаем данные пользователя из Marzban
            marzban_user = await marzban_api.get_user(telegram_user['marzban_username'])
            if marzban_user:
                # Преобразуем данные Marzban в удобный формат
                return {
                    'username': marzban_user['username'],
                    'status': marzban_user['status'],
                    'used_traffic': marzban_user['used_traffic'],
                    'data_limit': marzban_user['data_limit'],
                    'expire': marzban_user.get('expire'),
                    'created_at': marzban_user['created_at'],
                    'subscription_url': marzban_user.get('subscription_url', ''),
                    'online_at': marzban_user.get('online_at'),
                    'links': marzban_user.get('links', [])
                }
            return None
        except Exception as e:
            logger.error(f"Ошибка получения пользователя из Marzban: {e}")
            return None

    @staticmethod
    async def get_all_marzban_users() -> List[Dict[str, Any]]:
        """Получить всех пользователей из Marzban"""
        from utils.marzban_api import marzban_api
        try:
            users = await marzban_api.get_all_users()
            return users
        except Exception as e:
            logger.error(f"Ошибка получения всех пользователей из Marzban: {e}")
            return []

    @staticmethod
    async def create_marzban_subscription(telegram_id: int, expire_days: int) -> Optional[str]:
        """Создать подписку в Marzban"""
        from utils.marzban_api import marzban_api

        # Генерируем уникальное имя пользователя
        marzban_username = f"tg_{telegram_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            # Создаем пользователя в Marzban
            marzban_user = await marzban_api.create_user(
                username=marzban_username,
                expire_days=expire_days
            )

            # Связываем Telegram пользователя с Marzban пользователем
            await Database.link_marzban_user(telegram_id, marzban_username)

            logger.info(f"Создан пользователь в Marzban: {marzban_username}")
            return marzban_username

        except Exception as e:
            logger.error(f"Ошибка создания пользователя в Marzban: {e}")
            return None

    @staticmethod
    async def create_payment(telegram_id: int, marzban_username: str, yookassa_payment_id: str, amount: int):
        """Создать платеж"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                "INSERT INTO payments (telegram_id, marzban_username, yookassa_payment_id, amount) VALUES (?, ?, ?, ?)",
                (telegram_id, marzban_username, yookassa_payment_id, amount)
            )
            await db.commit()

    @staticmethod
    async def update_payment_status(yookassa_payment_id: str, status: str):
        """Обновить статус платежа"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                "UPDATE payments SET status = ? WHERE yookassa_payment_id = ?",
                (status, yookassa_payment_id)
            )
            await db.commit()

    @staticmethod
    async def get_all_telegram_users() -> List[Dict[str, Any]]:
        """Получить всех Telegram пользователей (для админов)"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM telegram_users ORDER BY created_at DESC")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    async def get_payment_history(telegram_id: int = None) -> List[Dict[str, Any]]:
        """Получить историю платежей"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            if telegram_id:
                cursor = await db.execute(
                    "SELECT * FROM payments WHERE telegram_id = ? ORDER BY created_at DESC",
                    (telegram_id,)
                )
            else:
                cursor = await db.execute("SELECT * FROM payments ORDER BY created_at DESC")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    async def get_user_stats() -> Dict[str, Any]:
        """Получить статистику пользователей"""
        try:
            # Статистика из Marzban
            marzban_users = await Database.get_all_marzban_users()

            # Статистика из локальной БД
            telegram_users = await Database.get_all_telegram_users()
            payments = await Database.get_payment_history()

            active_users = len([u for u in marzban_users if u.get('status') == 'active'])
            total_traffic = sum(u.get('used_traffic', 0) for u in marzban_users)
            successful_payments = len([p for p in payments if p.get('status') == 'succeeded'])

            return {
                'total_marzban_users': len(marzban_users),
                'active_users': active_users,
                'total_telegram_users': len(telegram_users),
                'total_payments': len(payments),
                'successful_payments': successful_payments,
                'total_traffic_bytes': total_traffic
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {}
