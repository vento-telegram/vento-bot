from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
    FSInputFile,
    InlineKeyboardMarkup,
)
from pathlib import Path
from dependency_injector.wiring import Provide, inject

from bot.constants import settings_models_mapper
from bot.container import Container
from bot.enums import BotModeEnum, TransactionReasonEnum
from bot.interfaces.services.payments import AbcPaymentsService
from bot.interfaces.services.settings import AbcSettingsService
from bot.interfaces.services.user import AbcUserService
from bot.interfaces.services.subscription import AbcSubscriptionService
from bot.keyboards.change_ai import mode_keyboard
from bot.keyboards.payments import (
    card_bundles_keyboard,
    card_byn_bundles_keyboard,
    pay_link_keyboard,
    payments_back_keyboard,
    payments_keyboard,
    ru_bundles_back_keyboard,
    ru_bundles_keyboard,
    stars_bundles_keyboard,
)
from bot.keyboards.referral import referral_keyboard, referral_bonus_keyboard
from bot.keyboards.start import (
    start_keyboard,
)
from bot.keyboards.suno import (
    suno_back_keyboard,
    suno_input_mode_keyboard,
    suno_main_settings_keyboard,
    suno_styles_keyboard,
    suno_vocals_keyboard,
)
from bot.keyboards.veo import (
    veo_aspect_keyboard,
    veo_main_settings_keyboard,
    veo_quality_keyboard,
)
from bot.keyboards.nano import (
    NANO_FORMAT_OPTIONS,
    nano_format_keyboard,
    nano_main_settings_keyboard,
)
from bot.keyboards.sora2 import (
    sora2_aspect_keyboard,
    sora2_main_settings_keyboard,
)
from bot.keyboards.sora2_pro import (
    sora2pro_aspect_keyboard,
    sora2pro_duration_keyboard,
    sora2pro_main_settings_keyboard,
)
from bot.settings import settings
from sqlalchemy import select, func

router = Router()

NANO_MODE_TEXT = (
    "📏 Выбери формат картинки. \n\n"
    "🖊️ Отправь текст, чтобы создать изображение.\n\n"
    "🖼️ Отправь фото с подписью, чтобы отредактировать изображение.\n\n"
    "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start\n\n"
)
NANO_CHOOSE_FORMAT_TEXT = "Выбери формат изображения для Nano Banana:"

# Helper: check if user has ever purchased any token bundle
from sqlalchemy import select
from bot.interfaces.uow import AbcUnitOfWork
from bot.database.models import TransactionOrm, UserOrm
from bot.entities.transaction import TransactionEntity


@inject
async def _has_any_token_purchase(
    telegram_id: int,
    uow: AbcUnitOfWork = Provide[Container.uow],
) -> bool:
    try:
        async with uow:
            user = await uow.user.get_by_telegram_id(telegram_id)
            if not user:
                return False
            reasons = [
                str(TransactionReasonEnum.purchase_stars),
                str(TransactionReasonEnum.purchase_bepaid),
                str(TransactionReasonEnum.purchase_yookassa),
            ]
            stmt = (
                select(TransactionOrm.id)
                .where(TransactionOrm.user_id == user.id, TransactionOrm.reason.in_(reasons))
                .limit(1)
            )
            result = await uow.transaction.session.execute(stmt)
            return result.first() is not None
    except Exception:
        return False
@router.callback_query(F.data == "set_mode:veo_video")
@inject
async def set_mode_veo_video(
    call: CallbackQuery,
    state: FSMContext,
    settings: AbcSettingsService = Provide[Container.settings_service],
):
    await state.update_data(mode=BotModeEnum.veo_video, veo_aspect=None, veo_quality=None, veo_images=None)
    await call.answer("Режим Veo 3.1 активирован")
    try:
        await call.message.edit_reply_markup(reply_markup=mode_keyboard(BotModeEnum.veo_video))
    except Exception:
        pass
    std = int(await settings.get_value('veo_standard_price'))
    imp = int(await settings.get_value('veo_improved_price'))
    text = (
        "🎬 Выбери настройки генерируемого видео (формат и качество).\n\n"
        "⏩ Когда настройки выбраны, просто отправь запрос с описанием нужного видео или сценарием, можешь прикрепить картинку.\n\n"
        "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start"
    )
    await call.message.answer(text, reply_markup=veo_main_settings_keyboard(None, None, std, imp))

@router.callback_query(F.data == "set_mode:sora2_video")
@inject
async def set_mode_sora2_video(
    call: CallbackQuery,
    state: FSMContext,
    settings: AbcSettingsService = Provide[Container.settings_service],
):
    await state.update_data(mode=BotModeEnum.sora2_video, sora_aspect=None)
    await call.answer("Режим Sora 2 активирован")
    try:
        await call.message.edit_reply_markup(reply_markup=mode_keyboard(BotModeEnum.sora2_video))
    except Exception:
        pass
    text = (
        "🎬 Выбери формат генерируемого видео\n\n"
        "⏩ Когда настройки выбраны, просто отправь запрос с описанием нужного видео или сценарием, можешь прикрепить картинку.\n\n"
        "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start"
    )
    await call.message.answer(text, reply_markup=sora2_main_settings_keyboard(None))

@router.callback_query(F.data == "set_mode:sora2_pro_video")
@inject
async def set_mode_sora2_pro_video(
    call: CallbackQuery,
    state: FSMContext,
    settings: AbcSettingsService = Provide[Container.settings_service],
):
    await state.update_data(mode=BotModeEnum.sora2_pro_video, sora_pro_aspect=None, sora_pro_frames=None)
    await call.answer("Выбран Sora 2 Pro")
    try:
        await call.message.edit_reply_markup(reply_markup=mode_keyboard(BotModeEnum.sora2_pro_video))
    except Exception:
        pass
    text = (
        "🎥 Выбери формат и длительность генерируемого видео\n\n"
        "⏩ Когда настройки выбраны, просто отправь запрос с описанием нужного видео или сценарием, можешь прикрепить картинку.\n\n"
        "⚠️ Возможны ошибки в работе Sora 2 Pro из-за высокой нагрузки на OpenAI. В этом случае токены будут автоматически возвращены на ваш баланс. Ответы могут занимать до 1 часа.\n\n"
        "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start"
    )
    await call.message.answer(text, reply_markup=sora2pro_main_settings_keyboard(None, None))

@router.callback_query(F.data == "sora2:open")
@inject
async def open_sora2_noedit(
    call: CallbackQuery,
    state: FSMContext,
    settings: AbcSettingsService = Provide[Container.settings_service],
):
    await state.update_data(mode=BotModeEnum.sora2_video, sora_aspect=None)
    await call.answer("Режим Sora 2 активирован")
    text = (
        "🎬 Выбери формат генерируемого видео\n\n"
        "⏩ Когда настройки выбраны, просто отправь запрос с описанием нужного видео или сценарием, можешь прикрепить картинку.\n\n"
        "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start"
    )
    await call.message.answer(text, reply_markup=sora2_main_settings_keyboard(None))

@router.callback_query(F.data == "sora2pro:open")
@inject
async def open_sora2pro_noedit(
    call: CallbackQuery,
    state: FSMContext,
    settings: AbcSettingsService = Provide[Container.settings_service],
):
    await state.update_data(mode=BotModeEnum.sora2_pro_video, sora_pro_aspect=None, sora_pro_frames=None)
    await call.answer("Выбран Sora 2 Pro")
    text = (
        "🎥 Выбери формат и длительность генерируемого видео\n\n"
        "⏩ Когда настройки выбраны, просто отправь запрос с описанием нужного видео или сценарием, можешь прикрепить картинку.\n\n"
        "⚠️ Возможны ошибки в работе Sora 2 Pro из-за высокой нагрузки на OpenAI. В этом случае токены будут автоматически возвращены на ваш баланс. Ответы могут занимать до 1 часа.\n\n"
        "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start"
    )
    await call.message.answer(text, reply_markup=sora2pro_main_settings_keyboard(None, None))

@router.callback_query(F.data.startswith("sora2:aspect:"))
@inject
async def sora2_set_aspect(
    call: CallbackQuery,
    state: FSMContext,
    settings: AbcSettingsService = Provide[Container.settings_service],
):
    raw = call.data or ""
    prefix = "sora2:aspect:"
    aspect = raw[len(prefix):] if raw.startswith(prefix) else raw.split(":", maxsplit=2)[-1]
    if aspect not in {"16:9", "9:16"}:
        await call.answer("Некорректное значение формата", show_alert=True)
        return
    await state.update_data(sora_aspect=aspect)
    await call.answer("Формат выбран")
    text = (
        "🎬 Выбери формат генерируемого видео\n\n"
        "⏩ Когда настройки выбраны, просто отправь запрос с описанием нужного видео или сценарием, можешь прикрепить картинку.\n\n"
        "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start"
    )
    await call.message.edit_text(text=text, reply_markup=sora2_main_settings_keyboard(aspect))

@router.callback_query(F.data.startswith("sora2pro:aspect:"))
@inject
async def sora2pro_set_aspect(
    call: CallbackQuery,
    state: FSMContext,
    settings: AbcSettingsService = Provide[Container.settings_service],
):
    raw = call.data or ""
    prefix = "sora2pro:aspect:"
    aspect = raw[len(prefix):] if raw.startswith(prefix) else raw.split(":", maxsplit=2)[-1]
    if aspect not in {"16:9", "9:16"}:
        await call.answer("Некорректное значение формата", show_alert=True)
        return
    await state.update_data(sora_pro_aspect=aspect)
    await call.answer("Формат выбран")
    text = (
        "🎥 Выбери формат и длительность генерируемого видео\n\n"
        "⏩ Когда настройки выбраны, просто отправь запрос с описанием нужного видео или сценарием, можешь прикрепить картинку.\n\n"
        "⚠️ Возможны ошибки в работе Sora 2 Pro из-за высокой нагрузки на OpenAI. В этом случае токены будут автоматически возвращены на ваш баланс. Ответы могут занимать до 1 часа.\n\n"
        "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start"
    )
    data = await state.get_data()
    await call.message.edit_text(text=text, reply_markup=sora2pro_main_settings_keyboard(aspect, data.get("sora_pro_frames")))

@router.callback_query(F.data == "sora2:open:aspect")
async def sora2_open_aspect(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await call.answer()
    try:
        await call.message.edit_text("📐 Выбери соотношение сторон видеоролика.", reply_markup=sora2_aspect_keyboard(data.get("sora_aspect")))
    except Exception:
        await call.message.edit_reply_markup(reply_markup=sora2_aspect_keyboard(data.get("sora_aspect")))

@router.callback_query(F.data == "sora2pro:open:aspect")
async def sora2pro_open_aspect(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await call.answer()
    try:
        await call.message.edit_text("📐 Выбери соотношение сторон видеоролика.", reply_markup=sora2pro_aspect_keyboard(data.get("sora_pro_aspect")))
    except Exception:
        await call.message.edit_reply_markup(reply_markup=sora2pro_aspect_keyboard(data.get("sora_pro_aspect")))

@router.callback_query(F.data == "sora2pro:open:frames")
async def sora2pro_open_frames(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await call.answer()
    try:
        await call.message.edit_text("⏱️ Выбери длительность ролика.", reply_markup=sora2pro_duration_keyboard(data.get("sora_pro_frames")))
    except Exception:
        await call.message.edit_reply_markup(reply_markup=sora2pro_duration_keyboard(data.get("sora_pro_frames")))

@router.callback_query(F.data.startswith("sora2pro:frames:"))
async def sora2pro_set_frames(call: CallbackQuery, state: FSMContext):
    raw = call.data or ""
    prefix = "sora2pro:frames:"
    n_frames = raw[len(prefix):] if raw.startswith(prefix) else raw.split(":", maxsplit=2)[-1]
    if n_frames not in {"10", "15"}:
        await call.answer("Выбери: 10 или 15 секунд", show_alert=True)
        return
    await state.update_data(sora_pro_frames=n_frames)
    await call.answer("Длительность сохранена")
    data = await state.get_data()
    text = (
        "🎥 Выбери формат и длительность генерируемого видео\n\n"
        "⏩ Когда настройки выбраны, просто отправь запрос с описанием нужного видео или сценарием, можешь прикрепить картинку.\n\n"
        "⚠️ Возможны ошибки в работе Sora 2 Pro из-за высокой нагрузки на OpenAI. В этом случае токены будут автоматически возвращены на ваш баланс. Ответы могут занимать до 1 часа.\n\n"
        "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start"
    )
    await call.message.edit_text(text, reply_markup=sora2pro_main_settings_keyboard(data.get("sora_pro_aspect"), n_frames))

@router.callback_query(F.data == "sora2:main")
async def sora2_back_to_main(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await call.answer()
    text = (
        "🎥 Выбери формат и длительность генерируемого видео\n\n"
        "⏩ Когда настройки выбраны, просто отправь запрос с описанием нужного видео или сценарием, можешь прикрепить картинку.\n\n"
        "⚠️ Возможны ошибки в работе Sora 2 Pro из-за высокой нагрузки на OpenAI. В этом случае токены будут автоматически возвращены на ваш баланс. Ответы могут занимать до 1 часа.\n\n"
        "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start"
    )
    await call.message.edit_text(
        text,
        reply_markup=sora2_main_settings_keyboard(data.get("sora_aspect")),
    )
@router.callback_query(F.data == "sora2pro:main")
async def sora2pro_back_to_main(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await call.answer()
    text = (
        "🎥 Выбери формат и длительность генерируемого видео\n\n"
        "⏩ Когда настройки выбраны, просто отправь запрос с описанием нужного видео или сценарием, можешь прикрепить картинку.\n\n"
        "⚠️ Возможны ошибки в работе Sora 2 Pro из-за высокой нагрузки на OpenAI. В этом случае токены будут автоматически возвращены на ваш баланс. Ответы могут занимать до 1 часа.\n\n"
        "🔄 Если захочешь сменить режим или очистить контекст — используй команду /start"
    )
    await call.message.edit_text(
        text,
        reply_markup=sora2pro_main_settings_keyboard(data.get("sora_pro_aspect"), data.get("sora_pro_frames")),
    )
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
        "⏩ Когда настройки выбраны, просто отправь запрос с описанием нужного видео или сценарием, можешь прикрепить картинку.\n\n"
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
        "⏩ Когда настройки выбраны, просто отправь запрос с описанием нужного видео или сценарием, можешь прикрепить картинку.\n\n"
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
        "⏩ Когда настройки выбраны, просто отправь запрос с описанием нужного видео или сценарием, можешь прикрепить картинку.\n\n"
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

@router.callback_query(F.data == "set_mode:nano_banana")
async def set_mode_nano_banana(
    call: CallbackQuery,
    state: FSMContext,
):
    await state.update_data(mode=BotModeEnum.nano_banana, history=[], nano_format=None)
    await call.answer("Nano Banana выбран")
    try:
        await call.message.edit_reply_markup(reply_markup=mode_keyboard(BotModeEnum.nano_banana))
    except Exception:
        pass
    await call.message.answer(
        NANO_MODE_TEXT,
        reply_markup=nano_main_settings_keyboard(None),
    )

@router.callback_query(F.data == "nano_banana:open")
async def open_nano_banana_noedit(
    call: CallbackQuery,
    state: FSMContext,
):
    data = await state.get_data()
    current_format = data.get("nano_format")
    await state.update_data(mode=BotModeEnum.nano_banana, history=[], nano_format=current_format)
    await call.answer("Nano Banana выбран")
    await call.message.answer(
        NANO_MODE_TEXT,
        reply_markup=nano_main_settings_keyboard(current_format),
    )


@router.callback_query(F.data == "nano:open:format")
async def nano_open_format(
    call: CallbackQuery,
    state: FSMContext,
):
    data = await state.get_data()
    current_format = data.get("nano_format")
    await call.answer()
    try:
        await call.message.edit_text(
            NANO_CHOOSE_FORMAT_TEXT,
            reply_markup=nano_format_keyboard(current_format),
        )
    except Exception:
        try:
            await call.message.edit_reply_markup(reply_markup=nano_format_keyboard(current_format))
        except Exception:
            pass


@router.callback_query(F.data == "nano:main")
async def nano_back_to_main(
    call: CallbackQuery,
    state: FSMContext,
):
    data = await state.get_data()
    current_format = data.get("nano_format")
    await call.answer()
    try:
        await call.message.edit_text(
            NANO_MODE_TEXT,
            reply_markup=nano_main_settings_keyboard(current_format),
        )
    except Exception:
        try:
            await call.message.edit_reply_markup(reply_markup=nano_main_settings_keyboard(current_format))
        except Exception:
            pass


@router.callback_query(F.data.startswith("nano:format:"))
async def nano_set_format(
    call: CallbackQuery,
    state: FSMContext,
):
    raw = call.data or ""
    prefix = "nano:format:"
    format_value = raw[len(prefix):] if raw.startswith(prefix) else raw.split(":", maxsplit=2)[-1]
    if format_value not in NANO_FORMAT_OPTIONS:
        await call.answer("Недоступный формат", show_alert=True)
        return
    await state.update_data(nano_format=format_value)
    await call.answer(f"Формат: {format_value}")
    try:
        await call.message.edit_text(
            NANO_MODE_TEXT,
            reply_markup=nano_main_settings_keyboard(format_value),
        )
    except Exception:
        try:
            await call.message.edit_reply_markup(reply_markup=nano_main_settings_keyboard(format_value))
        except Exception:
            pass

@router.callback_query(F.data == "set_mode:suno_music")
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

 
@router.callback_query(F.data == "goto:replenish")
async def goto_replenish(
    call: CallbackQuery,
):
    await call.answer()
    await call.message.edit_text(
        text=(
            "🎟️ *Пополнение баланса*\n\n"
            "💰 Держим самые демократичные цены на рынке!\n\n"
            "👇 Выбери удобный способ пополнения:"),
        reply_markup=payments_keyboard(),
    )


@router.callback_query(F.data == "goto:referral")
async def goto_referral(call: CallbackQuery, bot: Bot):
    await call.answer()
    try:
        me = await bot.get_me()
        username = me.username or ""
    except Exception:
        username = ""
    # Build deep link with user id as referral payload
    ref_payload = str(call.from_user.id)
    deep_link = f"https://t.me/{username}?start={ref_payload}" if username else ""
    from urllib.parse import quote_plus
    url_param = quote_plus(deep_link) if deep_link else ""
    share_url = f"https://t.me/share/url?url={url_param}"

    text = (
        "🤝 *Реферальная программа*\n"
        "Хочешь больше токенов? Зови друзей и получай бонусы! 🚀\n\n"
        "*Как это работает:*\n"
        "1️⃣ *Поделись* своей уникальной реферальной ссылкой с другом.\n"
        "2️⃣ Когда он перейдёт по ней и зарегистрируется — ты получаешь *+10 токенов* 💎\n"
        "3️⃣ Если твой друг купит любой пакет токенов — тебе прилетит ещё *+100 токенов* 🎉\n\n"
        "🔥 *Без ограничений!*\n"
        "Чем больше друзей пригласишь — тем больше токенов получишь.\n\n"
        "👇 Копируй ссылку с помощью кнопки под этим сообщением и отправляй друзьям!"
    )
    try:
        await call.message.edit_text(text=text, reply_markup=referral_keyboard(share_url))
    except Exception:
        await call.message.answer(text=text, reply_markup=referral_keyboard(share_url))


@router.callback_query(F.data == "referral:copy")
async def referral_copy(call: CallbackQuery, bot: Bot):
    await call.answer()
    try:
        me = await bot.get_me()
        username = me.username or ""
    except Exception:
        username = ""
    ref_payload = str(call.from_user.id)
    deep_link = f"https://t.me/{username}?start={ref_payload}" if username else ""
    from urllib.parse import quote_plus
    url_param = quote_plus(deep_link) if deep_link else ""
    share_url = f"https://t.me/share/url?url={url_param}"
    link_text = deep_link if deep_link else "Ссылка временно недоступна"
    try:
        await call.message.answer(
            text=f"Ваша реферальная ссылка:\n{link_text}",
            reply_markup=referral_keyboard(share_url),
        )
    except Exception:
        pass


@router.callback_query(F.data == "referral:stats")
@inject
async def referral_stats(
    call: CallbackQuery,
    bot: Bot,
    uow: AbcUnitOfWork = Provide[Container.uow],
):
    await call.answer()
    inviter_tid = call.from_user.id
    total_referred = 0
    total_buyers = 0
    try:
        async with uow:
            # Count total referred users
            stmt_ref = select(func.count()).where(UserOrm.from_ == str(inviter_tid))
            res_ref = await uow.transaction.session.execute(stmt_ref)
            total_referred = int(res_ref.scalar() or 0)

            # Count distinct referred users who made token purchases
            reasons = [
                str(TransactionReasonEnum.purchase_stars),
                str(TransactionReasonEnum.purchase_bepaid),
                str(TransactionReasonEnum.purchase_yookassa),
            ]
            subq = select(UserOrm.id).where(UserOrm.from_ == str(inviter_tid))
            stmt_buy = select(func.count(func.distinct(TransactionOrm.user_id))).where(
                TransactionOrm.user_id.in_(subq),
                TransactionOrm.reason.in_(reasons),
            )
            res_buy = await uow.transaction.session.execute(stmt_buy)
            total_buyers = int(res_buy.scalar() or 0)
    except Exception:
        total_referred = 0
        total_buyers = 0

    # Provide share + copy buttons again
    try:
        me = await bot.get_me()
        username = me.username or ""
    except Exception:
        username = ""
    ref_payload = str(inviter_tid)
    deep_link = f"https://t.me/{username}?start={ref_payload}" if username else ""
    from urllib.parse import quote_plus
    url_param = quote_plus(deep_link) if deep_link else ""
    share_url = f"https://t.me/share/url?url={url_param}"

    text = (
        "📊 Статистика рефералов\n\n"
        f"Пришло по ссылке: *{total_referred}*\n"
        f"Совершили покупку: *{total_buyers}*"
    )
    try:
        await call.message.answer(text=text, reply_markup=referral_keyboard(share_url))
    except Exception:
        pass

@router.callback_query(F.data == "goto:replenish_broadcast")
async def goto_replenish_broadcast(
    call: CallbackQuery,
):
    await call.answer()
    await call.message.answer(
        text=(
            "🎟️ *Пополнение баланса*\n\n"
            "💰 Держим самые демократичные цены на рынке!\n\n"
            "👇 Выбери удобный способ пополнения:"),
        reply_markup=payments_keyboard(),
    )

@router.callback_query(F.data == "pay:ru")
@inject
async def pay_ru(
    call: CallbackQuery,
    settings: AbcSettingsService = Provide[Container.settings_service],
    user_service: AbcUserService = Provide[Container.user_service],
    subscription_service: AbcSubscriptionService = Provide[Container.subscription_service],
):
    user = await user_service.get_user(call.from_user.id)
    sub = await subscription_service.get_active_by_user_id(user.id) if user else None
    await call.answer()
    # Show 100 tokens (99 RUB) only to users who never purchased tokens
    first_time_offer = not (await _has_any_token_purchase(call.from_user.id))
    bundle_token_amounts = ([100] if first_time_offer else []) + [300, 1100, 2400, 3800, 7000]
    bundles: list[tuple[int, int]] = []
    for amount in bundle_token_amounts:
        if amount == 100:
            price = 99
        else:
            price_value = await settings.get_value(f"{amount}_bundle_price")
            try:
                price = int(price_value)
            except Exception:
                price = 0
        bundles.append((amount, price))
    text = (
        "🇷🇺 *SberPay • T‑Pay • ЮMoney*\n\n"
        "💳 Для оплаты но номеру банковской карты используй способ оплаты \"🌍 Картой МИР\".\n\n"
        "🎁 *Гайд* - исчерпывающая инструкция по работе с моделями и составлению промптов.\n\n"
        "Выбери пакет токенов:"
    )
    await call.message.edit_text(
        text=text,
        reply_markup=ru_bundles_keyboard(bundles, has_subscription=bool(sub)),
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
    if tokens == "100":
        price = 99
    else:
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


@router.callback_query(F.data == "pay:card")
@inject
async def pay_card(
    call: CallbackQuery,
    settings: AbcSettingsService = Provide[Container.settings_service],
    user_service: AbcUserService = Provide[Container.user_service],
    subscription_service: AbcSubscriptionService = Provide[Container.subscription_service],
):
    user = await user_service.get_user(call.from_user.id)
    sub = await subscription_service.get_active_by_user_id(user.id) if user else None
    await call.answer()
    # Show 100 tokens (99 RUB) only to users who never purchased tokens
    first_time_offer = not (await _has_any_token_purchase(call.from_user.id))
    bundle_token_amounts = ([100] if first_time_offer else []) + [300, 1100, 2400, 3800, 7000]
    bundles: list[tuple[int, int]] = []
    for amount in bundle_token_amounts:
        if amount == 100:
            price = 99
        else:
            price_value = await settings.get_value(f"{amount}_bundle_price")
            try:
                price = int(price_value)
            except Exception:
                price = 0
        bundles.append((amount, price))
    text = (
        "🌍 *Картой МИР*\n\n"
        "Оплата картой МИР.\n\n"
        "🎁 *Гайд* - исчерпывающая инструкция по работе с моделями и составлению промптов.\n\n"
        "Выбери пакет токенов:"
    )
    await call.message.edit_text(
        text=text,
        reply_markup=card_bundles_keyboard(bundles, has_subscription=bool(sub)),
    )


@router.callback_query(F.data.startswith("pay:card:"))
@inject
async def pay_card_bundle_selected(
    call: CallbackQuery,
    settings: AbcSettingsService = Provide[Container.settings_service],
    payments: AbcPaymentsService = Provide[Container.payments_service],
):
    await call.answer()
    parts = (call.data or "").split(":", maxsplit=2)
    tokens = parts[-1] if parts and len(parts) >= 3 else ""
    if tokens == "100":
        price = 99
    else:
        price_value = await settings.get_value(f"{tokens}_bundle_price")
        try:
            price = int(price_value)
        except Exception:
            price = 0
    try:
        confirm_url = await payments.create_card_payment(user_id=call.from_user.id, tokens=int(tokens), price_rub=price)
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
    user_service: AbcUserService = Provide[Container.user_service],
    subscription_service: AbcSubscriptionService = Provide[Container.subscription_service],
):
    user = await user_service.get_user(call.from_user.id)
    sub = await subscription_service.get_active_by_user_id(user.id) if user else None
    await call.answer()
    text = (
        "⭐ *Оплата звёздами*\n\n"
        "🎁 *Гайд* - исчерпывающая инструкция по работе с моделями и составлению промптов.\n\n"
        "Выбери пакет токенов:"
    )
    first_time_offer = not (await _has_any_token_purchase(call.from_user.id))
    await call.message.edit_text(
        text=text,
        reply_markup=await stars_bundles_keyboard(settings, has_subscription=bool(sub), first_time_offer=first_time_offer),
    )


@router.callback_query(F.data == "pay:card_byn")
@inject
async def pay_card_byn(
    call: CallbackQuery,
    settings: AbcSettingsService = Provide[Container.settings_service],
    user_service: AbcUserService = Provide[Container.user_service],
    subscription_service: AbcSubscriptionService = Provide[Container.subscription_service],
):
    user = await user_service.get_user(call.from_user.id)
    sub = await subscription_service.get_active_by_user_id(user.id) if user else None
    await call.answer()
    first_time_offer = not (await _has_any_token_purchase(call.from_user.id))
    bundle_token_amounts = ([100] if first_time_offer else []) + [300, 1100, 2400, 3800, 7000]
    bundles: list[tuple[int, int]] = []
    for amount in bundle_token_amounts:
        if amount == 100:
            byn = 3.40
        else:
            price_value = await settings.get_value(f"{amount}_byn_bundle_price")
            try:
                byn = int(price_value)
            except Exception:
                byn = 0
        bundles.append((amount, byn))
    rate_value = await settings.get_value("byn-usd")
    try:
        usd_rate = float(rate_value) if rate_value is not None else 2.97
    except Exception:
        usd_rate = 2.97
    text = (
        "🚀 *Visa и Mastercard*\n\n"
        "Оплата картами VISA/Mastercard.\n\n"
        "🎁 *Гайд* - исчерпывающая инструкция по работе с моделями и составлению промптов.\n\n"
        "Выбери пакет токенов:"
    )
    await call.message.edit_text(
        text=text,
        reply_markup=card_byn_bundles_keyboard(bundles, usd_rate, has_subscription=bool(sub)),
    )


@router.callback_query(F.data.startswith("pay:card_byn:"))
@inject
async def pay_card_byn_bundle_selected(
    call: CallbackQuery,
    settings: AbcSettingsService = Provide[Container.settings_service],
    payments: AbcPaymentsService = Provide[Container.payments_service],
):
    await call.answer()
    parts = (call.data or "").split(":", maxsplit=2)
    tokens = parts[-1] if parts and len(parts) >= 3 else ""
    rate_value = await settings.get_value("byn-usd")
    if tokens == "100":
        byn = 3.40
    else:
        price_value = await settings.get_value(f"{tokens}_byn_bundle_price")
        try:
            byn = int(price_value)
        except Exception:
            byn = 0
    try:
        usd_rate = float(rate_value) if rate_value is not None else 2.97
    except Exception:
        usd_rate = 2.97
    try:
        confirm_url = await payments.create_card_payment_byn(user_id=call.from_user.id, tokens=int(tokens), price_byn=byn)
        approx_usd = byn / usd_rate if usd_rate else 0
        await call.message.edit_text(
            text=(
                f"✅ *Сумма заказа*: {tokens} токенов — {byn} BYN"
                + (f" (~${approx_usd:.2f})" if approx_usd > 0 else "")
                + "\n\nНажми кнопку, чтобы перейти к оплате."),
            reply_markup=pay_link_keyboard(confirm_url),
        )
    except Exception:
        await call.message.edit_text(
            text=(
                "⚠️ Не получилось создать ссылку на оплату. Попробуй позже."),
            reply_markup=ru_bundles_back_keyboard(),
        )


@router.callback_query(F.data.startswith("pay:stars:"))
async def pay_stars_bundle_selected(
    call: CallbackQuery,
):
    await call.answer()
    parts = (call.data or "").split(":", maxsplit=3)
    total_tokens = parts[-2] if len(parts) >= 4 else ""
    stars = parts[-1] if len(parts) >= 4 else ""
    try:
        tokens_int = int(total_tokens)
        stars_int = int(stars)
    except Exception:
        await call.message.edit_text(
            text="Некорректные данные пакета.",
            reply_markup=payments_back_keyboard(),
        )
        return
    if tokens_int <= 0 or stars_int <= 0:
        await call.message.edit_text(
            text="Некорректные данные пакета.",
            reply_markup=payments_back_keyboard(),
        )
        return

    payload = f"stars:{tokens_int}:{stars_int}"

    try:
        await call.bot.send_invoice(
            chat_id=call.from_user.id,
            title=f"Покупка {tokens_int} токенов",
            description=f"Зачисление {tokens_int} токенов на баланс бота.",
            payload=payload,
            provider_token="",  # Not needed for stars
            currency="XTR",
            prices=[LabeledPrice(label=f"{tokens_int} Токенов", amount=stars_int)],
            max_tip_amount=None,
            suggested_tip_amounts=None,
            protect_content=False,
            need_email=False,
            need_name=False,
            need_phone_number=False,
            need_shipping_address=False,
            send_email_to_provider=False,
            send_phone_number_to_provider=False,
            is_flexible=False,
        )
    except Exception as e:
        await call.message.edit_text(
            text=f"Ошибка при создании платежа: {str(e)}",
            reply_markup=payments_back_keyboard(),
        )

@router.pre_checkout_query()
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
    admin_bot: Bot = Provide[Container.admin_bot],
    settings: AbcSettingsService = Provide[Container.settings_service],
    uow: AbcUnitOfWork = Provide[Container.uow],
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
    # Parse stars spent value if present
    try:
        stars_used = int(parts[2]) if len(parts) >= 3 else None
    except Exception:
        stars_used = None
    if tokens <= 0:
        return
    try:
        updated_user = await user_service.add_tokens_by_telegram_id(
            telegram_id=message.from_user.id,
            amount=tokens,
            reason=TransactionReasonEnum.purchase_stars,
        )
        # Award referral purchase bonus (+100) to inviter, once per referred user
        try:
            user = await user_service.get_user(message.from_user.id)
            ref_raw = getattr(user, 'from_', None) if user else None
            inviter_tid = int(ref_raw) if ref_raw else None
        except Exception:
            inviter_tid = None
        if inviter_tid and inviter_tid != message.from_user.id:
            try:
                async with uow:
                    inviter = await uow.user.get_by_telegram_id(inviter_tid)
                    if inviter:
                        meta_tag = f"referred:{message.from_user.id}"
                        stmt = (
                            select(TransactionOrm.id)
                            .where(
                                TransactionOrm.user_id == inviter.id,
                                TransactionOrm.reason == str(TransactionReasonEnum.referral_purchase_bonus),
                                TransactionOrm.meta == meta_tag,
                            )
                            .limit(1)
                        )
                        res = await uow.transaction.session.execute(stmt)
                        if res.first() is None:
                            updated = await uow.user.update_balance_by_user_id(inviter.id, 100)
                            if updated:
                                await uow.transaction.add(
                                    TransactionEntity(
                                        user_id=inviter.id,
                                        delta=100,
                                        reason=TransactionReasonEnum.referral_purchase_bonus,
                                        meta=meta_tag,
                                    )
                                )
                                try:
                                    uname = getattr(user, 'username', None)
                                    suffix = f" за пользователя {uname}" if uname else ""
                                    note = (
                                        f"🎉 Поздравляем, ты получил реферальный бонус{suffix}: 100 токенов!\n\n"
                                        "🎞️ Копи бонусные токены или выбирай модель и твори!"
                                    )
                                    await message.bot.send_message(inviter_tid, note, reply_markup=referral_bonus_keyboard(), parse_mode=None)
                                except Exception:
                                    pass
            except Exception:
                pass
        balance = updated_user.balance if updated_user else None
        balance_text = f"*{balance}*" if balance is not None else "обновлён"
        if tokens in (1100, 2400, 3800, 7000):
            special_text = (
                "🎉 Спасибо за покупку!\n\n"
                "Вы получили:\n"
                f"🛸 {tokens} токенов — ваш личный запас для общения с ИИ\n"
                "🎁 Гайд по использованию — пошаговое руководство, как извлечь максимум из возможностей нашего бота.\n\n"
                "В гайде вы найдёте:\n"
                "✨ как правильно формулировать запросы,\n"
                "⚙️ примеры эффективных промтов,\n"
                "💡 способы ускорить и улучшить ответы ИИ,\n"
                "🚀 идеи для реальных задач — от работы до творчества.\n\n"
                "Приятного изучения и продуктивного общения с ИИ!"
            )
            await message.answer(
                special_text,
                reply_markup=start_keyboard(BotModeEnum.passive),
                parse_mode=None,
            )
            try:
                guide_path = (
                    Path(__file__).resolve().parents[3] / "media" / "files" / "guide.pdf"
                )
                await message.answer_document(document=FSInputFile(guide_path.as_posix()))
            except Exception:
                pass
        else:
            await message.answer(
            text=(
                f"✅ Оплата прошла успешно! Зачислено {tokens} токенов.\n\n"
                f"🪙 Твой баланс: {balance_text} токенов\n\n"
                "👇 Что хочешь сделать?"
            ),
            reply_markup=start_keyboard(BotModeEnum.passive),
        )
        try:
            admins = await user_service.list_admins()
            uname = message.from_user.username if message.from_user.username else None
            username = f"@{uname}" if uname else "—"
            try:
                _raw = await settings.get_value(f"{tokens}_stars_price")
                _price_val = int(_raw) if _raw is not None else None
            except Exception:
                _price_val = None
            amount_text = f"{_price_val} XTR" if isinstance(_price_val, int) and _price_val > 0 else "-"
            admin_text = (
                "🎉 Поступила оплата!\n\n"
                f"👤 Пользователь: {username} ({message.from_user.id})\n"
                f"📦 Количество токенов: {tokens}\n"
                f"💳 Способ оплаты: Stars\n\n"
                f"💵 Сумма: {amount_text}"
            )
            for admin in admins:
                try:
                    await admin_bot.send_message(admin.telegram_id, admin_text, parse_mode=None)
                except Exception:
                    pass
        except Exception:
            pass
    except Exception:
        await message.answer(
            text=(
                f"⚠️ Оплата прошла, но есть проблемы с начислением. Обратитесь в @{settings.SUPPORT_USERNAME}."
            ),
            reply_markup=start_keyboard(BotModeEnum.passive),
        )


@router.callback_query(F.data == "goto:start")
@inject
async def goto_start(
    call: CallbackQuery,
    state: FSMContext,
    service: AbcUserService = Provide[Container.user_service],
    settings: AbcSettingsService = Provide[Container.settings_service],
    subscription_service: AbcSubscriptionService = Provide[Container.subscription_service],
):
    await call.answer()

    await state.update_data(history=[])
    user, _ = await service.is_user_new(call.from_user)
    current_mode = (await state.get_data()).get('mode', BotModeEnum.passive)
    daily_bonus = await settings.get_value("daily_bonus")
    text = (
        f"👋 Привет, *{call.from_user.first_name}*!\n\n"
        f"🪙 Твой баланс: *{user.balance}* токенов\n"
    )
    try:
        user_balance_int = int(user.balance)
    except Exception:
        user_balance_int = 0
    if False:
        text += f"⚡ Ежедневно: до *{daily_bonus}* токенов\n\n"
    else:
        text += "\n"
    text += f"🤖 Текущий ИИ: *{current_mode}*\n"

    if current_mode != BotModeEnum.passive:
        price = await settings.get_value(settings_models_mapper[current_mode])
        try:
            if current_mode in (BotModeEnum.gpt, BotModeEnum.gpt_mini):
                sub_active = await subscription_service.get_active_by_user_id(user.id)
                if sub_active:
                    price = "0"
        except Exception:
            pass
        text += f"💸 Цена запроса: *{price} токенов*\n\n"
    else:
        text += "\n"

    text += "👇 Что хочешь сделать?"
    kb = start_keyboard(current_mode)

    await call.message.edit_text(
        text=text,
        reply_markup=kb,
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
    nano_price = await settings.get_value(settings_models_mapper[BotModeEnum.nano_banana])
    suno_price = await settings.get_value(settings_models_mapper[BotModeEnum.suno_music])
    sora_price = await settings.get_value(settings_models_mapper[BotModeEnum.sora2_video])
    sora_pro_price = await settings.get_value(settings_models_mapper[BotModeEnum.sora2_pro_video])

    text = (
        "👾 *Выбор ИИ*\n\n"
        f"🤖 *GPT‑5.1* | *{gpt_price}* токенов\n"
        "Самый продвинутый ИИ-чат.\n\n"
        f"⚡ *GPT‑5 Mini* | *{mini_price}* токен\n"
        "Быстрые и экономные ответы.\n\n"
        f"🏞️ *Nano Banana* | *{nano_price}* токенов\n"
        "Создание и редактирование изображений.\n\n"
        f"🎵 *Suno* | *{suno_price}* токенов\n"
        "Генерация музыки по стилю, описанию/тексту.\n\n"
        f"📹 *Sora 2* и *Veo 3.1* | *{sora_price}* токенов\n"
        "Генерация видео по тексту или картинке.\n\n"
        f"🎥 *Sora 2 Pro* | *{sora_pro_price}* токенов\n"
        "Лучшая модель генерации видео из существующих.\n\n"
        "🪙 _Цена указана за 1 запрос к модели_\n\n"
        "👇 Выбери нужный ИИ:"
    )

    await call.message.edit_text(
        text=text,
        reply_markup=mode_keyboard(current_mode)
    )
    await call.answer("Выбери режим работы")
