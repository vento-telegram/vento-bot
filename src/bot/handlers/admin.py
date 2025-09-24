import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from dependency_injector.wiring import Provide, inject

from bot.container import Container
from bot.keyboards.admin import admin_main_keyboard, admin_back_keyboard

logger = logging.getLogger(__name__)

router = Router()


async def _ensure_admin(state: FSMContext) -> bool:
    data = await state.get_data()
    # state should include user entity or admin flag; fallback to False
    return bool(data.get("is_admin"))


@router.callback_query(F.data == "admin:menu")
@inject
async def admin_menu(
    call: CallbackQuery,
    state: FSMContext,
):
    if not await _ensure_admin(state):
        await call.answer("Недостаточно прав", show_alert=True)
        return
    await call.answer()
    await call.message.edit_text("🛠️ Админ-панель", reply_markup=admin_main_keyboard())


@router.message(F.text == "/admin")
@inject
async def admin_entry(
    message: Message,
    state: FSMContext,
):
    if not await _ensure_admin(state):
        await message.answer("Недостаточно прав")
        return
    await message.answer("🛠️ Админ-панель", reply_markup=admin_main_keyboard())


@router.callback_query(F.data == "admin:stats:today")
@inject
async def admin_stats_today(
    call: CallbackQuery,
    state: FSMContext,
    uow = Provide[Container.uow],
):
    if not await _ensure_admin(state):
        await call.answer("Недостаточно прав", show_alert=True)
        return
    async with uow:
        counts = await uow.ledger.requests_by_model_today()
    text = (
        "📊 Запросы по моделям (сегодня):\n\n"
        f"GPT‑5: {counts.gpt_5}\n"
        f"GPT‑5 Mini: {counts.gpt_5_mini}\n"
        f"GPT Image: {counts.gpt_image}\n"
        f"Nano Banana: {counts.nano_banana}\n"
        f"Suno: {counts.suno}\n"
        f"Veo 3: {counts.veo}\n"
    )
    try:
        await call.message.edit_text(text, reply_markup=admin_back_keyboard())
    except Exception:
        await call.message.edit_reply_markup(reply_markup=admin_back_keyboard())


@router.callback_query(F.data == "admin:stats:bydate")
@inject
async def admin_stats_bydate_prompt(
    call: CallbackQuery,
    state: FSMContext,
):
    if not await _ensure_admin(state):
        await call.answer("Недостаточно прав", show_alert=True)
        return
    await state.update_data(admin_wait_date=True)
    await call.message.edit_text("📅 Введи дату в формате YYYY-MM-DD", reply_markup=admin_back_keyboard())


@router.message(F.text & ~F.text.startswith("/"))
@inject
async def admin_handle_date_or_inputs(
    message: Message,
    state: FSMContext,
    uow = Provide[Container.uow],
    settings_service = Provide[Container.settings_service],
    user_service = Provide[Container.user_service],
):
    data = await state.get_data()
    if not data.get("is_admin"):
        return

    text = (message.text or "").strip()

    if data.get("admin_wait_date"):
        await state.update_data(admin_wait_date=False)
        try:
            async with uow:
                counts = await uow.ledger.requests_by_model_on_date(text)
            reply = (
                f"📊 Запросы по моделям на {text}:\n\n"
                f"GPT‑5: {counts.gpt_5}\n"
                f"GPT‑5 Mini: {counts.gpt_5_mini}\n"
                f"GPT Image: {counts.gpt_image}\n"
                f"Nano Banana: {counts.nano_banana}\n"
                f"Suno: {counts.suno}\n"
                f"Veo 3: {counts.veo}\n"
            )
            await message.answer(reply, reply_markup=admin_back_keyboard())
        except Exception:
            await message.answer("☹️ Неверная дата или ошибка запроса", reply_markup=admin_back_keyboard())
        return

    if data.get("admin_wait_user"):
        await state.update_data(admin_wait_user=False)
        # text may be telegram_id or @username
        async with uow:
            user = None
            if text.startswith("@"):
                user = await uow.user.get_by_username(text[1:])
            else:
                try:
                    tid = int(text)
                except Exception:
                    tid = 0
                if tid:
                    user = await uow.user.get_by_telegram_id(tid)
            if not user:
                await message.answer("Пользователь не найден", reply_markup=admin_back_keyboard())
                return
            totals = await uow.ledger.user_totals(user.id)
        reply = (
            "👤 Пользователь:\n"
            f"telegram_id: {user.telegram_id}\n"
            f"username: {user.username}\n"
            f"зарегистрирован: {user.created_at}\n"
            f"последний запрос: {totals.last_request_at}\n"
            f"куплено токенов: {totals.tokens_purchased}\n\n"
            "Запросы по моделям:\n"
            f"GPT‑5: {totals.requests.gpt_5}, GPT‑5 Mini: {totals.requests.gpt_5_mini}, GPT Image: {totals.requests.gpt_image}, Nano Banana: {totals.requests.nano_banana}, Suno: {totals.requests.suno}, Veo: {totals.requests.veo}\n"
            f"Всего потрачено: {totals.total_spent}, сегодня: {totals.today_spent}"
        )
        await message.answer(reply, reply_markup=admin_back_keyboard())
        return

    if data.get("admin_wait_setting_key"):
        await state.update_data(admin_wait_setting_key=False, admin_setting_key=text, admin_wait_setting_value=True)
        await message.answer("Введи значение для этого ключа (строкой)", reply_markup=admin_back_keyboard())
        return

    if data.get("admin_wait_setting_value"):
        key = data.get("admin_setting_key")
        await state.update_data(admin_wait_setting_value=False, admin_setting_key=None)
        try:
            await settings_service.set_value(str(key), str(text))
            await message.answer("✅ Настройка сохранена", reply_markup=admin_back_keyboard())
        except Exception:
            await message.answer("☹️ Ошибка сохранения настройки", reply_markup=admin_back_keyboard())
        return

    if data.get("admin_wait_block"):
        await state.update_data(admin_wait_block=False)
        target = text
        async with uow:
            user = None
            if target.startswith("@"):
                user = await uow.user.get_by_username(target[1:])
            else:
                try:
                    tid = int(target)
                except Exception:
                    tid = 0
                if tid:
                    user = await uow.user.get_by_telegram_id(tid)
            if not user:
                await message.answer("Пользователь не найден", reply_markup=admin_back_keyboard())
                return
            await uow.user.set_blocked_by_id(user.id, True)
        await message.answer("✅ Пользователь заблокирован", reply_markup=admin_back_keyboard())
        return

    if data.get("admin_wait_unblock"):
        await state.update_data(admin_wait_unblock=False)
        target = text
        async with uow:
            user = None
            if target.startswith("@"):
                user = await uow.user.get_by_username(target[1:])
            else:
                try:
                    tid = int(target)
                except Exception:
                    tid = 0
                if tid:
                    user = await uow.user.get_by_telegram_id(tid)
            if not user:
                await message.answer("Пользователь не найден", reply_markup=admin_back_keyboard())
                return
            await uow.user.set_blocked_by_id(user.id, False)
        await message.answer("✅ Пользователь разблокирован", reply_markup=admin_back_keyboard())
        return


@router.callback_query(F.data == "admin:userstats")
@inject
async def admin_userstats_prompt(
    call: CallbackQuery,
    state: FSMContext,
):
    if not await _ensure_admin(state):
        await call.answer("Недостаточно прав", show_alert=True)
        return
    await state.update_data(admin_wait_user=True)
    await call.answer()
    await call.message.edit_text("👤 Введи telegram_id или @username", reply_markup=admin_back_keyboard())


@router.callback_query(F.data == "admin:settings:list")
@inject
async def admin_list_settings(
    call: CallbackQuery,
    state: FSMContext,
    settings_service = Provide[Container.settings_service],
):
    if not await _ensure_admin(state):
        await call.answer("Недостаточно прав", show_alert=True)
        return
    items = await settings_service.list_all()
    lines = [f"{k} = {v}" for k, v in sorted(items.items())]
    text = "⚙️ Настройки:\n" + "\n".join(lines)
    await call.answer()
    await call.message.edit_text(text, reply_markup=admin_back_keyboard())


@router.callback_query(F.data == "admin:settings:set")
@inject
async def admin_set_setting_prompt(
    call: CallbackQuery,
    state: FSMContext,
):
    if not await _ensure_admin(state):
        await call.answer("Недостаточно прав", show_alert=True)
        return
    await state.update_data(admin_wait_setting_key=True)
    await call.answer()
    await call.message.edit_text("🔧 Введи ключ настройки (например, gpt_price, 700_stars_price)", reply_markup=admin_back_keyboard())


@router.callback_query(F.data == "admin:block")
@inject
async def admin_block_prompt(
    call: CallbackQuery,
    state: FSMContext,
):
    if not await _ensure_admin(state):
        await call.answer("Недостаточно прав", show_alert=True)
        return
    await state.update_data(admin_wait_block=True)
    await call.answer()
    await call.message.edit_text("⛔ Введи telegram_id или @username для блокировки", reply_markup=admin_back_keyboard())


@router.callback_query(F.data == "admin:unblock")
@inject
async def admin_unblock_prompt(
    call: CallbackQuery,
    state: FSMContext,
):
    if not await _ensure_admin(state):
        await call.answer("Недостаточно прав", show_alert=True)
        return
    await state.update_data(admin_wait_unblock=True)
    await call.answer()
    await call.message.edit_text("✅ Введи telegram_id или @username для разблокировки", reply_markup=admin_back_keyboard())


