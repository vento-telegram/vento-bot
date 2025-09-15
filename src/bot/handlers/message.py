import logging

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from dependency_injector.wiring import inject, Provide

from bot.container import Container
from bot.enums import BotModeEnum
from bot.errors import OpenAIBadRequestError, InsufficientBalanceError
from bot.interfaces.services.gpt import AbcOpenAIService
from bot.interfaces.services.suno import AbcSunoService
from bot.interfaces.services.user import AbcUserService
from bot.keyboards.change_ai import mode_keyboard
from bot.utils.telegram_format import prepare_telegram_messages_from_markdown

logger = logging.getLogger(__name__)

router = Router()

@router.message()
@inject
async def common_message_handler(
    message: Message,
    state: FSMContext,
    openai_service: AbcOpenAIService = Provide[Container.openai_service],
    user_service: AbcUserService = Provide[Container.user_service],
    suno_service: AbcSunoService = Provide[Container.suno_service],
):
    state_data = await state.get_data()
    mode = state_data.get("mode")
    user = await user_service.get_user(message.from_user.id)

    if user.is_blocked:
        await message.answer("🚫 Ваш аккаунт заблокирован. Обратитесь в поддержку.")
        return

    if mode == BotModeEnum.gpt or mode == BotModeEnum.gpt_mini:
        status_msg = await message.answer("✨ *Готовлю ответ...*")
        try:
            response = await openai_service.process_gpt_request(message, state, user)
            parts = prepare_telegram_messages_from_markdown(response.text or "")
            if parts:
                await status_msg.edit_text(parts[0])
                for extra in parts[1:]:
                    await message.answer(extra)
        except InsufficientBalanceError:
            await status_msg.edit_text(
                "*☹️ Недостаточно токенов*\n\nТы можешь пополнить баланс токенов, оформить подписку на модель или выбрать более экономичную модель.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="goto:account"),
                            InlineKeyboardButton(text="👾 Сменить модель", callback_data="goto:replenish"),
                        ]
                    ]
                ),
            )
        except OpenAIBadRequestError:
            await status_msg.edit_text("*☹️ OpenAI отклонил твой запрос*\n\nПожалуйста, попробуй изменить его.")

    elif mode == BotModeEnum.gpt_image:
        try:
            await openai_service.submit_gpt_image_request(message, state, user)
        except InsufficientBalanceError:
            await message.answer(
                "*☹️ Недостаточно токенов*\n\nДля генерации изображения пополни баланс или выбери другую модель.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="goto:account"),
                            InlineKeyboardButton(text="👾 Сменить модель", callback_data="goto:replenish"),
                        ]
                    ]
                ),
            )

    elif mode == BotModeEnum.nano_banana:
        try:
            await openai_service.submit_nano_banana_request(message, state, user)
        except InsufficientBalanceError:
            await message.answer(
                "*☹️ Недостаточно токенов*\n\nПополните баланс или выберите другую модель.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="goto:account"),
                            InlineKeyboardButton(text="👾 Сменить модель", callback_data="goto:replenish"),
                        ]
                    ]
                ),
            )

    elif mode == BotModeEnum.suno:
        # Route by current stage (set via callbacks)
        state_data = await state.get_data()
        stage = state_data.get("suno_stage")
        flow = state_data.get("suno_flow")
        suno = state_data.get("suno", {}) or {}

        try:
            if stage == "awaiting_gen_style":
                suno["style"] = (message.text or "").strip()
                await state.update_data(suno=suno, suno_stage=None)
                await message.answer("✅ Стиль установлен")
            elif stage == "awaiting_gen_title":
                suno["title"] = (message.text or "").strip()
                await state.update_data(suno=suno, suno_stage=None)
                await message.answer("✅ Заголовок установлен")
            elif stage == "awaiting_gen_negative":
                suno["negativeTags"] = (message.text or "").strip()
                await state.update_data(suno=suno, suno_stage=None)
                await message.answer("✅ Негатив‑теги установлены")
            elif stage == "awaiting_gen_prompt":
                await state.update_data(suno_stage=None)
                await suno_service.submit_generate_music(message, state, user)

            elif stage == "awaiting_ins_audio":
                # Audio URL will be extracted by service if possible
                await state.update_data(suno_stage=None)
                await suno_service.submit_add_instrumental(message, state, user)
            elif stage == "awaiting_ins_title":
                suno["title"] = (message.text or "").strip()
                await state.update_data(suno=suno, suno_stage=None)
                await message.answer("✅ Заголовок установлен")
            elif stage == "awaiting_ins_tags":
                suno["tags"] = (message.text or "").strip()
                await state.update_data(suno=suno, suno_stage=None)
                await message.answer("✅ Теги установлены")
            elif stage == "awaiting_ins_negative":
                suno["negativeTags"] = (message.text or "").strip()
                await state.update_data(suno=suno, suno_stage=None)
                await message.answer("✅ Негатив‑теги установлены")
            elif stage == "submit_ins":
                await state.update_data(suno_stage=None)
                await suno_service.submit_add_instrumental(message, state, user)

            elif stage == "awaiting_voc_audio":
                await state.update_data(suno_stage=None)
                await suno_service.submit_add_vocals(message, state, user)
            elif stage == "awaiting_voc_prompt":
                suno["prompt"] = (message.text or "").strip()
                await state.update_data(suno=suno, suno_stage=None)
                await message.answer("✅ Промпт установлен")
            elif stage == "awaiting_voc_title":
                suno["title"] = (message.text or "").strip()
                await state.update_data(suno=suno, suno_stage=None)
                await message.answer("✅ Заголовок установлен")
            elif stage == "awaiting_voc_style":
                suno["style"] = (message.text or "").strip()
                await state.update_data(suno=suno, suno_stage=None)
                await message.answer("✅ Стиль установлен")
            elif stage == "awaiting_voc_negative":
                suno["negativeTags"] = (message.text or "").strip()
                await state.update_data(suno=suno, suno_stage=None)
                await message.answer("✅ Негатив‑теги установлены")
            elif stage == "submit_voc":
                await state.update_data(suno_stage=None)
                await suno_service.submit_add_vocals(message, state, user)

            elif stage == "awaiting_lyrics_prompt":
                await state.update_data(suno_stage=None)
                await suno_service.submit_generate_lyrics(message, state, user)

            elif stage == "awaiting_sep_task":
                suno["sep_taskId"] = (message.text or "").strip()
                await state.update_data(suno=suno, suno_stage=None)
                await message.answer("✅ taskId установлен")
            elif stage == "awaiting_sep_audio":
                suno["sep_audioId"] = (message.text or "").strip()
                await state.update_data(suno=suno, suno_stage=None)
                await message.answer("✅ audioId установлен")
            elif stage == "submit_sep":
                await state.update_data(suno_stage=None)
                await suno_service.submit_vocal_separation(message, state, user)

            elif stage == "awaiting_ext_audio":
                # For simplicity, take text as audioId
                await state.update_data(suno_stage=None)
                await suno_service.submit_extend_music(message, state, user)
            elif stage == "submit_ext":
                await state.update_data(suno_stage=None)
                await suno_service.submit_extend_music(message, state, user)
            else:
                # Default by flow without explicit stage
                if flow == "generate":
                    await suno_service.submit_generate_music(message, state, user)
                elif flow == "lyrics":
                    await suno_service.submit_generate_lyrics(message, state, user)
                elif flow == "instrumental":
                    await suno_service.submit_add_instrumental(message, state, user)
                elif flow == "vocals":
                    await suno_service.submit_add_vocals(message, state, user)
                elif flow == "separate":
                    await suno_service.submit_vocal_separation(message, state, user)
                elif flow == "extend":
                    await suno_service.submit_extend_music(message, state, user)
        except InsufficientBalanceError:
            await message.answer(
                "*☹️ Недостаточно токенов*\n\nПополните баланс или выберите другую модель.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="goto:account")]]
                ),
            )

    elif mode == BotModeEnum.passive or not mode:
        await message.answer(
            "👇 Сначала выбери, куда будем делать запрос:",
            reply_markup=mode_keyboard(BotModeEnum.passive),
        )
