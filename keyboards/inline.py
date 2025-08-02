"""
Инлайн клавиатуры
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню"""
    builder = InlineKeyboardBuilder()

    builder.add(InlineKeyboardButton(
        text="💳 Купить подписку",
        callback_data="buy_subscription"
    ))
    builder.add(InlineKeyboardButton(
        text="📊 Моя подписка",
        callback_data="my_subscription"
    ))
    builder.add(InlineKeyboardButton(
        text="🆘 Помощь",
        callback_data="help"
    ))

    builder.adjust(1)
    return builder.as_markup()

def regions_keyboard() -> InlineKeyboardMarkup:
    """Выбор региона"""
    builder = InlineKeyboardBuilder()

    regions = [
        ("🇫🇮 Финляндия", "region_finland")
    ]

    for region_name, callback_data in regions:
        builder.add(InlineKeyboardButton(
            text=region_name,
            callback_data=callback_data
        ))

    builder.add(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="back_to_main"
    ))

    builder.adjust(1)
    return builder.as_markup()

def subscription_plans_keyboard() -> InlineKeyboardMarkup:
    """Тарифные планы"""
    builder = InlineKeyboardBuilder()

    plans = [
        ("📅 1 месяц - 180₽", "plan_1_month_180"),
        ("📅 3 месяца - 490₽", "plan_3_months_490"),
        ("📅 6 месяцев - 860₽", "plan_6_months_860")
    ]

    for plan_name, callback_data in plans:
        builder.add(InlineKeyboardButton(
            text=plan_name,
            callback_data=callback_data
        ))

    builder.add(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="back_to_regions"
    ))

    builder.adjust(1)
    return builder.as_markup()

def payment_keyboard():
    """Клавиатура для оплаты"""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            # Платёжная кнопка автоматически добавится Telegram
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_payment")]
            ]
        )

def subscription_info_keyboard() -> InlineKeyboardMarkup:
    """Управление подпиской"""
    builder = InlineKeyboardBuilder()

    builder.add(InlineKeyboardButton(
        text="🔑 Получить ключи",
        callback_data="get_keys"
    ))
    builder.add(InlineKeyboardButton(
        text="📱 QR-код",
        callback_data="get_qr_code"
    ))
    builder.add(InlineKeyboardButton(
        text="🔄 Обновить подписку",
        callback_data="renew_subscription"
    ))
    builder.add(InlineKeyboardButton(
        text="🔙 Главное меню",
        callback_data="back_to_main"
    ))

    builder.adjust(2, 1, 1)
    return builder.as_markup()

def admin_keyboard() -> InlineKeyboardMarkup:
    """Административная панель"""
    builder = InlineKeyboardBuilder()

    builder.add(InlineKeyboardButton(
        text="👥 Пользователи",
        callback_data="admin_users"
    ))
    builder.add(InlineKeyboardButton(
        text="💰 Платежи",
        callback_data="admin_payments"
    ))
    builder.add(InlineKeyboardButton(
        text="📊 Статистика",
        callback_data="admin_stats"
    ))
    builder.add(InlineKeyboardButton(
        text="📢 Рассылка",
        callback_data="admin_broadcast"
    ))

    builder.adjust(2)
    return builder.as_markup()

def back_to_main_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата в главное меню"""
    builder = InlineKeyboardBuilder()
    

    builder.add(InlineKeyboardButton(
        text="🔙 Главное меню",
        callback_data="back_to_main"
    ))

    return builder.as_markup()
