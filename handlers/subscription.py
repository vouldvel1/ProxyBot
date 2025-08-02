"""
Обработчик управления подписками с Marzban API
"""

from aiogram import Router, types
from aiogram.types import CallbackQuery, BufferedInputFile, InputMediaPhoto
from aiogram.filters import Command
from datetime import datetime


from keyboards.inline import (
    regions_keyboard, 
    subscription_plans_keyboard, 
    subscription_info_keyboard,
    back_to_main_keyboard
)
from bot.database import Database
from utils.marzban_api import marzban_api
from utils.qr_generator import qr_generator
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(lambda c: c.data == "my_subscription")
async def my_subscription(callback: CallbackQuery):
    """Информация о подписке пользователя из Marzban"""
    user_id = callback.from_user.id
    subscription = await Database.get_user_subscription_from_marzban(user_id)

    if not subscription:
        text = """
❌ <b>У вас нет активной подписки</b>

Чтобы приобрести подписку, нажмите кнопку "Купить подписку" в главном меню.
"""
        await callback.message.edit_text(
            text,
            reply_markup=back_to_main_keyboard()
        )
    else:
        try:
            # Получаем дополнительную статистику
            username = subscription['username']
            usage_stats = await marzban_api.get_user_usage(username)

            # Конвертируем timestamp в дату
            expire_date = "Не установлено"
            if subscription.get('expire'):
                expire_timestamp = subscription['expire']
                expire_dt = datetime.fromtimestamp(expire_timestamp)
                expire_date = expire_dt.strftime('%d.%m.%Y')
                days_left = max(0, (expire_dt - datetime.now()).days)
            else:
                days_left = 0

            # Конвертируем трафик в GB
            used_gb = subscription.get('used_traffic', 0) / (1024**3)

            status_emoji = "✅" if subscription['status'] == 'active' else "❌"
            status_text = {
                'active': 'Активна',
                'limited': 'Ограничена',
                'expired': 'Истекла',
                'disabled': 'Отключена'
            }.get(subscription['status'], subscription['status'])

            text = f"""
{status_emoji} <b>Ваша подписка (Marzban)</b>

📋 <b>Информация:</b>
• Пользователь: {username}
• Статус: {status_text}
• Дней осталось: {days_left}
• Истекает: {expire_date}

💾 <b>Использование трафика: {used_gb:.2f} GB</b>

Данные синхронизируются с Marzban панелью в реальном времени.
"""

            await callback.message.edit_text(
                text,
                reply_markup=subscription_info_keyboard()
            )

        except Exception as e:
            logger.error(f"Ошибка получения информации о подписке: {e}")
            text = "❌ Ошибка получения данных из Marzban. Попробуйте позже."
            await callback.message.edit_text(
                text,
                reply_markup=back_to_main_keyboard()
            )

    await callback.answer()

@router.callback_query(lambda c: c.data == "get_keys")
async def get_keys(callback: CallbackQuery):
    """Получить ключи подключения из Marzban"""
    await callback.message.delete()
    user_id = callback.from_user.id
    subscription = await Database.get_user_subscription_from_marzban(user_id)

    if not subscription:
        await callback.answer("❌ У вас нет активной подписки", show_alert=True)
        return

    try:
        subscription_url = subscription.get("subscription_url")
        # Получаем прямые ссылки подключения
        links = subscription.get('links', [])

        text = f"""
🔑 <b>Ваши ключи подключения</b>

📱 <b>Ссылка для подписки:</b>
<code>{subscription_url}</code>

📱 <b>Прямой ключ для подписки:</b>
<code>{links[0]}</code>

<b>Инструкция по подключению:</b>
1. Скопируйте ссылку подписки выше
2. Откройте ваше VPN приложение
3. Добавьте подписку по ссылке
4. Обновите серверы

<b>Рекомендуемые приложения:</b>
• Android/iOS: V2rayTun
• Windows: V2rayTun, Hiddify
• macOS: V2rayTun
"""

        await callback.message.answer(
            text,
            reply_markup=subscription_info_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка получения ключей: {e}")
        await callback.answer("❌ Ошибка получения ключей из Marzban", show_alert=True)

    await callback.answer()

@router.callback_query(lambda c: c.data == "get_qr_code")
async def get_qr_code(callback: CallbackQuery):
    """Получить QR-код для подключения"""
    user_id = callback.from_user.id
    subscription = await Database.get_user_subscription_from_marzban(user_id)

    if not subscription:
        await callback.answer("❌ У вас нет активной подписки", show_alert=True)
        return

    try:
        username = subscription['username']
        subscription_url = await marzban_api.get_user_subscription_url(username)
        qr_bytes = qr_generator.generate_subscription_qr(subscription_url)

        qr_file = BufferedInputFile(qr_bytes, filename="subscription_qr.png")

        # Определяем дату истечения
        expire_date = "Не установлено"
        if subscription.get('expire'):
            expire_timestamp = subscription['expire']
            expire_dt = datetime.fromtimestamp(expire_timestamp)
            expire_date = expire_dt.strftime('%d.%m.%Y')

             

        caption = f"""
📱 <b>QR-код для подключения (Marzban)</b>

Отсканируйте этот QR-код в вашем VPN приложении для автоматической настройки.

<b>Пользователь:</b> {username}
<b>Статус:</b> {subscription['status']}
<b>Подписка действует до:</b> {expire_date}
"""
        media = InputMediaPhoto(media=qr_file, caption=caption, parse_mode="HTML") 
        await callback.message.edit_media(media=media, reply_markup=subscription_info_keyboard())

    except Exception as e:
        logger.error(f"Ошибка генерации QR-кода: {e}")
        await callback.answer("❌ Ошибка генерации QR-кода", show_alert=True)

    await callback.answer()

@router.callback_query(lambda c: c.data == "renew_subscription")
async def renew_subscription(callback: CallbackQuery):
    """Продлить подписку"""
    await callback.message.delete()
    text = """
🔄 <b>Продление подписки</b>

Для продления подписки выберите регион и тарифный план.
"""

    await callback.message.answer(
        text,
        reply_markup=regions_keyboard()
    )
    await callback.answer()

@router.message(Command("subscription"))
async def cmd_subscription(message: types.Message):
    """Команда информации о подписке"""
    user_id = message.from_user.id
    subscription = await Database.get_user_subscription_from_marzban(user_id)

    if not subscription:
        text = "❌ У вас нет активной подписки. Используйте /start для покупки."
    else:
        expire_date = "Не установлено"
        days_left = 0

        if subscription.get('expire'):
            expire_timestamp = subscription['expire']
            expire_dt = datetime.fromtimestamp(expire_timestamp)
            expire_date = expire_dt.strftime('%d.%m.%Y')
            days_left = max(0, (expire_dt - datetime.now()).days)

        used_gb = subscription.get('used_traffic', 0) / (1024**3)

        text = f"""
📊 <b>Информация о подписке (Marzban)</b>

• Пользователь: {subscription['username']}
• Статус: {subscription['status']}
• Дней осталось: {days_left}
• Истекает: {expire_date}
• Использовано: {used_gb:.2f} GB

Используйте /start для управления подпиской.
"""

    await message.answer(text)
