from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from dependency_injector.wiring import Provide, inject

from bot.container import Container
from bot.enums import BotModeEnum
from bot.keyboards.suno import (
    suno_main_menu,
    suno_generate_keyboard,
    suno_model_keyboard,
    suno_instrumental_keyboard,
    suno_vocals_keyboard,
    suno_lyrics_keyboard,
    suno_separation_keyboard,
    suno_extend_keyboard,
)

router = Router()


def _get_suno_state(data: dict) -> dict:
    default = {
        "model": "V3_5",
        "customMode": False,
        "instrumental": True,
        "sep_type": "separate_vocal",
    }
    raw = data.get("suno") or {}
    return {**default, **raw}


@router.callback_query(F.data == "set_mode:suno")
@inject
async def set_mode_suno(call: CallbackQuery, state: FSMContext):
    await state.update_data(mode=BotModeEnum.suno, suno=_get_suno_state(await state.get_data()))
    await call.answer("Режим Suno активирован")
    await call.message.edit_text(
        "🎵 Suno — генерация и обработка музыки. Выбери действие:",
        reply_markup=suno_main_menu(),
    )


@router.callback_query(F.data == "suno:menu")
@inject
async def suno_menu(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_text("🎵 Выбери действие:", reply_markup=suno_main_menu())


@router.callback_query(F.data.startswith("suno:action:"))
@inject
async def suno_action(call: CallbackQuery, state: FSMContext):
    await call.answer()
    action = (call.data or "").split(":", maxsplit=2)[-1]
    data = await state.get_data()
    suno = _get_suno_state(data)
    await state.update_data(suno=suno, suno_flow=action)

    if action == "generate":
        await call.message.edit_text(
            "✨ Режим генерации музыки. Настрой параметры или сразу введи промпт.",
            reply_markup=suno_generate_keyboard(suno.get("customMode", False), suno.get("instrumental", True), suno.get("model", "V3_5")),
        )
    elif action == "instrumental":
        await call.message.edit_text(
            "🎶 Добавь инструментал к своему аудио. Заполни поля и загрузись аудио.",
            reply_markup=suno_instrumental_keyboard(),
        )
    elif action == "vocals":
        await call.message.edit_text(
            "🎤 Добавим вокал к твоему треку. Укажи промпт/стиль/заголовок и аудио.",
            reply_markup=suno_vocals_keyboard(),
        )
    elif action == "lyrics":
        await call.message.edit_text(
            "📜 Сгенерирую текст песни. Введи описание темы.",
            reply_markup=suno_lyrics_keyboard(),
        )
    elif action == "separate":
        await call.message.edit_text(
            "🧽 Разделение вокала/инструмента или STEM.",
            reply_markup=suno_separation_keyboard(suno.get("sep_type", "separate_vocal")),
        )
    elif action == "extend":
        await call.message.edit_text(
            "➕ Продление трека. Вставь audioId из предыдущей генерации.",
            reply_markup=suno_extend_keyboard(),
        )


@router.callback_query(F.data == "suno:gen:model")
@inject
async def suno_gen_choose_model(call: CallbackQuery, state: FSMContext):
    await call.answer()
    suno = _get_suno_state(await state.get_data())
    await call.message.edit_reply_markup(reply_markup=suno_model_keyboard(suno.get("model", "V3_5")))


@router.callback_query(F.data.startswith("suno:gen:model:"))
@inject
async def suno_gen_set_model(call: CallbackQuery, state: FSMContext):
    await call.answer("Модель обновлена")
    model = (call.data or "").split(":")[-1]
    data = await state.get_data()
    suno = _get_suno_state(data)
    suno["model"] = model
    await state.update_data(suno=suno)
    await call.message.edit_reply_markup(reply_markup=suno_generate_keyboard(suno.get("customMode", False), suno.get("instrumental", True), model))


@router.callback_query(F.data == "suno:gen:back")
@inject
async def suno_gen_back(call: CallbackQuery, state: FSMContext):
    await call.answer()
    suno = _get_suno_state(await state.get_data())
    await call.message.edit_reply_markup(reply_markup=suno_generate_keyboard(suno.get("customMode", False), suno.get("instrumental", True), suno.get("model", "V3_5")))


@router.callback_query(F.data == "suno:gen:custom")
@inject
async def suno_gen_toggle_custom(call: CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    suno = _get_suno_state(data)
    suno["customMode"] = not bool(suno.get("customMode", False))
    await state.update_data(suno=suno)
    await call.message.edit_reply_markup(reply_markup=suno_generate_keyboard(suno.get("customMode", False), suno.get("instrumental", True), suno.get("model", "V3_5")))


@router.callback_query(F.data == "suno:gen:instrumental")
@inject
async def suno_gen_toggle_instrumental(call: CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    suno = _get_suno_state(data)
    suno["instrumental"] = not bool(suno.get("instrumental", True))
    await state.update_data(suno=suno)
    await call.message.edit_reply_markup(reply_markup=suno_generate_keyboard(suno.get("customMode", False), suno.get("instrumental", True), suno.get("model", "V3_5")))


@router.callback_query(F.data.in_({
    "suno:gen:set:style",
    "suno:gen:set:title",
    "suno:gen:set:negative",
    "suno:gen:set:prompt",
}))
@inject
async def suno_gen_set_inputs(call: CallbackQuery, state: FSMContext):
    await call.answer()
    mapping = {
        "suno:gen:set:style": ("awaiting_gen_style", "✏️ Введи стиль (например: Folk, Acoustic)"),
        "suno:gen:set:title": ("awaiting_gen_title", "🧾 Введи заголовок трека"),
        "suno:gen:set:negative": ("awaiting_gen_negative", "🚫 Введи негатив‑теги через запятую"),
        "suno:gen:set:prompt": ("awaiting_gen_prompt", "📨 Введи промпт для музыки"),
    }
    stage, text = mapping.get(call.data)
    await state.update_data(suno_stage=stage)
    await call.message.answer(text)


@router.callback_query(F.data.in_({
    "suno:ins:set:audio",
    "suno:ins:set:title",
    "suno:ins:set:tags",
    "suno:ins:set:negative",
}))
@inject
async def suno_ins_set_inputs(call: CallbackQuery, state: FSMContext):
    await call.answer()
    mapping = {
        "suno:ins:set:audio": ("awaiting_ins_audio", "📤 Пришли аудио‑файл (mp3/wav/voice)"),
        "suno:ins:set:title": ("awaiting_ins_title", "🧾 Введи заголовок"),
        "suno:ins:set:tags": ("awaiting_ins_tags", "🏷️ Введи теги (жанр/настроение) через запятую"),
        "suno:ins:set:negative": ("awaiting_ins_negative", "🚫 Введи негатив‑теги через запятую"),
    }
    stage, text = mapping.get(call.data)
    await state.update_data(suno_stage=stage)
    await call.message.answer(text)


@router.callback_query(F.data == "suno:ins:submit")
@inject
async def suno_ins_submit(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.update_data(suno_stage="submit_ins")
    await call.message.answer("Отправь любое сообщение, чтобы запустить задачу (или загрузи аудио, если не загрузил).")


@router.callback_query(F.data.in_({
    "suno:voc:set:audio",
    "suno:voc:set:prompt",
    "suno:voc:set:title",
    "suno:voc:set:style",
    "suno:voc:set:negative",
    "suno:voc:set:gender",
}))
@inject
async def suno_voc_inputs(call: CallbackQuery, state: FSMContext):
    await call.answer()
    mapping = {
        "suno:voc:set:audio": ("awaiting_voc_audio", "📤 Пришли аудио‑файл (инструментал)"),
        "suno:voc:set:prompt": ("awaiting_voc_prompt", "📨 Введи промпт/идею вокала"),
        "suno:voc:set:title": ("awaiting_voc_title", "🧾 Введи заголовок"),
        "suno:voc:set:style": ("awaiting_voc_style", "🎼 Введи стиль"),
        "suno:voc:set:negative": ("awaiting_voc_negative", "🚫 Введи негатив‑теги через запятую"),
        "suno:voc:set:gender": ("toggle_voc_gender", "🗣️ Пол голоса переключён (m/f)"),
    }
    stage, text = mapping.get(call.data)
    if stage == "toggle_voc_gender":
        data = await state.get_data()
        suno = _get_suno_state(data)
        suno["vocalGender"] = "f" if suno.get("vocalGender") == "m" else "m"
        await state.update_data(suno=suno)
        await call.message.answer(text)
    else:
        await state.update_data(suno_stage=stage)
        await call.message.answer(text)


@router.callback_query(F.data == "suno:voc:submit")
@inject
async def suno_voc_submit(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.update_data(suno_stage="submit_voc")
    await call.message.answer("Отправь любое сообщение, чтобы запустить задачу (или прикрепи аудио/текст, если не указал).")


@router.callback_query(F.data == "suno:lyr:set:prompt")
@inject
async def suno_lyrics_set_prompt(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.update_data(suno_stage="awaiting_lyrics_prompt")
    await call.message.answer("📨 Опиши тему и настроение песни.")


@router.callback_query(F.data == "suno:sep:toggle:type")
@inject
async def suno_sep_toggle_type(call: CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    suno = _get_suno_state(data)
    suno["sep_type"] = "split_stem" if suno.get("sep_type") == "separate_vocal" else "separate_vocal"
    await state.update_data(suno=suno)
    await call.message.edit_reply_markup(reply_markup=suno_separation_keyboard(suno["sep_type"]))


@router.callback_query(F.data.in_({"suno:sep:set:task", "suno:sep:set:audio"}))
@inject
async def suno_sep_set_ids(call: CallbackQuery, state: FSMContext):
    await call.answer()
    if call.data == "suno:sep:set:task":
        await state.update_data(suno_stage="awaiting_sep_task")
        await call.message.answer("🆔 Введи taskId (из генерации трека)")
    else:
        await state.update_data(suno_stage="awaiting_sep_audio")
        await call.message.answer("🎵 Введи audioId (из генерации трека)")


@router.callback_query(F.data == "suno:sep:submit")
@inject
async def suno_sep_submit(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.update_data(suno_stage="submit_sep")
    await call.message.answer("Отправь любое сообщение, чтобы запустить разделение.")


@router.callback_query(F.data.in_({"suno:ext:set:audio"}))
@inject
async def suno_ext_set_audio(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.update_data(suno_stage="awaiting_ext_audio")
    await call.message.answer("🆔 Вставь audioId трека для продления")


@router.callback_query(F.data == "suno:ext:submit")
@inject
async def suno_ext_submit(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.update_data(suno_stage="submit_ext")
    await call.message.answer("Отправь любое сообщение с audioId для запуска продления.")


