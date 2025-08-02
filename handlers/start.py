"""
Обработчик команды /start и главного меню
"""

from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import CallbackQuery

from keyboards.inline import main_menu_keyboard, back_to_main_keyboard
from bot.database import Database

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    user = message.from_user

    # Добавляем пользователя в БД
    await Database.add_telegram_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )

    welcome_text = f"""
👋 <b>Добро пожаловать, {user.first_name}!</b>

🔐 Этот бот поможет вам приобрести и управлять подпиской на прокси-сервер через Marzban.

<b>Возможности:</b>
• 💳 Покупка подписки с оплатой через ЮКасса
• 🌍 Выбор региона сервера
• 📱 Получение QR-кодов для подключения
• 📊 Просмотр информации о вашей подписке из Marzban
• ⏰ Отслеживание срока действия в реальном времени

Выберите действие из меню ниже:
"""

    await message.answer(
        welcome_text,
        reply_markup=main_menu_keyboard()
    )

@router.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.delete()
    user = callback.from_user

    main_text = f"""
🏠 <b>Главное меню</b>

Привет, {user.first_name}! Выберите действие:
"""

    await callback.message.answer(
        main_text,
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()

@router.callback_query(lambda c: c.data == "help")
async def help_handler(callback: CallbackQuery):
    """Помощь"""
    help_text = """
🆘 <b>Помощь</b>

<b>Как пользоваться ботом:</b>

1. 💳 <b>Покупка подписки:</b>
   • Выберите регион сервера
   • Выберите тарифный план
   • Оплатите через ЮКасса
   • Подписка автоматически создается в Marzban

2. 📱 <b>Подключение:</b>
   • Получите ключи подключения из Marzban
   • Используйте QR-код для быстрой настройки
   • Настройте приложение согласно инструкции

3. 📊 <b>Управление:</b>
   • Проверяйте статус подписки в реальном времени
   • Отслеживайте использование трафика
   • Продлевайте подписку заранее

<b>Поддерживаемые приложения:</b>
• V2rayNG (Android)
• Shadowrocket (iOS)
• V2rayN (Windows)
• V2rayU (macOS)

<b>Особенности:</b>
• Данные синхронизируются с Marzban панелью
• Реальная статистика использования
• Автоматическая активация после оплаты

<b>Нужна помощь?</b>
Обратитесь в поддержку: @support_username
"""

    await callback.message.edit_text(
        help_text,
        reply_markup=back_to_main_keyboard()
    )
    await callback.answer()

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Команда помощи"""
    help_text = """
🆘 <b>Справка по командам:</b>

/start - Запуск бота и главное меню
/help - Эта справка
/subscription - Информация о подписке (из Marzban)
/support - Связаться с поддержкой

Для полного функционала используйте кнопки меню.
"""

    await message.answer(help_text)
