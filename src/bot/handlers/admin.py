import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from dependency_injector.wiring import Provide, inject

from bot.container import Container
from bot.interfaces.services.user import AbcUserService
from bot.interfaces.uow import AbcUnitOfWork


logger = logging.getLogger(__name__)

router = Router()


def _ensure_admin_or_raise(user) -> None:
    if not getattr(user, "is_admin", False):
        raise PermissionError("Admin privileges required")


@router.callback_query(F.data == "goto:admin")
@inject
async def goto_admin(
    call: CallbackQuery,
    user_service: AbcUserService = Provide[Container.user_service],
):
    await call.answer()
    user = await user_service.get_user(call.from_user.id)
    try:
        _ensure_admin_or_raise(user)
    except PermissionError:
        await call.message.answer("🚫 У тебя нет прав администратора.")
        return

    await call.message.answer(
        "🛠 *Админ-панель*\n\n"
        "Доступные команды:\n"
        "- /stats — статистика за сегодня\n"
        "- /user <username> — статистика пользователя (@username или username)\n"
        "- /grant <username> <amount> — начислить ⭐ пользователю по юзернейму\n"
        "- /block <username> — заблокировать пользователя\n"
        "- /unblock <username> — разблокировать пользователя\n"
    )


    


@router.message(Command("stats"))
@inject
async def stats_today(
    message: Message,
    user_service: AbcUserService = Provide[Container.user_service],
    uow: AbcUnitOfWork = Provide[Container.uow],
):
    admin = await user_service.get_user(message.from_user.id)
    try:
        _ensure_admin_or_raise(admin)
    except PermissionError:
        await message.answer("🚫 Команда доступна только администраторам.")
        return

    async with uow:
        spent = await uow.ledger.total_spent_today()
        cnt = await uow.ledger.requests_count_today()
        by_model = await uow.ledger.requests_by_model_today()

    lines = [
        "📊 Статистика за сегодня:",
        f"— Потрачено ⭐: {spent}",
        f"— Запросов: {cnt}",
        f"— По моделям:",
        f"   • GPT‑5: {by_model.gpt_5}",
        f"   • GPT‑5 Mini: {by_model.gpt_5_mini}",
        f"   • DALL·E 3: {by_model.dalle3}",
    ]
    await message.answer("\n".join(lines))


def _normalize_username(text: str) -> str:
    name = text.strip()
    if name.startswith("@"):  # strip leading '@'
        name = name[1:]
    return name


@router.message(Command("user"))
@inject
async def user_stats(
    message: Message,
    user_service: AbcUserService = Provide[Container.user_service],
    uow: AbcUnitOfWork = Provide[Container.uow],
):
    admin = await user_service.get_user(message.from_user.id)
    try:
        _ensure_admin_or_raise(admin)
    except PermissionError:
        await message.answer("🚫 Команда доступна только администраторам.")
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) != 2:
        await message.answer("Использование: /user <username>")
        return

    username = _normalize_username(parts[1])
    target = await user_service.get_user(telegram_id=admin.telegram_id)  # placeholder to satisfy type checker
    async with uow:
        user = await uow.user.get_by_username(username)
        if not user:
            await message.answer("Пользователь не найден")
            return
        totals = await uow.ledger.user_totals(user.id)

    lines = [
        f"👤 @{username}",
        f"🪙 Баланс: {user.balance} ⭐",
        f"🚫 Заблокирован: {'да' if user.is_blocked else 'нет'}",
        f"Всего потрачено: {totals.total_spent}",
        f"Сегодня потрачено: {totals.today_spent}",
        "Запросов по моделям (всё время):",
        f"— GPT‑5: {totals.requests.gpt_5}",
        f"— GPT‑5 Mini: {totals.requests.gpt_5_mini}",
        f"— DALL·E 3: {totals.requests.dalle3}",
        f"Последний запрос: {totals.last_request_at}",
    ]
    await message.answer("\n".join(lines))


@router.message(Command("grant"))
@inject
async def grant_tokens(
    message: Message,
    user_service: AbcUserService = Provide[Container.user_service],
):
    admin = await user_service.get_user(message.from_user.id)
    try:
        _ensure_admin_or_raise(admin)
    except PermissionError:
        await message.answer("🚫 Команда доступна только администраторам.")
        return

    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Использование: /grant <username> <amount>")
        return

    username = _normalize_username(parts[1])
    try:
        amount = int(parts[2])
    except ValueError:
        await message.answer("amount должен быть числом")
        return

    updated = await user_service.add_tokens_by_username(username, amount, reason=f"admin grant by {message.from_user.id}")
    if not updated:
        await message.answer("Пользователь не найден")
        return
    await message.answer(f"✅ Начислено {amount} ⭐ @{username}. Новый баланс: {updated.balance}")


@router.message(Command("block"))
@inject
async def block_user(
    message: Message,
    user_service: AbcUserService = Provide[Container.user_service],
):
    admin = await user_service.get_user(message.from_user.id)
    try:
        _ensure_admin_or_raise(admin)
    except PermissionError:
        await message.answer("🚫 Команда доступна только администраторам.")
        return

    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Использование: /block <username>")
        return
    username = _normalize_username(parts[1])
    updated = await user_service.block_user_by_username(username)
    if not updated:
        await message.answer("Пользователь не найден")
        return
    await message.answer(f"⛔️ Пользователь @{username} заблокирован")


@router.message(Command("unblock"))
@inject
async def unblock_user(
    message: Message,
    user_service: AbcUserService = Provide[Container.user_service],
):
    admin = await user_service.get_user(message.from_user.id)
    try:
        _ensure_admin_or_raise(admin)
    except PermissionError:
        await message.answer("🚫 Команда доступна только администраторам.")
        return

    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Использование: /unblock <username>")
        return
    username = _normalize_username(parts[1])
    updated = await user_service.unblock_user_by_username(username)
    if not updated:
        await message.answer("Пользователь не найден")
        return
    await message.answer(f"✅ Пользователь @{username} разблокирован")


