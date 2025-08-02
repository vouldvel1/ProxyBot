"""
Работа с Marzban API
"""

import aiohttp
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json

from config.settings import settings

logger = logging.getLogger(__name__)

class MarzbanAPI:
    """Класс для работы с Marzban API"""

    def __init__(self):
        self.api_url = settings.MARZBAN_API_URL.rstrip('/')
        self.username = settings.MARZBAN_USERNAME
        self.password = settings.MARZBAN_PASSWORD
        self.token = None
        self.token_expires = None

    async def _get_token(self) -> str:
        """Получить токен авторизации"""
        if self.token and self.token_expires and datetime.now() < self.token_expires:
            return self.token

        async with aiohttp.ClientSession() as session:
            auth_data = {
                "grant_type": "password",
                "username": self.username,
                "password": self.password
            }
            header = {
                "content-type": "application/x-www-form-urlencoded"
            }

            async with session.post(
                f"{self.api_url}/api/admin/token",
                data=auth_data,
                headers=header
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.token = data.get("access_token")
                    # Токен действует 24 часа, обновляем за час до истечения
                    self.token_expires = datetime.now() + timedelta(hours=23)
                    logger.info("Получен новый токен Marzban")
                    return self.token
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка получения токена: {response.status} - {error_text}")
                    raise Exception(f"Не удалось получить токен: {response.status}")

    async def get_all_users(self, offset: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Получить всех пользователей из Marzban"""
        token = await self._get_token()

        headers = {
            "Authorization": f"Bearer {token}"
        }

        params = {
            "offset": offset,
            "limit": limit
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_url}/api/users",
                headers=headers,
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    users = data.get("users", [])
                    total = data.get("total", 0)

                    # Если есть еще пользователи, получаем их рекурсивно
                    if len(users) == limit and offset + limit < total:
                        more_users = await self.get_all_users(offset + limit, limit)
                        users.extend(more_users)

                    logger.info(f"Получено {len(users)} пользователей из Marzban")
                    return users
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка получения пользователей: {response.status} - {error_text}")
                    raise Exception(f"Не удалось получить пользователей: {response.status}")

    async def create_user(self, username: str, expire_days: int) -> Dict[str, Any]:
        """Создать пользователя в Marzban"""
        token = await self._get_token()

        expire_timestamp = int((datetime.now() + timedelta(days=expire_days)).timestamp())

        user_data = {
            "username": username,
             "inbounds": {
                    "vless": [
                        "VLESS TCP REALITY"
                    ],
            },
            "proxies": {
                "vless": {
                    "flow": "xtls-rprx-vision"
                }
            },
            "data_limit": 0,
            "expire": expire_timestamp,
            "data_limit_reset_strategy": "no_reset",
            "status": "active"
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}/api/user",
                json=user_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Пользователь {username} создан в Marzban")
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка создания пользователя: {response.status} - {error_text}")
                    raise Exception(f"Не удалось создать пользователя: {response.status}")

    async def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о пользователе"""
        token = await self._get_token()

        headers = {
            "Authorization": f"Bearer {token}"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_url}/api/user/{username}",
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    return None
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка получения пользователя: {response.status} - {error_text}")
                    raise Exception(f"Не удалось получить пользователя: {response.status}")

    async def get_user_usage(self, username: str) -> Optional[Dict[str, Any]]:
        """Получить статистику использования пользователя"""
        token = await self._get_token()

        headers = {
            "Authorization": f"Bearer {token}"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_url}/api/user/{username}/usage",
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    return None
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка получения статистики пользователя: {response.status} - {error_text}")
                    return None

    async def get_user_subscription_url(self, username: str) -> str:
        """Получить URL подписки пользователя"""
        return f"{self.api_url}/sub/{username}"

    async def delete_user(self, username: str):
        """Удалить пользователя"""
        token = await self._get_token()

        headers = {
            "Authorization": f"Bearer {token}"
        }

        async with aiohttp.ClientSession() as session:
            async with session.delete(
                f"{self.api_url}/api/user/{username}",
                headers=headers
            ) as response:
                if response.status == 200:
                    logger.info(f"Пользователь {username} удален из Marzban")
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка удаления пользователя: {response.status} - {error_text}")

    async def modify_user(self, username: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Изменить пользователя"""
        token = await self._get_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.put(
                f"{self.api_url}/api/user/{username}",
                json=user_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Пользователь {username} изменен в Marzban")
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка изменения пользователя: {response.status} - {error_text}")
                    raise Exception(f"Не удалось изменить пользователя: {response.status}")

    async def get_system_stats(self) -> Dict[str, Any]:
        """Получить системную статистику"""
        token = await self._get_token()

        headers = {
            "Authorization": f"Bearer {token}"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_url}/api/system",
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка получения системной статистики: {response.status} - {error_text}")
                    return {}

# Глобальный экземпляр API
marzban_api = MarzbanAPI()
