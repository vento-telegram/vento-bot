from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    Message,
    PreCheckoutQuery,
)
from dependency_injector.wiring import Provide, inject

from bot.constants import settings_models_mapper
from bot.container import Container
from bot.enums import BotModeEnum, LedgerReasonEnum
from bot.interfaces.services.user import AbcUserService
from bot.interfaces.services.settings import AbcSettingsService
from bot.keyboards.change_ai import mode_keyboard, gpt_image_size_keyboard
from bot.keyboards.veo import veo_aspect_keyboard, veo_quality_keyboard, veo_main_settings_keyboard
from bot.keyboards.suno import (
    suno_styles_keyboard,
    suno_back_keyboard,
    suno_vocals_keyboard,
    suno_prompt_keyboard,
    suno_input_mode_keyboard,
    suno_main_settings_keyboard,
)
from bot.keyboards.start import (
    account_keyboard,
    start_keyboard,
)
from bot.keyboards.payments import payments_keyboard, payments_back_keyboard, ru_bundles_keyboard, ru_bundles_back_keyboard, pay_link_keyboard, stars_bundles_keyboard
from bot.interfaces.services.payments import AbcPaymentsService
from bot.enums import BotModeEnum
from bot.interfaces.services.veo import AbcVeoService

router = Router()
@router.callback_query(F.data == "set_mode:veo_video")
@inject
async def set_mode_veo_video(
    call: CallbackQuery,
    state: FSMContext,
    settings: AbcSettingsService = Provide[Container.settings_service],
):
    await state.update_data(mode=BotModeEnum.veo_video, veo_aspect=None, veo_quality=None, veo_images=None)
    await call.answer("Режим Veo 3 активирован")
    try:
        await call.message.edit_reply_markup(reply_markup=mode_keyboard(BotModeEnum.veo_video))
    except Exception:
        pass
    std = int(await settings.get_value('veo_standard_price'))
    imp = int(await settings.get_value('veo_improved_price'))
    text = (
        "🎬 Выбери настройки генерируемого видео (формат и качество).\n\n"
        "⏩ Когда настройки выбраны, просто отправь запрос с описанием нужного видео или сценарием.\n\n"
        "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start"
    )
    await call.message.answer(text, reply_markup=veo_main_settings_keyboard(None, None, std, imp))
@router.callback_query(F.data.startswith("veo:quality:"))
@inject
async def veo_set_quality(
    call: CallbackQuery,
    state: FSMContext,
    settings: AbcSettingsService = Provide[Container.settings_service],
):
    q = (call.data or "").split(":")[-1]
    if q not in {"standard", "improved"}:
        await call.answer("Некорректное качество", show_alert=True)
        return
    await state.update_data(veo_quality=q)
    std = int(await settings.get_value('veo_standard_price'))
    imp = int(await settings.get_value('veo_improved_price'))
    await call.answer("Качество выбрано")
    data = await state.get_data()
    aspect = data.get('veo_aspect', None)
    main_text = (
        "🎬 Выбери настройки генерируемого видео (формат и качество).\n\n"
        "⏩ Когда настройки выбраны, просто отправь запрос с описанием нужного видео или сценарием.\n\n"
        "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start"
    )
    try:
        await call.message.edit_text(main_text, reply_markup=veo_main_settings_keyboard(aspect, q, std, imp))
    except Exception:
        try:
            await call.message.edit_reply_markup(reply_markup=veo_main_settings_keyboard(aspect, q, std, imp))
        except Exception:
            pass


@router.callback_query(F.data.startswith("veo:aspect:"))
@inject
async def veo_set_aspect(
    call: CallbackQuery,
    state: FSMContext,
    settings: AbcSettingsService = Provide[Container.settings_service],
):
    raw = call.data or ""
    prefix = "veo:aspect:"
    aspect = raw[len(prefix):] if raw.startswith(prefix) else raw.split(":", maxsplit=2)[-1]
    if aspect not in {"16:9", "9:16"}:
        await call.answer("Некорректное соотношение", show_alert=True)
        return
    await state.update_data(veo_aspect=aspect)
    await call.answer(f"Формат: {aspect}")
    # Re-render single menu
    std = int(await settings.get_value('veo_standard_price'))
    imp = int(await settings.get_value('veo_improved_price'))
    data = await state.get_data()
    q = data.get('veo_quality')
    main_text = (
        "🎬 Выбери настройки генерируемого видео (формат и качество).\n\n"
        "⏩ Когда настройки выбраны, просто отправь запрос с описанием нужного видео или сценарием.\n\n"
        "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start"
    )
    try:
        await call.message.edit_text(main_text, reply_markup=veo_main_settings_keyboard(aspect, q, std, imp))
    except Exception:
        try:
            await call.message.edit_reply_markup(reply_markup=veo_main_settings_keyboard(aspect, q, std, imp))
        except Exception:
            pass


@router.callback_query(F.data == "veo:open:quality")
@inject
async def veo_open_quality(
    call: CallbackQuery,
    state: FSMContext,
    settings: AbcSettingsService = Provide[Container.settings_service],
):
    std = int(await settings.get_value('veo_standard_price'))
    imp = int(await settings.get_value('veo_improved_price'))
    data = await state.get_data()
    q = data.get('veo_quality')
    await call.answer()
    # Show quality explanation text with prices, keep buttons without prices
    text = (
        "💎 Выбери качество генерируемого видеоролика. От качества зависит цена генерации:\n\n"
        f"⚖️ Стандартное качество - {std} токенов/запрос\n\n"
        f"✨ Улучшенное качество - {imp} токенов/запрос\n\n"
        f"ℹ️ Цена не суммируется с доплатой за формат. При генерации улучшенного видео 9:16 цена будет {imp} токенов/запрос"
    )
    try:
        await call.message.edit_text(text=text, reply_markup=veo_quality_keyboard(std, imp, selected=q))
    except Exception:
        await call.message.edit_reply_markup(reply_markup=veo_quality_keyboard(std, imp, selected=q))


@router.callback_query(F.data == "veo:open:aspect")
@inject
async def veo_open_aspect(
    call: CallbackQuery,
    state: FSMContext,
    settings: AbcSettingsService = Provide[Container.settings_service],
):
    data = await state.get_data()
    aspect = data.get('veo_aspect', None)
    std = int(await settings.get_value('veo_standard_price'))
    imp = int(await settings.get_value('veo_improved_price'))
    await call.answer()
    try:
        await call.message.edit_text(
            (
                "📐 Выбери соотношение сторон видеоролика.\n\n"
                f"🖥️ 16:9 — {std} токенов/запрос\n\n"
                f"📱 9:16 — {imp} токенов/запрос\n\n"
                    f"ℹ️ Цена не суммируется с доплатой за качество. При генерации улучшенного видео 9:16 цена будет {imp} токенов/запрос"
            ),
            reply_markup=veo_aspect_keyboard(aspect),
        )
    except Exception:
        await call.message.edit_reply_markup(reply_markup=veo_aspect_keyboard(aspect))


@router.callback_query(F.data == "veo:main")
@inject
async def veo_back_to_main(
    call: CallbackQuery,
    state: FSMContext,
    settings: AbcSettingsService = Provide[Container.settings_service],
):
    data = await state.get_data()
    q = data.get('veo_quality')
    aspect = data.get('veo_aspect', None)
    std = int(await settings.get_value('veo_standard_price'))
    imp = int(await settings.get_value('veo_improved_price'))
    await call.answer()
    text = (
        "🎬 Выбери настройки генерируемого видео (формат и качество).\n\n"
        "⏩ Когда настройки выбраны, просто отправь запрос с описанием нужного видео или сценарием.\n\n"
        "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start"
    )
    try:
        await call.message.edit_text(text, reply_markup=veo_main_settings_keyboard(aspect, q, std, imp))
    except Exception:
        try:
            await call.message.edit_reply_markup(reply_markup=veo_main_settings_keyboard(aspect, q, std, imp))
        except Exception:
            pass
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
            "🎤 Опиши нужный стиль (жанры), например: 'Жесткий дабстеп, 90 bpm'",
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
    data = await state.get_data()
    try:
        await call.message.edit_text(
            "🎵 Выбери настройки генерации музыкальной композиции (стиль, вокал, режим ввода).\n\n"
            "⏩ Когда настройки выбраны, просто отправь запрос с описанием нужной композиции или текстом.\n\n"
            "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start",
            reply_markup=suno_main_settings_keyboard(label, data.get('suno_instrumental'), data.get('suno_custom_mode')),
        )
    except Exception:
        await call.message.edit_reply_markup(reply_markup=suno_main_settings_keyboard(label, data.get('suno_instrumental'), data.get('suno_custom_mode')))

@router.callback_query(F.data == "suno:change_style")
@inject
async def suno_change_style(
    call: CallbackQuery,
    state: FSMContext,
):
    await state.update_data(suno_style=None, suno_style_pending=True)
    await call.answer()
    await call.message.edit_text(
        "🎤 Опиши нужный стиль (жанры), например: 'Жесткий дабстеп, 90 bpm'",
    )


@router.callback_query(F.data == "suno:open:style")
@inject
async def suno_open_style(
    call: CallbackQuery,
    state: FSMContext,
):
    await call.answer()
    try:
        await call.message.edit_text(
            "💥 Выбери стиль:",
            reply_markup=suno_styles_keyboard(None),
        )
    except Exception:
        await call.message.edit_reply_markup(reply_markup=suno_styles_keyboard(None))


@router.callback_query(F.data == "suno:open:vocals")
@inject
async def suno_open_vocals(
    call: CallbackQuery,
    state: FSMContext,
):
    await call.answer()
    try:
        await call.message.edit_text(
            "🎤 Добавить вокал?",
            reply_markup=suno_vocals_keyboard(),
        )
    except Exception:
        await call.message.edit_reply_markup(reply_markup=suno_vocals_keyboard())


@router.callback_query(F.data == "suno:open:input")
@inject
async def suno_open_input(
    call: CallbackQuery,
    state: FSMContext,
):
    await call.answer()
    try:
        await call.message.edit_text(
            "💭 Выбери режим ввода:",
            reply_markup=suno_input_mode_keyboard(),
        )
    except Exception:
        await call.message.edit_reply_markup(reply_markup=suno_input_mode_keyboard())


@router.callback_query(F.data == "suno:main")
@inject
async def suno_back_to_main(
    call: CallbackQuery,
    state: FSMContext,
):
    data = await state.get_data()
    await call.answer()
    try:
        await call.message.edit_text(
            "🎵 Выбери настройки генерации музыкальной композиции (стиль, вокал, режим ввода).\n\n"
            "⏩ Когда настройки выбраны, просто отправь запрос с описанием нужной композиции или текстом.\n\n"
            "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start",
            reply_markup=suno_main_settings_keyboard(
                data.get('suno_style'),
                data.get('suno_instrumental'),
                data.get('suno_custom_mode'),
            ),
        )
    except Exception:
        await call.message.edit_reply_markup(
            reply_markup=suno_main_settings_keyboard(
                data.get('suno_style'),
                data.get('suno_instrumental'),
                data.get('suno_custom_mode'),
            )
        )


@router.callback_query(F.data.startswith("suno:vocals:"))
@inject
async def suno_set_vocals(
    call: CallbackQuery,
    state: FSMContext,
):
    value = (call.data or "").split(":")[-1]
    if value == "yes":
        await state.update_data(suno_instrumental=False)
        await call.answer("Вокал добавлен")
    elif value == "no":
        await state.update_data(suno_instrumental=True)
        await call.answer("Инструментал выбран")
    elif value == "back":
        data = await state.get_data()
        await call.message.edit_reply_markup(reply_markup=suno_main_settings_keyboard(data.get('suno_style'), data.get('suno_instrumental'), data.get('suno_custom_mode')))
        return
    else:
        await call.answer("Некорректное значение", show_alert=True)
        return
    # After choosing vocals, ask if user wants to provide lyrics or just a description
    data = await state.get_data()
    try:
        await call.message.edit_text(
            "🎵 Выбери настройки генерации музыкальной композиции (стиль, вокал, режим ввода).\n\n"
            "⏩ Когда настройки выбраны, просто отправь запрос с описанием нужной композиции или текстом.\n\n"
            "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start",
            reply_markup=suno_main_settings_keyboard(data.get('suno_style'), data.get('suno_instrumental'), data.get('suno_custom_mode')),
        )
    except Exception:
        await call.message.edit_reply_markup(reply_markup=suno_main_settings_keyboard(data.get('suno_style'), data.get('suno_instrumental'), data.get('suno_custom_mode')))


@router.callback_query(F.data.startswith("suno:im:"))
@inject
async def suno_input_mode_selected(
    call: CallbackQuery,
    state: FSMContext,
):
    value = (call.data or "").split(":")[-1]
    if value == "custom":
        await state.update_data(suno_custom_mode=True)
    elif value == "desc":
        await state.update_data(suno_custom_mode=False)
    else:
        await call.answer("Некорректное значение", show_alert=True)
        return
    data = await state.get_data()
    try:
        await call.message.edit_text(
            "🎵 Выбери настройки генерации музыкальной композиции (стиль, вокал, режим ввода).\n\n"
            "⏩ Когда настройки выбраны, просто отправь запрос с описанием нужной композиции или текстом.\n\n"
            "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start",
            reply_markup=suno_main_settings_keyboard(data.get('suno_style'), data.get('suno_instrumental'), data.get('suno_custom_mode')),
        )
    except Exception:
        await call.message.edit_reply_markup(reply_markup=suno_main_settings_keyboard(data.get('suno_style'), data.get('suno_instrumental'), data.get('suno_custom_mode')))


@router.callback_query(F.data == "set_mode:gpt")
@inject
async def set_mode_chatgpt(
    call: CallbackQuery,
    state: FSMContext,
):
    # Always re-select: reset short-term context/history
    await state.update_data(mode=BotModeEnum.gpt, history=[])
    await call.answer("Режим GPT активирован")
    # Guard against "message is not modified"
    try:
        await call.message.edit_reply_markup(reply_markup=mode_keyboard(BotModeEnum.gpt))
    except Exception:
        pass
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
    await state.update_data(mode=BotModeEnum.gpt_mini, history=[])
    await call.answer("Режим GPT Mini активирован")
    try:
        await call.message.edit_reply_markup(reply_markup=mode_keyboard(BotModeEnum.gpt_mini))
    except Exception:
        pass
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
    await state.update_data(mode=BotModeEnum.gpt_image, gpt_image_size="1:1", history=[])
    await call.answer("Режим GPT Image активирован")
    try:
        await call.message.edit_reply_markup(reply_markup=mode_keyboard(BotModeEnum.gpt_image))
    except Exception:
        pass
    text = (
        "🖊️ Отправь текст, чтобы создать изображение.\n\n"
        "🖼️ Отправь фото с подписью, чтобы отредактировать изображение.\n\n"
        "📐 Текущий размер: 1:1. Его можно сменить кнопками под сообщением.\n\n"
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
    await state.update_data(mode=BotModeEnum.nano_banana, history=[])
    await call.answer("Режим Nano Banana активирован")
    try:
        await call.message.edit_reply_markup(reply_markup=mode_keyboard(BotModeEnum.nano_banana))
    except Exception:
        pass
    await call.message.answer(
        "🖊️ Отправь текст, чтобы создать изображение.\n\n"
        "🖼️ Отправь фото с подписью, чтобы отредактировать изображение.\n\n"
        "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start"
    )

@router.callback_query(F.data == "set_mode:suno_music")
@inject
async def set_mode_suno_music(
    call: CallbackQuery,
    state: FSMContext,
):
    await state.update_data(mode=BotModeEnum.suno_music, suno_style=None, suno_style_pending=False, suno_instrumental=None, suno_custom_mode=None, history=[])
    await call.answer("Режим Suno активирован")
    try:
        await call.message.edit_reply_markup(reply_markup=mode_keyboard(BotModeEnum.suno_music))
    except Exception:
        pass
    text = (
        "🎵 Выбери настройки генерации музыкальной композиции (стиль, вокал, режим ввода).\n\n"
        "⏩ Когда настройки выбраны, просто отправь запрос с описанием нужной композиции или текстом.\n\n"
        "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start"
    )
    await call.message.answer(text, reply_markup=suno_main_settings_keyboard(None, None, None))

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
                "🖊️ Отправь текст, чтобы создать изображение.\n\n"
                "🖼️ Отправь фото с подписью, чтобы отредактировать изображение.\n\n"
                f"📐 Текущий размер: {size}. Его можно сменить кнопками под сообщением.\n\n"
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
    settings: AbcSettingsService = Provide[Container.settings_service],
):
    await call.answer()
    await call.message.edit_text(
        text=(
            "⭐ *Оплата звёздами*\n\n"
            "Выберите пакет токенов:"),
        reply_markup=await stars_bundles_keyboard(settings),
    )

@router.pre_checkout_query()
@inject
async def stars_pre_checkout(
    query: PreCheckoutQuery,
):
    try:
        await query.answer(ok=True)
    except Exception:
        pass


@router.message(F.successful_payment)
@inject
async def stars_successful_payment(
    message: Message,
    user_service: AbcUserService = Provide[Container.user_service],
):
    sp = message.successful_payment
    if not sp or (sp.currency or "").upper() != "XTR":
        return
    payload = sp.invoice_payload or ""
    # Expected: stars:{tokens}:{stars}
    parts = payload.split(":", maxsplit=2)
    try:
        tokens = int(parts[1]) if len(parts) >= 2 else 0
    except Exception:
        tokens = 0
    if tokens <= 0:
        return
    try:
        updated_user = await user_service.add_tokens_by_telegram_id(
            telegram_id=message.from_user.id,
            amount=tokens,
            reason=LedgerReasonEnum.purchase_stars,
        )
        balance = updated_user.balance if updated_user else None
        balance_text = f"*{balance}*" if balance is not None else "обновлён"
        await message.answer(
            text=(
                f"✅ Оплата прошла успешно! Зачислено {tokens} токенов.\n\n"
                f"🪙 Твой баланс: {balance_text} токенов\n\n"
                "👇 Что хочешь сделать?"
            ),
            reply_markup=start_keyboard(BotModeEnum.passive),
        )
    except Exception:
        # Even if crediting failed, avoid raising in handler
        await message.answer(
            text=(
                "✅ Оплата прошла. Начисление будет обработано автоматически в ближайшее время."),
            reply_markup=start_keyboard(BotModeEnum.passive),
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
    # Pass admin flag to show admin button when applicable
    user = await service.get_user(call.from_user.id)
    is_admin = bool(getattr(user, 'is_admin', False))
    await call.message.edit_text(
        text=text,
        reply_markup=start_keyboard(current_mode, is_admin=is_admin),
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
    veo_standard = await settings.get_value('veo_standard_price')

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
        f"🎵 *Suno* ({suno_price} токенов/запрос)\n"
        "Генерация музыки по стилю, описанию/тексту.\n\n"
        f"🎬 *Veo 3* (от {veo_standard} токенов/запрос)\n"
        "Генерация видео по тексту или картинке.\n\n"
        "👇 Выбери нужный ИИ:"
    )

    await call.message.edit_text(
        text=text,
        reply_markup=mode_keyboard(current_mode)
    )
    await call.answer("Выбери режим работы")
