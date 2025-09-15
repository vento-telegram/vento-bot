from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
)
from dependency_injector.wiring import Provide, inject

from bot.constants import settings_models_mapper
from bot.container import Container
from bot.enums import BotModeEnum
from bot.interfaces.services.user import AbcUserService
from bot.interfaces.services.settings import AbcSettingsService
from bot.keyboards.change_ai import mode_keyboard, gpt_image_size_keyboard
from bot.keyboards.suno import suno_styles_keyboard, suno_back_keyboard
from bot.keyboards.start import (
    account_keyboard,
    start_keyboard,
)
from bot.keyboards.payments import payments_keyboard, payments_back_keyboard, ru_bundles_keyboard, ru_bundles_back_keyboard, pay_link_keyboard
from bot.interfaces.services.payments import AbcPaymentsService
from bot.enums import BotModeEnum

router = Router()
@router.callback_query(F.data.startswith("suno:style:"))
@inject
async def suno_select_style(
    call: CallbackQuery,
    state: FSMContext,
):
    raw = call.data or ""
    prefix = "suno:style:"
    style_slug = raw[len(prefix):] if raw.startswith(prefix) else raw.split(":", maxsplit=2)[-1]
    if style_slug == "custom":
        await state.update_data(suno_style=None, suno_style_pending=True)
        await call.message.edit_text(
            "🧑‍🎤 Напиши свой стиль (жанры/описание), например: 'Pop, Dreamy, 90 BPM'",
            reply_markup=suno_back_keyboard()
        )
        await call.answer()
        return
    # Map simple slug to readable label
    slug_to_label = {
        "pop": "Pop",
        "rock": "Rock",
        "hiphop": "Hip-hop",
        "edm": "EDM",
        "electronic": "Electronic",
        "lofi": "Lo-fi",
        "jazz": "Jazz",
        "classical": "Classical",
        "ambient": "Ambient",
        "folk": "Folk",
    }
    label = slug_to_label.get(style_slug, style_slug)
    await state.update_data(suno_style=label, suno_style_pending=False)
    await call.answer(f"Стиль: {label}")
    try:
        await call.message.edit_text(
            (
                f"🎼 Стиль выбран: *{label}*\n\n"
                "Теперь пришли промпт — текст песни/описание."
            ),
            reply_markup=suno_back_keyboard(),
        )
    except Exception:
        await call.message.answer(
            f"🎼 Стиль выбран: *{label}*\n\nТеперь пришли промпт — текст песни/описание.",
            reply_markup=suno_back_keyboard(),
        )

@router.callback_query(F.data == "suno:change_style")
@inject
async def suno_change_style(
    call: CallbackQuery,
    state: FSMContext,
):
    await state.update_data(suno_style=None, suno_style_pending=False)
    await call.answer()
    await call.message.edit_text(
        "Выбери стиль:",
        reply_markup=suno_styles_keyboard(),
    )


@router.callback_query(F.data.startswith("suno:vocals:"))
@inject
async def suno_set_vocals(
    call: CallbackQuery,
    state: FSMContext,
):
    value = (call.data or "").split(":")[-1]
    if value == "on":
        await state.update_data(suno_instrumental=False)
        await call.answer("Вокал: ВКЛ")
    elif value == "off":
        await state.update_data(suno_instrumental=True)
        await call.answer("Инструментал: ВКЛ")
    else:
        await call.answer("Некорректное значение", show_alert=True)
        return
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass


@router.callback_query(F.data == "set_mode:gpt")
@inject
async def set_mode_chatgpt(
    call: CallbackQuery,
    state: FSMContext,
):
    await state.update_data(mode=BotModeEnum.gpt)
    await call.answer("Режим GPT активирован")
    await call.message.edit_reply_markup(reply_markup=mode_keyboard(BotModeEnum.gpt))
    await call.message.answer(
        "🤖 Теперь на твои сообщения будет отвечать *GPT-5*.\n\n"
        "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start"
    )

@router.callback_query(F.data == "set_mode:gpt_mini")
@inject
async def set_mode_chatgpt_mini(
    call: CallbackQuery,
    state: FSMContext,
):
    await state.update_data(mode=BotModeEnum.gpt_mini)
    await call.answer("Режим GPT Mini активирован")
    await call.message.edit_reply_markup(reply_markup=mode_keyboard(BotModeEnum.gpt_mini))
    await call.message.answer(
        "⚡ Теперь на твои сообщения будет отвечать *GPT-5 Mini*.\n\n"
        "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start"
    )

@router.callback_query(F.data == "set_mode:gpt_image")
@inject
async def set_mode_gpt_image(
    call: CallbackQuery,
    state: FSMContext,
):
    await state.update_data(mode=BotModeEnum.gpt_image, gpt_image_size="1:1")
    await call.answer("Режим GPT Image активирован")
    await call.message.edit_reply_markup(reply_markup=mode_keyboard(BotModeEnum.gpt_image))
    text = (
        "🖼️ Теперь ты можешь генерировать изображения. Отправь промпт — получишь картинку.\n\n"
        "📐 Текущий размер: *1:1*. Его можно сменить кнопками под сообщением.\n\n"
        "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start"
    )
    await call.message.answer(
        text,
        reply_markup=gpt_image_size_keyboard("1:1"),
    )

@router.callback_query(F.data == "set_mode:nano_banana")
@inject
async def set_mode_nano_banana(
    call: CallbackQuery,
    state: FSMContext,
):
    await state.update_data(mode=BotModeEnum.nano_banana)
    await call.answer("Режим Nano Banana активирован")
    await call.message.edit_reply_markup(reply_markup=mode_keyboard(BotModeEnum.nano_banana))
    await call.message.answer(
        "🍌 *Nano Banana*\n\n"
        "Отправь текст, чтобы *создать* изображение.\n"
        "Отправь фото с подписью, чтобы *отредактировать* изображение.\n\n"
        "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start"
    )

@router.callback_query(F.data == "set_mode:suno_music")
@inject
async def set_mode_suno_music(
    call: CallbackQuery,
    state: FSMContext,
):
    await state.update_data(mode=BotModeEnum.suno_music, suno_style=None, suno_style_pending=False)
    await call.answer("Режим Suno Music активирован")
    await call.message.edit_reply_markup(reply_markup=mode_keyboard(BotModeEnum.suno_music))
    text = (
        "🎵 Сначала выбери стиль, затем пришли промпт (текст песни/описание).\n\n🔄 Если захочешь сменить режим или очистить контекст — используй команду /start"
    )
    await call.message.answer(text, reply_markup=suno_styles_keyboard())

@router.callback_query(F.data.startswith("gpt_image:size:"))
@inject
async def set_gpt_image_size(
    call: CallbackQuery,
    state: FSMContext,
):
    raw = call.data or ""
    prefix = "gpt_image:size:"
    size = raw[len(prefix):] if raw.startswith(prefix) else raw.split(":", maxsplit=2)[-1]
    if size not in {"1:1", "3:2", "2:3"}:
        await call.answer("Неверный размер", show_alert=True)
        return
    await state.update_data(gpt_image_size=size)
    await call.answer(f"Размер изображения: {size}")
    # Update the last message text (if possible) or just update buttons
    try:
        await call.message.edit_text(
            text=(
                "🖼️ Теперь ты можешь генерировать изображения. Отправь промпт — получишь картинку.\n\n"
                f"📐 Текущий размер: *{size}*. Его можно сменить кнопками под сообщением.\n\n"
                "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start"
            ),
            reply_markup=gpt_image_size_keyboard(size),
        )
    except Exception:
        await call.message.edit_reply_markup(reply_markup=gpt_image_size_keyboard(size))

@router.callback_query(F.data == "goto:account")
@inject
async def goto_account(
    call: CallbackQuery,
    service: AbcUserService = Provide[Container.user_service],
    settings: AbcSettingsService = Provide[Container.settings_service],
):
    await call.answer()

    first_name = call.from_user.first_name
    last_name = call.from_user.last_name if call.from_user.last_name else None
    username = call.from_user.username if call.from_user.username else None
    user = await service.get_user(call.from_user.id)

    display_name_parts = [first_name or ""]
    if last_name:
        display_name_parts.append(f" {last_name}")
    if username:
        display_name_parts.append(f" (@{username})")
    display_name = "".join(display_name_parts)

    daily_bonus = await settings.get_value("daily_bonus")

    await call.message.edit_text(
        text=(
            f"🎟️ *Аккаунт*\n\n"
            f"🐻‍❄️ *{display_name}*\n\n"
            f"🪙 Баланс: *{user.balance}* токенов\n"
            f"🎁 Ежедневно: *{daily_bonus}* токенов\n\n"
            f"👇 Действия:"
        ),
        reply_markup=account_keyboard,
    )
@router.callback_query(F.data == "goto:replenish")
@inject
async def goto_replenish(
    call: CallbackQuery,
):
    await call.answer()
    await call.message.edit_text(
        text=(
            "💳 *Пополнение баланса*\n\n"
            "Выбери удобный способ оплаты:"),
        reply_markup=payments_keyboard(),
    )


@router.callback_query(F.data == "pay:ru")
@inject
async def pay_ru(
    call: CallbackQuery,
    settings: AbcSettingsService = Provide[Container.settings_service],
):
    await call.answer()
    bundle_token_amounts = [700, 1600, 4500, 11000, 28000]
    bundles: list[tuple[int, int]] = []
    for amount in bundle_token_amounts:
        price_value = await settings.get_value(f"{amount}_bundle_price")
        try:
            price = int(price_value)
        except Exception:
            price = 0
        bundles.append((amount, price))
    await call.message.edit_text(
        text=(
            "🇷🇺 *SberPay | T‑Pay | ЮMoney*\n\n"
            "⚠️ Временно не принимаем оплату по номеру карты МИР.\n"
            "Пожалуйста, используй SberPay, T‑Pay или ЮMoney.\n\n"
            "Выбери пакет токенов:"),
        reply_markup=ru_bundles_keyboard(bundles),
    )


@router.callback_query(F.data.startswith("pay:ru:"))
@inject
async def pay_ru_bundle_selected(
    call: CallbackQuery,
    settings: AbcSettingsService = Provide[Container.settings_service],
    payments: AbcPaymentsService = Provide[Container.payments_service],
):
    await call.answer()
    parts = (call.data or "").split(":", maxsplit=2)
    tokens = parts[-1] if parts and len(parts) >= 3 else ""
    price_value = await settings.get_value(f"{tokens}_bundle_price")
    try:
        price = int(price_value)
    except Exception:
        price = 0
    try:
        confirm_url = await payments.create_ru_payment(user_id=call.from_user.id, tokens=int(tokens), price_rub=price)
        await call.message.edit_text(
            text=(
                f"🧾 *Вы выбрали*: {tokens} токенов — {price} ₽\n\n"
                "Нажми кнопку, чтобы перейти к оплате."),
            reply_markup=pay_link_keyboard(confirm_url),
        )
    except Exception:
        await call.message.edit_text(
            text=(
                "☹️ Не удалось создать платёж. Попробуй ещё раз позже."),
            reply_markup=ru_bundles_back_keyboard(),
        )


@router.callback_query(F.data == "pay:stars")
@inject
async def pay_stars(
    call: CallbackQuery,
):
    await call.answer()
    await call.message.edit_text(
        text=(
            "⭐ *Оплата звёздами*\n\n"
            "Скоро можно будет обменять звёзды на токены прямо здесь."),
        reply_markup=payments_back_keyboard(),
    )


@router.callback_query(F.data == "pay:crypto")
@inject
async def pay_crypto(
    call: CallbackQuery,
):
    await call.answer()
    await call.message.edit_text(
        text=(
            "🪙 *Крипто‑оплата*\n\n"
            "Скоро добавим крипто‑платёж: покажем адрес и сумму, зачисление — автоматически."),
        reply_markup=payments_back_keyboard(),
    )


@router.callback_query(F.data == "goto:start")
@inject
async def goto_start(
    call: CallbackQuery,
    state: FSMContext,
    service: AbcUserService = Provide[Container.user_service],
    settings: AbcSettingsService = Provide[Container.settings_service],
):
    await call.answer()

    await state.update_data(history=[])
    user, _ = await service.is_user_new(call.from_user)
    current_mode = (await state.get_data()).get('mode', BotModeEnum.passive)
    text = (
        f"👋 Привет, *{call.from_user.first_name}*!\n\n"
        f"🪙 Твой баланс: *{user.balance}* токенов\n\n"
        f"🤖 Текущий ИИ: *{current_mode}*\n"
    )

    if current_mode != BotModeEnum.passive:
        price = await settings.get_value(settings_models_mapper[current_mode])
        text += f"💸 Цена запроса: *{price} токенов*\n\n"
    else:
        text += "\n"

    text += "👇 Что хочешь сделать?"
    await call.message.edit_text(
        text=text,
        reply_markup=start_keyboard(current_mode),
    )

@router.callback_query(F.data == "goto:switch")
@inject
async def goto_switch(
    call: CallbackQuery,
    state: FSMContext,
    settings: AbcSettingsService = Provide[Container.settings_service],
):
    current_mode = (await state.get_data()).get("mode", BotModeEnum.passive)

    gpt_price = await settings.get_value(settings_models_mapper[BotModeEnum.gpt])
    mini_price = await settings.get_value(settings_models_mapper[BotModeEnum.gpt_mini])
    image_price = await settings.get_value(settings_models_mapper[BotModeEnum.gpt_image])
    nano_price = await settings.get_value(settings_models_mapper[BotModeEnum.nano_banana])
    suno_price = await settings.get_value(settings_models_mapper[BotModeEnum.suno_music])

    text = (
        "👾 *Выбор ИИ*\n\n"
        f"🤖 *GPT‑5* ({gpt_price} токенов/запрос)\n"
        "Самый продвинутый ИИ-чат.\n\n"
        f"⚡ *GPT‑5 Mini* ({mini_price} токенов/запрос)\n"
        "Быстрые и экономные ответы.\n\n"
        f"🖼️ *GPT Image* ({image_price} токенов/запрос)\n"
        "Генерация картинок по описанию.\n\n"
        f"🍌 *Nano Banana* ({nano_price} токенов/запрос)\n"
        "Создание и редактирование изображений.\n\n"
        f"🎵 *Suno Music* ({suno_price} токенов/запрос)\n"
        "Генерация музыки по стилю и описанию.\n\n"
        "👇 Выбери нужный ИИ:"
    )

    await call.message.edit_text(
        text=text,
        reply_markup=mode_keyboard(current_mode)
    )
    await call.answer("Выбери режим работы")
