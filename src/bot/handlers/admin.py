import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from dependency_injector.wiring import inject, Provide

from bot.container import Container
from bot.keyboards.admin import (
    admin_home_keyboard,
    admin_ai_stats_keyboard,
    admin_settings_keyboard,
    admin_back_keyboard,
)
from bot.interfaces.uow import AbcUnitOfWork
from bot.interfaces.services.settings import AbcSettingsService


logger = logging.getLogger(__name__)

router = Router()


def _ensure_admin(user_data: dict) -> bool:
    return bool(user_data.get('is_admin'))


@router.callback_query(F.data == "admin:home")
@inject
async def admin_home(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not _ensure_admin(data):
        await call.answer("Недостаточно прав", show_alert=True)
        return
    await call.answer()
    await call.message.edit_text("🛡️ Админ-панель", reply_markup=admin_home_keyboard())


@router.callback_query(F.data == "admin:stats:ai")
async def admin_stats_ai_menu(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not _ensure_admin(data):
        await call.answer("Недостаточно прав", show_alert=True)
        return
    await call.answer()
    await call.message.edit_text("Выберите период", reply_markup=admin_ai_stats_keyboard())


@router.callback_query(F.data == "admin:stats:ai:today")
@inject
async def admin_stats_ai_today(call: CallbackQuery, state: FSMContext, uow: AbcUnitOfWork = Provide[Container.uow]):
    data = await state.get_data()
    if not _ensure_admin(data):
        await call.answer("Недостаточно прав", show_alert=True)
        return
    async with uow:
        counts = await uow.ledger.requests_by_model_today()
    txt = (
        "📊 Сегодняшние запросы:\n\n"
        f"GPT‑5: {counts.gpt_5}\n"
        f"GPT‑5 Mini: {counts.gpt_5_mini}\n"
    )
    await call.message.edit_text(txt, reply_markup=admin_back_keyboard())


@router.callback_query(F.data == "admin:stats:user")
async def admin_stats_user_prompt(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not _ensure_admin(data):
        await call.answer("Недостаточно прав", show_alert=True)
        return
    await state.update_data(admin_wait_user_query=True)
    await call.message.edit_text("Отправьте username или telegram_id пользователя", reply_markup=admin_back_keyboard())


@router.message()
@inject
async def admin_stats_user_query(message: Message, state: FSMContext, uow: AbcUnitOfWork = Provide[Container.uow]):
    data = await state.get_data()
    if not data.get('admin_wait_user_query'):
        return
    if not _ensure_admin(data):
        await message.answer("Недостаточно прав")
        return
    await state.update_data(admin_wait_user_query=False)
    query = (message.text or "").strip()
    async with uow:
        user = None
        if query.isdigit():
            user = await uow.user.get_by_telegram_id(int(query))
        else:
            if query.startswith("@"): query = query[1:]
            user = await uow.user.get_by_username(query)
        if not user:
            await message.answer("Пользователь не найден", reply_markup=admin_back_keyboard())
            return
        totals = await uow.ledger.user_totals(user.id)
    last_at = totals.last_request_at.isoformat() if totals.last_request_at else "—"
    txt = (
        f"👤 @{user.username or '—'} (id={user.id}, tg={user.telegram_id})\n"
        f"Зарегистрирован: {user.created_at.isoformat() if user.created_at else '—'}\n"
        f"Баланс: {user.balance}\n"
        f"Последний запрос: {last_at}\n\n"
        "Запросы:\n"
        f"• GPT‑5: {totals.requests.gpt_5}\n"
        f"• GPT‑5 Mini: {totals.requests.gpt_5_mini}\n"
        f"Потрачено всего: {totals.total_spent}\n"
        f"Потрачено сегодня: {totals.today_spent}\n"
    )
    await message.answer(txt, reply_markup=admin_back_keyboard())


@router.callback_query(F.data == "admin:settings")
@inject
async def admin_settings_menu(call: CallbackQuery, state: FSMContext, settings: AbcSettingsService = Provide[Container.settings_service]):
    data = await state.get_data()
    if not _ensure_admin(data):
        await call.answer("Недостаточно прав", show_alert=True)
        return
    items = await settings.list_all()
    # show first 20 to avoid too long message
    pairs = list(items.items())[:20]
    await call.message.edit_text("✏️ Настройки (нажмите, чтобы редактировать)", reply_markup=admin_settings_keyboard(pairs))


@router.callback_query(F.data.startswith("admin:settings:edit:"))
@inject
async def admin_settings_edit(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not _ensure_admin(data):
        await call.answer("Недостаточно прав", show_alert=True)
        return
    key = (call.data or "").split(":", maxsplit=2)[-1]
    await state.update_data(admin_settings_edit_key=key, admin_wait_setting_value=True)
    await call.message.edit_text(f"Введите новое значение для {key}", reply_markup=admin_back_keyboard())


@router.message()
@inject
async def admin_settings_set_value(message: Message, state: FSMContext, settings: AbcSettingsService = Provide[Container.settings_service]):
    data = await state.get_data()
    if not data.get('admin_wait_setting_value'):
        return
    if not _ensure_admin(data):
        await message.answer("Недостаточно прав")
        return
    key = data.get('admin_settings_edit_key')
    value = (message.text or "").strip()
    await settings.set_value(str(key), str(value))
    await state.update_data(admin_wait_setting_value=False, admin_settings_edit_key=None)
    await message.answer("✅ Сохранено", reply_markup=admin_back_keyboard())


@router.callback_query(F.data == "admin:block")
async def admin_block_prompt(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not _ensure_admin(data):
        await call.answer("Недостаточно прав", show_alert=True)
        return
    await state.update_data(admin_wait_block_user=True)
    await call.message.edit_text("Введите username или telegram_id для блокировки/разблокировки (формат: id 123456 или @username true/false)", reply_markup=admin_back_keyboard())


@router.message()
@inject
async def admin_block_apply(message: Message, state: FSMContext, uow: AbcUnitOfWork = Provide[Container.uow]):
    data = await state.get_data()
    if not data.get('admin_wait_block_user'):
        return
    if not _ensure_admin(data):
        await message.answer("Недостаточно прав")
        return
    text = (message.text or "").strip()
    parts = text.split()
    if not parts:
        await message.answer("Неверный формат", reply_markup=admin_back_keyboard())
        return
    blocked = True
    ident = parts[0]
    if len(parts) >= 2:
        blocked = parts[1].lower() in {"1", "true", "yes", "+"}
    async with uow:
        user = None
        if ident.isdigit():
            user = await uow.user.get_by_telegram_id(int(ident))
        else:
            if ident.startswith("@"): ident = ident[1:]
            user = await uow.user.get_by_username(ident)
        if not user:
            await message.answer("Пользователь не найден", reply_markup=admin_back_keyboard())
            return
        await uow.session.execute(
            "UPDATE \"user\" SET is_blocked = :blocked WHERE id = :id",
            {"blocked": blocked, "id": user.id},
        )
    await message.answer(f"Готово. Блокировка: {blocked}", reply_markup=admin_back_keyboard())


