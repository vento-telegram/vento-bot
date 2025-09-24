import logging
from typing import Tuple

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message
from dependency_injector.wiring import Provide, inject

from bot.container import Container
from bot.interfaces.services.user import AbcUserService
from bot.keyboards.admin import admin_main_keyboard, admin_back_keyboard
from bot.keyboards.start import start_keyboard
from bot.enums import LedgerReasonEnum, BotModeEnum


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


@router.callback_query(F.data == "goto:admin")
@inject
async def open_admin(
    call: CallbackQuery,
    user_service: AbcUserService = Provide[Container.user_service],
):
    exists, is_admin = await _ensure_admin(user_service, call.from_user.id)
    if not exists or not is_admin:
        try:
            await call.answer("Раздел доступен только администраторам", show_alert=True)
        except Exception:
            pass
        return
    await call.message.edit_text(
        "Админ-панель. Выберите действие:",
        reply_markup=admin_main_keyboard(),
    )


@router.callback_query(F.data == "admin:add_tokens")
@inject
async def admin_add_tokens_prompt(
    call: CallbackQuery,
    state: FSMContext,
    user_service: AbcUserService = Provide[Container.user_service],
):
    exists, is_admin = await _ensure_admin(user_service, call.from_user.id)
    if not exists or not is_admin:
        try:
            await call.answer("Недостаточно прав", show_alert=True)
        except Exception:
            pass
        return
    await state.set_state(AdminStates.add_tokens)
    await call.message.edit_text(
        "Введите в одной строке: @username и количество токенов. Пример: @username 100",
        reply_markup=admin_back_keyboard(),
    )


@router.callback_query(F.data == "admin:block")
@inject
async def admin_block_prompt(
    call: CallbackQuery,
    state: FSMContext,
    user_service: AbcUserService = Provide[Container.user_service],
):
    exists, is_admin = await _ensure_admin(user_service, call.from_user.id)
    if not exists or not is_admin:
        try:
            await call.answer("Недостаточно прав", show_alert=True)
        except Exception:
            pass
        return
    await state.set_state(AdminStates.block_user)
    await call.message.edit_text(
        "Введите @username пользователя для блокировки",
        reply_markup=admin_back_keyboard(),
    )


@router.callback_query(F.data == "admin:unblock")
@inject
async def admin_unblock_prompt(
    call: CallbackQuery,
    state: FSMContext,
    user_service: AbcUserService = Provide[Container.user_service],
):
    exists, is_admin = await _ensure_admin(user_service, call.from_user.id)
    if not exists or not is_admin:
        try:
            await call.answer("Недостаточно прав", show_alert=True)
        except Exception:
            pass
        return
    await state.set_state(AdminStates.unblock_user)
    await call.message.edit_text(
        "Введите @username пользователя для разблокировки",
        reply_markup=admin_back_keyboard(),
    )


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
            reply_markup=admin_back_keyboard(),
        )
        return

    updated = await user_service.add_tokens_by_username(username=username, amount=amount, reason=LedgerReasonEnum.admin_adjustment)
    if not updated:
        await message.answer(f"Пользователь @{username} не найден", reply_markup=admin_back_keyboard())
        return

    await state.clear()
    await message.answer(
        f"Зачислено {amount} токенов пользователю @{username}. Текущий баланс: {updated.balance}",
        reply_markup=admin_main_keyboard(),
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
        await message.answer("Укажите @username", reply_markup=admin_back_keyboard())
        return
    updated = await user_service.block_user_by_username(username)
    if not updated:
        await message.answer(f"Пользователь @{username} не найден", reply_markup=admin_back_keyboard())
        return
    await state.clear()
    await message.answer(f"Пользователь @{username} заблокирован", reply_markup=admin_main_keyboard())


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
        await message.answer("Укажите @username", reply_markup=admin_back_keyboard())
        return
    updated = await user_service.unblock_user_by_username(username)
    if not updated:
        await message.answer(f"Пользователь @{username} не найден", reply_markup=admin_back_keyboard())
        return
    await state.clear()
    await message.answer(f"Пользователь @{username} разблокирован", reply_markup=admin_main_keyboard())

