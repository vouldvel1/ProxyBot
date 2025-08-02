"""
Административные команды с интеграцией Marzban
"""

from aiogram import Router, types, F
from aiogram.types import CallbackQuery
from aiogram.filters import Command
import logging
from datetime import datetime

from keyboards.inline import admin_keyboard, back_to_main_keyboard
from bot.database import Database
from config.settings import settings

router = Router()
logger = logging.getLogger(__name__)

def is_admin(user_id: int) -> bool:
    """Проверка является ли пользователь админом"""
    return user_id in settings.ADMIN_IDS

@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    """Административная панель"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return

    text = """
👨‍💼 <b>Административная панель</b>

Добро пожаловать в панель управления ботом.
Данные пользователей берутся из Marzban API.
Выберите нужное действие:
"""

    await message.answer(
        text,
        reply_markup=admin_keyboard()
    )

@router.callback_query(lambda c: c.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    """Список пользователей из Marzban"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав доступа", show_alert=True)
        return

    try:
        # Получаем пользователей из Marzban
        marzban_users = await Database.get_all_marzban_users()

        if not marzban_users:
            text = "👥 <b>Пользователи Marzban</b>\n\nПользователей пока нет."
        else:
            text = f"👥 <b>Пользователи Marzban ({len(marzban_users)})</b>\n\n"

            for i, user in enumerate(marzban_users[:10], 1):  # Показываем первых 10
                username = user.get('username', 'Без имени')
                status = user.get('status', 'unknown')
                used_gb = user.get('used_traffic', 0) / (1024**3)

                status_emoji = {
                    'active': '✅',
                    'limited': '⚠️',
                    'expired': '❌',
                    'disabled': '🚫'
                }.get(status, '❓')

                text += f"{i}. {status_emoji} {username}\n"
                text += f"   Статус: {status}\n"
                text += f"   Трафик: {used_gb:.2f} GB\n\n"

            if len(marzban_users) > 10:
                text += f"... и еще {len(marzban_users) - 10} пользователей"

        await callback.message.edit_text(
            text,
            reply_markup=admin_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка получения пользователей Marzban: {e}")
        await callback.answer("❌ Ошибка получения данных из Marzban", show_alert=True)

    await callback.answer()

@router.callback_query(lambda c: c.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    """Статистика из Marzban и локальной БД"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав доступа", show_alert=True)
        return

    try:
        stats = await Database.get_user_stats()

        text = f"""
📊 <b>Статистика бота и Marzban</b>

👥 <b>Пользователи Marzban:</b>
• Всего: {stats.get('total_marzban_users', 0)}
• Активных: {stats.get('active_users', 0)}

📱 <b>Telegram пользователи:</b>
• Зарегистрировано в боте: {stats.get('total_telegram_users', 0)}

💰 <b>Платежи:</b>
• Всего платежей: {stats.get('total_payments', 0)}
• Успешных: {stats.get('successful_payments', 0)}

📊 <b>Трафик:</b>
• Использовано: {stats.get('total_traffic_bytes', 0) / (1024**3):.2f} GB

<i>Данные синхронизируются с Marzban API</i>
"""

        await callback.message.edit_text(
            text,
            reply_markup=admin_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        await callback.answer("❌ Ошибка получения статистики", show_alert=True)

    await callback.answer()

@router.callback_query(lambda c: c.data == "admin_payments")
async def admin_payments(callback: CallbackQuery):
    """История платежей"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав доступа", show_alert=True)
        return

    try:
        payments = await Database.get_payment_history()

        if not payments:
            text = "💰 <b>История платежей</b>\n\nПлатежей пока нет."
        else:
            text = f"💰 <b>История платежей ({len(payments)})</b>\n\n"

            for i, payment in enumerate(payments[:10], 1):
                amount = payment.get('amount', 0)
                status = payment.get('status', 'unknown')
                created = payment.get('created_at', '')[:16] if payment.get('created_at') else 'Неизвестно'
                marzban_user = payment.get('marzban_username', 'N/A')

                status_emoji = {
                    'succeeded': '✅',
                    'pending': '⏳',
                    'canceled': '❌'
                }.get(status, '❓')

                text += f"{i}. {status_emoji} {amount} ₽\n"
                text += f"   Статус: {status}\n"
                text += f"   Пользователь: {marzban_user}\n"
                text += f"   Дата: {created}\n\n"

            if len(payments) > 10:
                text += f"... и еще {len(payments) - 10} платежей"

        await callback.message.edit_text(
            text,
            reply_markup=admin_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка получения платежей: {e}")
        await callback.answer("❌ Ошибка получения платежей", show_alert=True)

    await callback.answer()

@router.callback_query(lambda c: c.data == "admin_broadcast")
async def admin_broadcast(callback: CallbackQuery):
    """Рассылка"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав доступа", show_alert=True)
        return

    text = """
📢 <b>Рассылка сообщений</b>

<b>Доступные команды:</b>
• <code>/broadcast текст</code> - рассылка всем пользователям бота
• <code>/stats</code> - быстрая статистика

<b>Особенности:</b>
• Рассылка отправляется только Telegram пользователям
• Пользователи Marzban доступны через панель управления
• Статистика агрегируется из обеих систем

<i>Для отправки используйте команду /broadcast</i>
"""

    await callback.message.edit_text(
        text,
        reply_markup=admin_keyboard()
    )
    await callback.answer()

@router.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message):
    """Рассылка сообщения"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return

    # Получаем текст для рассылки
    text_to_broadcast = message.text.replace("/broadcast", "").strip()

    if not text_to_broadcast:
        await message.answer("❌ Укажите текст для рассылки.\nПример: <code>/broadcast Привет всем!</code>")
        return

    try:
        users = await Database.get_all_telegram_users()

        if not users:
            await message.answer("❌ Нет пользователей для рассылки.")
            return

        status_message = await message.answer(f"📤 Начинаю рассылку для {len(users)} пользователей...")

        success_count = 0
        failed_count = 0

        for user in users:
            try:
                await message.bot.send_message(user['telegram_id'], text_to_broadcast)
                success_count += 1
            except Exception as e:
                failed_count += 1
                logger.warning(f"Не удалось отправить сообщение пользователю {user['telegram_id']}: {e}")

        await status_message.edit_text(
            f"✅ <b>Рассылка завершена!</b>\n\n"
            f"• Успешно: {success_count}\n"
            f"• Ошибок: {failed_count}\n"
            f"• Всего: {len(users)}"
        )

    except Exception as e:
        logger.error(f"Ошибка рассылки: {e}")
        await message.answer("❌ Ошибка при выполнении рассылки.")

@router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """Быстрая статистика"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return

    try:
        stats = await Database.get_user_stats()

        text = f"""
📊 <b>Быстрая статистика</b>

👥 Marzban пользователей: {stats.get('total_marzban_users', 0)}
✅ Активных: {stats.get('active_users', 0)}
📱 Telegram пользователей: {stats.get('total_telegram_users', 0)}
💰 Успешных платежей: {stats.get('successful_payments', 0)}
📊 Использовано трафика: {stats.get('total_traffic_bytes', 0) / (1024**3):.1f} GB

🗓 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}

Используйте /admin для подробной панели управления.
"""

        await message.answer(text)

    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        await message.answer("❌ Ошибка получения статистики из Marzban.")
