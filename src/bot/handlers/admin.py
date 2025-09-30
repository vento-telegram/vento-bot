import logging
from typing import Tuple

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from aiogram.filters import Command
from dependency_injector.wiring import Provide, inject

from bot.container import Container
from bot.interfaces.services.user import AbcUserService
from bot.enums import LedgerReasonEnum


logger = logging.getLogger(__name__)


class AdminStates(StatesGroup):
    add_tokens = State()
    block_user = State()
    unblock_user = State()


router = Router()


async def _ensure_admin(user_service: AbcUserService, telegram_id: int) -> Tuple[bool, bool]:
    """Return tuple (exists, is_admin)."""
    user = await user_service.get_user(telegram_id)
    if not user:
        return False, False
    return True, bool(user.is_admin)


@router.message(Command("admin"))
@inject
async def admin_help(
    message: Message,
    user_service: AbcUserService = Provide[Container.user_service],
):
    exists, is_admin = await _ensure_admin(user_service, message.from_user.id)
    if not exists or not is_admin:
        await message.answer("Раздел доступен только администраторам")
        return
    await message.answer(
        (
            "🛠 Админ-команды:\n"
            "/addtokens @username amount — начислить токены\n"
            "/block @username — заблокировать пользователя\n"
            "/unblock @username — разблокировать пользователя"
        )
    )


@router.message(Command("addtokens"))
@inject
async def admin_add_tokens_command(
    message: Message,
    state: FSMContext,
    user_service: AbcUserService = Provide[Container.user_service],
):
    exists, is_admin = await _ensure_admin(user_service, message.from_user.id)
    if not exists or not is_admin:
        await message.answer("Недостаточно прав")
        return
    # Try parse arguments: /addtokens @user 100
    text = (message.text or "").replace("\n", " ").strip()
    parts = text.split()
    username = None
    amount = None
    if len(parts) >= 3:
        # parts[0] is command
        raw_user = parts[1]
        if raw_user.startswith("@"): raw_user = raw_user[1:]
        username = raw_user
        try:
            amount = int(parts[2])
        except Exception:
            amount = None
    if username and isinstance(amount, int) and amount > 0:
        updated = await user_service.add_tokens_by_username(
            username=username,
            amount=amount,
            reason=LedgerReasonEnum.admin_adjustment,
        )
        if not updated:
            await message.answer(f"Пользователь @{username} не найден")
            return
        await message.answer(
            f"Зачислено {amount} токенов пользователю @{username}. Текущий баланс: {updated.balance}"
        )
        return
    # Fallback to state flow
    await state.set_state(AdminStates.add_tokens)
    await message.answer(
        "Введите в одной строке: @username и количество токенов. Пример: @username 100",
    )


@router.message(Command("block"))
@inject
async def admin_block_command(
    message: Message,
    state: FSMContext,
    user_service: AbcUserService = Provide[Container.user_service],
):
    exists, is_admin = await _ensure_admin(user_service, message.from_user.id)
    if not exists or not is_admin:
        await message.answer("Недостаточно прав")
        return
    text = (message.text or "").replace("\n", " ").strip()
    parts = text.split()
    username = None
    if len(parts) >= 2:
        raw = parts[1]
        if raw.startswith("@"): raw = raw[1:]
        username = raw
    if username:
        updated = await user_service.block_user_by_username(username)
        if not updated:
            await message.answer(f"Пользователь @{username} не найден")
            return
        await message.answer(f"Пользователь @{username} заблокирован")
        return
    await state.set_state(AdminStates.block_user)
    await message.answer("Введите @username пользователя для блокировки")


@router.message(Command("unblock"))
@inject
async def admin_unblock_command(
    message: Message,
    state: FSMContext,
    user_service: AbcUserService = Provide[Container.user_service],
):
    exists, is_admin = await _ensure_admin(user_service, message.from_user.id)
    if not exists or not is_admin:
        await message.answer("Недостаточно прав")
        return
    text = (message.text or "").replace("\n", " ").strip()
    parts = text.split()
    username = None
    if len(parts) >= 2:
        raw = parts[1]
        if raw.startswith("@"): raw = raw[1:]
        username = raw
    if username:
        updated = await user_service.unblock_user_by_username(username)
        if not updated:
            await message.answer(f"Пользователь @{username} не найден")
            return
        await message.answer(f"Пользователь @{username} разблокирован")
        return
    await state.set_state(AdminStates.unblock_user)
    await message.answer("Введите @username пользователя для разблокировки")


def _parse_username_and_amount(text: str) -> tuple[str | None, int | None]:
    try:
        parts = (text or "").replace("\n", " ").split()
        if len(parts) < 2:
            return None, None
        username = parts[0]
        if username.startswith("@"):  # strip leading @
            username = username[1:]
        amount = int(parts[1])
        if amount <= 0:
            return username, None
        return username, amount
    except Exception:
        return None, None


@router.message(AdminStates.add_tokens)
@inject
async def admin_add_tokens_handle(
    message: Message,
    state: FSMContext,
    user_service: AbcUserService = Provide[Container.user_service],
):
    exists, is_admin = await _ensure_admin(user_service, message.from_user.id)
    if not exists or not is_admin:
        await message.answer("Недостаточно прав")
        await state.clear()
        return

    username, amount = _parse_username_and_amount(message.text or "")
    if not username or amount is None:
        await message.answer(
            "Неверный формат. Введите: @username и число токенов. Пример: @user 100",
        )
        return

    updated = await user_service.add_tokens_by_username(username=username, amount=amount, reason=LedgerReasonEnum.admin_adjustment)
    if not updated:
        await message.answer(f"Пользователь @{username} не найден")
        return
    
    await state.clear()
    await message.answer(
        f"Зачислено {amount} токенов пользователю @{username}. Текущий баланс: {updated.balance}",
    )


def _parse_username_only(text: str) -> str | None:
    raw = (text or "").strip()
    if not raw:
        return None
    if raw.startswith("@"):
        raw = raw[1:]
    return raw


@router.message(AdminStates.block_user)
@inject
async def admin_block_handle(
    message: Message,
    state: FSMContext,
    user_service: AbcUserService = Provide[Container.user_service],
):
    exists, is_admin = await _ensure_admin(user_service, message.from_user.id)
    if not exists or not is_admin:
        await message.answer("Недостаточно прав")
        await state.clear()
        return

    username = _parse_username_only(message.text or "")
    if not username:
        await message.answer("Укажите @username")
        return
    updated = await user_service.block_user_by_username(username)
    if not updated:
        await message.answer(f"Пользователь @{username} не найден")
        return
    await state.clear()
    await message.answer(f"Пользователь @{username} заблокирован")


@router.message(AdminStates.unblock_user)
@inject
async def admin_unblock_handle(
    message: Message,
    state: FSMContext,
    user_service: AbcUserService = Provide[Container.user_service],
):
    exists, is_admin = await _ensure_admin(user_service, message.from_user.id)
    if not exists or not is_admin:
        await message.answer("Недостаточно прав")
        await state.clear()
        return

    username = _parse_username_only(message.text or "")
    if not username:
        await message.answer("Укажите @username")
        return
    updated = await user_service.unblock_user_by_username(username)
    if not updated:
        await message.answer(f"Пользователь @{username} не найден")
        return
    await state.clear()
    await message.answer(f"Пользователь @{username} разблокирован")

