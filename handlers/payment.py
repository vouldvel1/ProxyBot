"""
Обработчик платежей с интеграцией Marzban API
"""

from aiogram import Router, types, F
from aiogram.types import CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
import logging
from datetime import datetime
import asyncio

from keyboards.inline import (
    regions_keyboard, 
    subscription_plans_keyboard, 
    payment_keyboard,
    back_to_main_keyboard,
    main_menu_keyboard
)
from bot.database import Database
from utils.marzban_api import marzban_api
from utils.payment_utils import payment_utils
from config.settings import settings

router = Router()
logger = logging.getLogger(__name__)

# Временное хранение выбора пользователя
user_selections = {}

@router.callback_query(lambda c: c.data == "buy_subscription")
async def buy_subscription(callback: CallbackQuery):
    """Начать покупку подписки"""
    text = """
🌍 <b>Выбор региона сервера</b>

Выберите регион, где будет расположен ваш прокси-сервер:

• 🇫🇮 <b>Финляндия</b> - Низкая задержка

Выберите регион из списка ниже:
"""

    await callback.message.edit_text(
        text,
        reply_markup=regions_keyboard()
    )
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("region_"))
async def select_region(callback: CallbackQuery):
    """Выбор региона"""
    user_id = callback.from_user.id
    region_code = callback.data.replace("region_", "")

    region_names = {
        "finland": "🇫🇮 Финляндия"
    }

    region_name = region_names.get(region_code, region_code)

    # Сохраняем выбор пользователя
    if user_id not in user_selections:
        user_selections[user_id] = {}
    user_selections[user_id]['region'] = region_name

    text = f"""
📋 <b>Выбор тарифного плана</b>

Регион: {region_name}

Выберите подходящий тарифный план:

• 📅 <b>1 месяц</b> - 180₽
  отлично для тестирования

• 📅 <b>3 месяца</b> - 490₽ 
  экономия 10%

• 📅 <b>6 месяцев</b> - 860₽
  экономия 20%

<b>Во всех тарифах:</b>
• Высокая скорость подключения
• 24/7 поддержка
• протокол VLESS
"""

    await callback.message.edit_text(
        text,
        reply_markup=subscription_plans_keyboard()
    )
    await callback.answer()

@router.callback_query(lambda c: c.data == "back_to_regions")
async def back_to_regions(callback: CallbackQuery):
    """Возврат к выбору региона"""
    text = """
🌍 <b>Выбор региона сервера</b>

Выберите регион, где будет расположен ваш прокси-сервер:
"""

    await callback.message.edit_text(
        text,
        reply_markup=regions_keyboard()
    )
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("plan_"))
async def select_plan(callback: CallbackQuery):
    """Выбор тарифного плана и создание пользователя в Marzban"""
    user_id = callback.from_user.id
    plan_data = callback.data.replace("plan_", "")

    # Парсим данные плана
    plan_info = {
        "1_month_180": {"months": 1, "price": 180, "name": "1 месяц"},
        "3_months_490": {"months": 3, "price": 490, "name": "3 месяца"},
        "6_months_860": {"months": 6, "price": 860, "name": "6 месяцев"}
    }

    plan = plan_info.get(plan_data)
    if not plan:
        await callback.answer("❌ Неверный тарифный план", show_alert=True)
        return

    # Сохраняем выбор пользователя
    if user_id not in user_selections:
        user_selections[user_id] = {}

    user_selections[user_id]['plan'] = plan

    user_selection = user_selections[user_id]
    region = user_selection.get('region', 'Неизвестно')

    try:
        # Добавляем пользователя в локальную БД если его нет
        await Database.add_telegram_user(
            telegram_id=user_id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
            last_name=callback.from_user.last_name
        )

        # Создаем пользователя в Marzban
        #marzban_username = await Database.create_marzban_subscription(
        #    telegram_id=user_id,
        #    expire_days=plan['months'] * 30
        #)

        #if not marzban_username:
        #    await callback.answer("❌ Ошибка создания подписки в Marzban", show_alert=True)
        #    return

        user_selections[user_id]['marzban_username'] = user_id

        # Используем встроенные платежи Telegram
        prices = [LabeledPrice(label=f"Подписка {plan['name']}", amount=plan['price'] * 100)]

        await callback.bot.send_invoice(
            chat_id = callback.from_user.id,
            title="Подписка на прокси-сервер",
            description=f"Подписка на {plan['name']}\nРегион: {region}",
            provider_token=settings.YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=prices,
            start_parameter="subscription_payment",
            payload=f"marzban_{user_id}",
            protect_content=True
        )
    except Exception as e:
        logger.error(f"Ошибка создания платежа и пользователя Marzban: {e}")
        await callback.answer("❌ Ошибка создания подписки. Попробуйте позже.", show_alert=True)

    await callback.answer()

@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    """Обработка предварительной проверки платежа"""
    logger.info(f"Предварительная проверка платежа: {pre_checkout_query.id}")
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    """Обработка успешного платежа"""
    payment = message.successful_payment
    user_id = message.from_user.id

    logger.info(f"Успешный платеж от пользователя {user_id}: {payment.telegram_payment_charge_id}")

    try:
        # Извлекаем marzban_username из payload
        payload = payment.invoice_payload
        if payload.startswith("marzban_"):
            username = payload.replace("marzban_", "")
            if int(user_selections[user_id]['marzban_username']) != int(username):
                await message.answer(f"Пользователи не одинаковые ({user_selections[user_id]['marzban_username']}) != ({username})", show_alert=True)
                return
            
            marzban_username = await Database.create_marzban_subscription(
            telegram_id=user_id,
            expire_days=user_selections[user_id].get("plan")['months'] * 30
            )

            if not marzban_username:
                await message.answer("❌ Ошибка создания подписки в Marzban", show_alert=True)
                return
            # Сохраняем информацию о платеже
            await Database.create_payment(
                telegram_id=user_id,
                marzban_username=marzban_username,
                yookassa_payment_id=payment.telegram_payment_charge_id,
                amount=int(payment.total_amount / 100)
            )

            # Обновляем статус платежа
            await Database.update_payment_status(
                payment.telegram_payment_charge_id, 
                "succeeded"
            )

            

            # Получаем информацию о созданной подписке из Marzban
            subscription = await Database.get_user_subscription_from_marzban(user_id)

            if subscription:
                subscription_url = await marzban_api.get_user_subscription_url(marzban_username)

                success_text = f"""
✅ <b>Платеж успешно обработан!</b>

🎉 Ваша подписка активирована в Marzban!

📋 <b>Детали подписки:</b>
• Пользователь: {marzban_username}
• Статус: {subscription['status']}

🔗 <b>Ссылка для подключения:</b>
<code>{subscription_url}</code>

Используйте главное меню для получения QR-кода и инструкций по подключению.
"""

                await message.answer(
                    success_text,
                    reply_markup=main_menu_keyboard()
                )
            else:
                await message.answer(
                    "✅ Платеж получен! Подписка создается в Marzban...\n"
                    "Используйте /start → 'Моя подписка' для просмотра статуса."
                )

    except Exception as e:
        logger.error(f"Ошибка обработки платежа: {e}")
        await message.answer(
            "❌ Ошибка активации подписки. Платеж получен, обратитесь в поддержку.",
            reply_markup=main_menu_keyboard()
        )

@router.callback_query(lambda c: c.data == "check_payment")
async def check_payment(callback: CallbackQuery):
    """Проверка статуса платежа"""
    user_id = callback.from_user.id

    # Проверяем есть ли активная подписка в Marzban
    subscription = await Database.get_user_subscription_from_marzban(user_id)

    if subscription and subscription['status'] == 'active':
        await callback.answer("✅ Платеж подтвержден! Подписка активна в Marzban.", show_alert=True)

        # Показываем информацию о подписке
        expire_date = "Не установлено"
        if subscription.get('expire'):
            expire_timestamp = subscription['expire']
            expire_dt = datetime.fromtimestamp(expire_timestamp)
            expire_date = expire_dt.strftime('%d.%m.%Y')

        text = f"""
✅ <b>Подписка активна в Marzban!</b>

📋 <b>Информация:</b>
• Пользователь: {subscription['username']}
• Статус: {subscription['status']}
• Истекает: {expire_date}
• Лимит: {subscription.get('data_limit', 0) / (1024**3):.0f} GB

Используйте главное меню для управления подпиской.
"""

        await callback.message.edit_text(
            text,
            reply_markup=main_menu_keyboard()
        )
    else:
        await callback.answer("⏳ Подписка еще не активирована или истекла. Попробуйте через минуту.", show_alert=True)

@router.callback_query(lambda c: c.data == "cancel_payment")
async def cancel_payment(callback: CallbackQuery):
    """Отмена платежа"""
    user_id = callback.from_user.id

    # Очищаем выбор пользователя
    if user_id in user_selections:
        marzban_username = user_selections[user_id].get('marzban_username')
        if marzban_username:
            try:
                # Удаляем созданного пользователя из Marzban если платеж отменен
                await marzban_api.delete_user(marzban_username)
                logger.info(f"Удален неоплаченный пользователь из Marzban: {marzban_username}")
            except Exception as e:
                logger.error(f"Ошибка удаления пользователя при отмене: {e}")

        del user_selections[user_id]

    text = """
❌ <b>Платеж отменен</b>

Созданная подписка удалена из Marzban.
Вы можете начать покупку заново из главного меню.
"""

    await callback.message.edit_text(
        text,
        reply_markup=main_menu_keyboard()
    )
    await callback.answer("Платеж отменен")
