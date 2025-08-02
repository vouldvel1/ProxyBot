"""
Утилиты для работы с платежами через ЮКасса
"""

import yookassa
from yookassa import Configuration, Payment
import logging
from typing import Dict, Any
import uuid

from config.settings import settings

logger = logging.getLogger(__name__)

# Настройка ЮКасса
Configuration.account_id = settings.YOOKASSA_SHOP_ID
Configuration.secret_key = settings.YOOKASSA_SECRET_KEY

class PaymentUtils:
    """Утилиты для работы с платежами"""

    @staticmethod
    def create_payment(amount: int, description: str, return_url: str = None) -> Dict[str, Any]:
        """Создать платеж"""
        try:
            payment = Payment.create({
                "amount": {
                    "value": f"{amount}.00",
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": return_url or "https://t.me/your_bot"
                },
                "capture": True,
                "description": description,
                "metadata": {
                    "source": "telegram_bot"
                }
            }, str(uuid.uuid4()))

            logger.info(f"Создан платеж: {payment.id}")
            return {
                "id": payment.id,
                "status": payment.status,
                "confirmation_url": payment.confirmation.confirmation_url if payment.confirmation else None,
                "amount": payment.amount.value
            }
        except Exception as e:
            logger.error(f"Ошибка создания платежа: {e}")
            raise

    @staticmethod
    def get_payment_status(payment_id: str) -> Dict[str, Any]:
        """Получить статус платежа"""
        try:
            payment = Payment.find_one(payment_id)
            return {
                "id": payment.id,
                "status": payment.status,
                "paid": payment.paid,
                "amount": payment.amount.value
            }
        except Exception as e:
            logger.error(f"Ошибка получения статуса платежа {payment_id}: {e}")
            raise

    @staticmethod
    def format_price(amount: int) -> str:
        """Форматировать цену для отображения"""
        return f"{amount:,} ₽".replace(",", " ")

payment_utils = PaymentUtils()
