"""
Обработчик админки бота
Доступен только администраторам (проверка по ADMIN_IDS из env)
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.services.database_service import db_service
from bot.services.telegram_service import telegram_service
from bot.config import ADMIN_IDS
from bot.utils.logger import get_logger
from bot.database.models import ReportGenerationStatus, User
from bot.database.database import async_session
from sqlalchemy import select
from datetime import datetime
import os

logger = get_logger(__name__)
router = Router()

# Состояния для FSM
class BroadcastState(StatesGroup):
    waiting_for_message = State()


def is_admin(telegram_id: int) -> bool:
    """Проверить, является ли пользователь администратором"""
    return telegram_id in ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Обработка команды /admin"""
    chat_id = message.chat.id
    
    if not is_admin(chat_id):
        logger.warning(f"⚠️ Попытка доступа к админке от неавторизованного пользователя {chat_id}")
        await message.answer("❌ У вас нет доступа к админке.")
        return
    
    try:
        logger.info(f"🔐 Админка открыта пользователем {chat_id}")
        
        # Создаем клавиатуру с опциями админки
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👥 Все пользователи", callback_data="admin_all_users")],
            [InlineKeyboardButton(text="📊 Бесплатные отчеты", callback_data="admin_free_reports")],
            [InlineKeyboardButton(text="💎 Премиум отчеты", callback_data="admin_premium_reports")],
            [InlineKeyboardButton(text="🔗 Ссылки на отчеты", callback_data="admin_report_links")],
            [InlineKeyboardButton(text="📝 Ответы пользователей", callback_data="admin_answers")],
            [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_menu")]
        ])
        
        admin_text = """
🔐 <b>Админ-панель PRIZMA</b>

Выберите действие:
        """.strip()
        
        await message.answer(
            admin_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке команды /admin для пользователя {chat_id}: {e}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")


@router.callback_query(F.data == "admin_menu")
async def admin_menu(callback: CallbackQuery):
    """Главное меню админки"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа", show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Все пользователи", callback_data="admin_all_users")],
        [InlineKeyboardButton(text="📊 Бесплатные отчеты", callback_data="admin_free_reports")],
        [InlineKeyboardButton(text="💎 Премиум отчеты", callback_data="admin_premium_reports")],
        [InlineKeyboardButton(text="🔗 Ссылки на отчеты", callback_data="admin_report_links")],
        [InlineKeyboardButton(text="📝 Ответы пользователей", callback_data="admin_answers")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")]
    ])
    
    admin_text = """
🔐 <b>Админ-панель PRIZMA</b>

Выберите действие:
    """.strip()
    
    await callback.message.edit_text(
        admin_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_all_users"))
async def admin_all_users(callback: CallbackQuery):
    """Показать всех пользователей с пагинацией"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа", show_alert=True)
        return
    
    try:
        # Получаем номер страницы из callback_data
        page = 1
        if ":" in callback.data:
            try:
                page = int(callback.data.split(":")[1])
            except:
                page = 1
        
        users = await db_service.get_all_users()
        users_per_page = 8  # Меньше пользователей на страницу из-за подробной информации
        total_pages = (len(users) + users_per_page - 1) // users_per_page if users else 1
        
        if not users:
            text = "👥 <b>Пользователи</b>\n\nПользователей пока нет."
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
            ])
        else:
            text = f"👥 <b>Все пользователи</b>\n\nВсего: {len(users)} | Страница {page}/{total_pages}\n\n"
            
            # Функция для форматирования даты
            def format_date(dt):
                if not dt:
                    return "—"
                try:
                    # Форматируем в формат ДД.ММ.ГГГГ ЧЧ:ММ
                    return dt.strftime("%d.%m.%Y %H:%M")
                except:
                    return "—"
            
            # Функция для форматирования относительного времени
            def format_relative_time(dt):
                if not dt:
                    return "—"
                try:
                    now = datetime.utcnow()
                    diff = now - dt
                    
                    if diff.days > 0:
                        return f"{diff.days} дн. назад"
                    elif diff.seconds >= 3600:
                        hours = diff.seconds // 3600
                        return f"{hours} ч. назад"
                    elif diff.seconds >= 60:
                        minutes = diff.seconds // 60
                        return f"{minutes} мин. назад"
                    else:
                        return "только что"
                except:
                    return "—"
            
            # Вычисляем диапазон пользователей для текущей страницы
            start_idx = (page - 1) * users_per_page
            end_idx = start_idx + users_per_page
            page_users = users[start_idx:end_idx]
            
            # Показываем пользователей текущей страницы
            for i, user in enumerate(page_users, start=start_idx + 1):
                text += f"<b>{i}. ID: <code>{user.telegram_id}</code></b>"
                if user.first_name:
                    text += f" ({user.first_name}"
                    if user.last_name:
                        text += f" {user.last_name}"
                    text += ")"
                text += "\n"
                
                # Дата регистрации
                reg_date = format_date(user.created_at)
                text += f"   📅 Регистрация: {reg_date}"
                if user.created_at:
                    text += f" ({format_relative_time(user.created_at)})"
                text += "\n"
                
                # Последняя активность (updated_at)
                last_active = format_date(user.updated_at)
                text += f"   🔄 Последняя активность: {last_active}"
                if user.updated_at:
                    text += f" ({format_relative_time(user.updated_at)})"
                text += "\n"
                
                # Статус теста
                if user.test_started_at:
                    test_start = format_date(user.test_started_at)
                    text += f"   🧪 Тест начат: {test_start}"
                    if user.test_completed_at:
                        test_end = format_date(user.test_completed_at)
                        text += f" | Завершен: {test_end}"
                    else:
                        text += " | В процессе"
                    text += "\n"
                
                # Статус оплаты
                if user.is_paid or user.is_premium_paid:
                    text += "   💎 Платный пользователь"
                    if user.is_premium_paid:
                        text += " (Премиум)"
                    text += "\n"
                
                text += "\n"
            
            # Кнопки пагинации
            keyboard_buttons = []
            nav_buttons = []
            
            if page > 1:
                nav_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"admin_all_users:{page-1}"))
            if page < total_pages:
                nav_buttons.append(InlineKeyboardButton(text="Вперед ▶️", callback_data=f"admin_all_users:{page+1}"))
            
            if nav_buttons:
                keyboard_buttons.append(nav_buttons)
            
            keyboard_buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")])
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"❌ Ошибка при получении списка пользователей: {e}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        await callback.answer("❌ Ошибка при получении данных", show_alert=True)


@router.callback_query(F.data == "admin_free_reports")
async def admin_free_reports(callback: CallbackQuery):
    """Показать статистику бесплатных отчетов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа", show_alert=True)
        return
    
    try:
        count = await db_service.get_free_reports_count()
        
        # Получаем детальную информацию
        async with async_session() as session:
            stmt = select(User).where(
                User.free_report_status.in_([
                    ReportGenerationStatus.PROCESSING,
                    ReportGenerationStatus.COMPLETED
                ])
            )
            result = await session.execute(stmt)
            users = result.scalars().all()
            
            processing = sum(1 for u in users if u.free_report_status == ReportGenerationStatus.PROCESSING)
            completed = sum(1 for u in users if u.free_report_status == ReportGenerationStatus.COMPLETED)
        
        text = f"""
📊 <b>Бесплатные отчеты</b>

Всего запущено: {count}
• В обработке: {processing}
• Завершено: {completed}

<b>Пользователи:</b>
        """.strip()
        
        if users:
            # Группируем по статусу
            processing_users = [u for u in users if u.free_report_status == ReportGenerationStatus.PROCESSING]
            completed_users = [u for u in users if u.free_report_status == ReportGenerationStatus.COMPLETED]
            
            if processing_users:
                text += "\n\n<b>В обработке:</b>"
                for i, user in enumerate(processing_users[:30], 1):
                    text += f"\n{i}. ID: <code>{user.telegram_id}</code>"
                if len(processing_users) > 30:
                    text += f"\n... и еще {len(processing_users) - 30} пользователей"
            
            if completed_users:
                text += "\n\n<b>Завершено:</b>"
                for i, user in enumerate(completed_users[:30], 1):
                    text += f"\n{i}. ID: <code>{user.telegram_id}</code>"
                if len(completed_users) > 30:
                    text += f"\n... и еще {len(completed_users) - 30} пользователей"
        else:
            text += "\n\nПользователей пока нет."
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
        ])
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"❌ Ошибка при получении статистики бесплатных отчетов: {e}")
        await callback.answer("❌ Ошибка при получении данных", show_alert=True)


@router.callback_query(F.data == "admin_premium_reports")
async def admin_premium_reports(callback: CallbackQuery):
    """Показать статистику премиум отчетов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа", show_alert=True)
        return
    
    try:
        count = await db_service.get_premium_reports_count()
        
        # Получаем детальную информацию
        async with async_session() as session:
            stmt = select(User).where(
                User.premium_report_status.in_([
                    ReportGenerationStatus.PROCESSING,
                    ReportGenerationStatus.COMPLETED
                ])
            )
            result = await session.execute(stmt)
            users = result.scalars().all()
            
            processing = sum(1 for u in users if u.premium_report_status == ReportGenerationStatus.PROCESSING)
            completed = sum(1 for u in users if u.premium_report_status == ReportGenerationStatus.COMPLETED)
        
        text = f"""
💎 <b>Премиум отчеты</b>

Всего запущено: {count}
• В обработке: {processing}
• Завершено: {completed}

<b>Пользователи:</b>
        """.strip()
        
        if users:
            # Группируем по статусу
            processing_users = [u for u in users if u.premium_report_status == ReportGenerationStatus.PROCESSING]
            completed_users = [u for u in users if u.premium_report_status == ReportGenerationStatus.COMPLETED]
            
            if processing_users:
                text += "\n\n<b>В обработке:</b>"
                for i, user in enumerate(processing_users[:30], 1):
                    text += f"\n{i}. ID: <code>{user.telegram_id}</code>"
                if len(processing_users) > 30:
                    text += f"\n... и еще {len(processing_users) - 30} пользователей"
            
            if completed_users:
                text += "\n\n<b>Завершено:</b>"
                for i, user in enumerate(completed_users[:30], 1):
                    text += f"\n{i}. ID: <code>{user.telegram_id}</code>"
                if len(completed_users) > 30:
                    text += f"\n... и еще {len(completed_users) - 30} пользователей"
        else:
            text += "\n\nПользователей пока нет."
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
        ])
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"❌ Ошибка при получении статистики премиум отчетов: {e}")
        await callback.answer("❌ Ошибка при получении данных", show_alert=True)


@router.callback_query(F.data == "admin_report_links")
async def admin_report_links(callback: CallbackQuery):
    """Показать все ссылки на отчеты"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа", show_alert=True)
        return
    
    try:
        links = await db_service.get_all_report_links()
        webapp_url = os.getenv("WEBAPP_URL", "").rstrip("/")
        
        if not links:
            text = "🔗 <b>Ссылки на отчеты</b>\n\nОтчетов пока нет."
        else:
            text = f"🔗 <b>Все ссылки на отчеты</b>\n\nВсего: {len(links)}\n\n"
            
            # Группируем по пользователям
            user_links = {}
            for link in links:
                user_id = link["telegram_id"]
                if user_id not in user_links:
                    user_links[user_id] = []
                user_links[user_id].append(link)
            
            # Показываем первые 20 пользователей
            for i, (user_id, user_link_list) in enumerate(list(user_links.items())[:20], 1):
                text += f"<b>Пользователь {user_id}:</b>\n"
                for link in user_link_list:
                    report_type = "Бесплатный" if link["type"] == "free" else "Премиум"
                    status = link["status"] or "N/A"
                    
                    # Формируем URL для скачивания
                    if webapp_url:
                        if link["type"] == "premium":
                            download_url = f"{webapp_url}/api/download/premium-report/{user_id}?download=1"
                        else:
                            download_url = f"{webapp_url}/api/download/report/{user_id}?download=1"
                        text += f"  • {report_type} ({status}): <code>{download_url}</code>\n"
                    else:
                        text += f"  • {report_type} ({status}): {link['path']}\n"
                text += "\n"
            
            if len(user_links) > 20:
                text += f"\n... и еще {len(user_links) - 20} пользователей с отчетами"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
        ])
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"❌ Ошибка при получении ссылок на отчеты: {e}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        await callback.answer("❌ Ошибка при получении данных", show_alert=True)


@router.callback_query(F.data == "admin_answers")
async def admin_answers(callback: CallbackQuery):
    """Показать статистику ответов пользователей"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа", show_alert=True)
        return
    
    try:
        stats = await db_service.get_users_answers_count()
        
        if not stats:
            text = "📝 <b>Ответы пользователей</b>\n\nОтветов пока нет."
        else:
            text = f"📝 <b>Ответы пользователей</b>\n\nВсего пользователей с ответами: {len(stats)}\n\n"
            
            # Показываем топ 30 пользователей
            for i, stat in enumerate(stats[:30], 1):
                text += f"{i}. ID: <code>{stat['telegram_id']}</code> - {stat['answers_count']} ответов\n"
            
            if len(stats) > 30:
                text += f"\n... и еще {len(stats) - 30} пользователей"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
        ])
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"❌ Ошибка при получении статистики ответов: {e}")
        await callback.answer("❌ Ошибка при получении данных", show_alert=True)


@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    """Начать рассылку сообщений"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа", show_alert=True)
        return
    
    text = """
📢 <b>Рассылка сообщений</b>

Отправьте текст сообщения, которое будет разослано всем пользователям.

Для отмены отправьте /cancel
    """.strip()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_broadcast_cancel")]
    ])
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(BroadcastState.waiting_for_message)
    await callback.answer()


@router.callback_query(F.data == "admin_broadcast_cancel")
async def admin_broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    """Отменить рассылку"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа", show_alert=True)
        return
    
    await state.clear()
    await callback.message.edit_text("❌ Рассылка отменена.")
    await callback.answer()
    
    # Возвращаемся в меню
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="admin_menu")]
    ])
    await callback.message.answer(
        "🔐 <b>Админ-панель</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(Command("cancel"))
async def admin_broadcast_cancel_command(message: Message, state: FSMContext):
    """Отменить рассылку через команду /cancel"""
    if not is_admin(message.chat.id):
        await message.answer("❌ У вас нет доступа.")
        return
    
    current_state = await state.get_state()
    if current_state == BroadcastState.waiting_for_message:
        await state.clear()
        await message.answer("❌ Рассылка отменена.")
    else:
        await message.answer("❌ Нет активной рассылки для отмены.")


@router.message(BroadcastState.waiting_for_message)
async def admin_broadcast_process(message: Message, state: FSMContext):
    """Обработать сообщение для рассылки"""
    if not is_admin(message.chat.id):
        await state.clear()
        await message.answer("❌ У вас нет доступа.")
        return
    
    if message.text and message.text.strip() == "/cancel":
        await state.clear()
        await message.answer("❌ Рассылка отменена.")
        return
    
    try:
        broadcast_text = message.text or message.caption or ""
        
        if not broadcast_text:
            await message.answer("❌ Сообщение не может быть пустым. Попробуйте еще раз или отправьте /cancel для отмены.")
            return
        
        # Подтверждение
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Отправить", callback_data=f"admin_broadcast_confirm:{message.message_id}")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_broadcast_cancel")]
        ])
        
        preview_text = f"""
📢 <b>Предпросмотр рассылки</b>

<b>Текст сообщения:</b>
{broadcast_text}

<b>Внимание!</b> Это сообщение будет отправлено всем активным пользователям бота.
        """.strip()
        
        await message.answer(
            preview_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        # Сохраняем текст в состоянии
        await state.update_data(broadcast_text=broadcast_text)
        
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке сообщения для рассылки: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте еще раз или отправьте /cancel для отмены.")


@router.callback_query(F.data.startswith("admin_broadcast_confirm:"))
async def admin_broadcast_confirm(callback: CallbackQuery, state: FSMContext):
    """Подтвердить и выполнить рассылку"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа", show_alert=True)
        return
    
    try:
        data = await state.get_data()
        broadcast_text = data.get("broadcast_text")
        
        if not broadcast_text:
            await callback.answer("❌ Текст сообщения не найден", show_alert=True)
            await state.clear()
            return
        
        # Получаем всех активных пользователей
        users = await db_service.get_all_active_users()
        
        if not users:
            await callback.message.edit_text("❌ Нет активных пользователей для рассылки.")
            await callback.answer()
            await state.clear()
            return
        
        # Отправляем сообщение о начале рассылки
        await callback.message.edit_text(f"📢 Начинаю рассылку для {len(users)} пользователей...")
        await callback.answer()
        
        # Отправляем сообщения
        success_count = 0
        fail_count = 0
        
        for user in users:
            try:
                success = await telegram_service.send_message(
                    chat_id=user.telegram_id,
                    text=broadcast_text,
                    parse_mode="HTML"
                )
                if success:
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                logger.error(f"❌ Ошибка при отправке сообщения пользователю {user.telegram_id}: {e}")
                fail_count += 1
        
        # Итоговое сообщение
        result_text = f"""
✅ <b>Рассылка завершена</b>

Всего пользователей: {len(users)}
✅ Успешно отправлено: {success_count}
❌ Ошибок: {fail_count}
        """.strip()
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="admin_menu")]
        ])
        
        await callback.message.edit_text(
            result_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        await state.clear()
        logger.info(f"📢 Рассылка завершена: {success_count} успешно, {fail_count} ошибок")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при выполнении рассылки: {e}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        await callback.message.edit_text("❌ Произошла ошибка при рассылке.")
        await state.clear()

