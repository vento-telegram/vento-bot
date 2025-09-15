from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def suno_main_menu() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text="✨ Сгенерировать музыку", callback_data="suno:action:generate")],
        [InlineKeyboardButton(text="➕ Продлить трек", callback_data="suno:action:extend")],
        [InlineKeyboardButton(text="🎶 Добавить инструментал", callback_data="suno:action:instrumental")],
        [InlineKeyboardButton(text="🎤 Добавить вокал", callback_data="suno:action:vocals")],
        [InlineKeyboardButton(text="📜 Генерация текста песни", callback_data="suno:action:lyrics")],
        [InlineKeyboardButton(text="🧽 Удалить вокал / Stems", callback_data="suno:action:separate")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="goto:start")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def suno_generate_keyboard(custom: bool, instrumental: bool, model: str) -> InlineKeyboardMarkup:
    def _bool_label(flag: bool) -> str:
        return "✅" if flag else "✳️"

    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text=f"Модель: {model}", callback_data="suno:gen:model")],
        [InlineKeyboardButton(text=f"Режим: {'Custom' if custom else 'Simple'}", callback_data="suno:gen:custom")],
        [InlineKeyboardButton(text=f"Вокал: {'нет' if instrumental else 'да'}", callback_data="suno:gen:instrumental")],
        [InlineKeyboardButton(text="✏️ Стиль", callback_data="suno:gen:set:style"), InlineKeyboardButton(text="🧾 Заголовок", callback_data="suno:gen:set:title")],
        [InlineKeyboardButton(text="🚫 Негатив‑теги", callback_data="suno:gen:set:negative")],
        [InlineKeyboardButton(text="📨 Ввести промпт", callback_data="suno:gen:set:prompt")],
        [InlineKeyboardButton(text="🔙 В меню Suno", callback_data="suno:menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def suno_model_keyboard(current: str) -> InlineKeyboardMarkup:
    models = ["V3_5", "V4", "V4_5", "V4_5PLUS"]
    buttons: list[InlineKeyboardButton] = []
    for m in models:
        label = f"✅ {m}" if m == current else m
        buttons.append(InlineKeyboardButton(text=label, callback_data=f"suno:gen:model:{m}"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons, [InlineKeyboardButton(text="⬅️ Назад", callback_data="suno:gen:back")]])


def suno_instrumental_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="📤 Загрузить аудио", callback_data="suno:ins:set:audio")],
        [InlineKeyboardButton(text="🧾 Заголовок", callback_data="suno:ins:set:title")],
        [InlineKeyboardButton(text="🏷️ Теги", callback_data="suno:ins:set:tags"), InlineKeyboardButton(text="🚫 Негатив‑теги", callback_data="suno:ins:set:negative")],
        [InlineKeyboardButton(text="✅ Запустить", callback_data="suno:ins:submit")],
        [InlineKeyboardButton(text="🔙 В меню Suno", callback_data="suno:menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def suno_vocals_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="📤 Загрузить аудио", callback_data="suno:voc:set:audio")],
        [InlineKeyboardButton(text="📨 Промпт", callback_data="suno:voc:set:prompt")],
        [InlineKeyboardButton(text="🧾 Заголовок", callback_data="suno:voc:set:title")],
        [InlineKeyboardButton(text="🎼 Стиль", callback_data="suno:voc:set:style"), InlineKeyboardButton(text="🚫 Негатив‑теги", callback_data="suno:voc:set:negative")],
        [InlineKeyboardButton(text="🗣️ Голос: m/f", callback_data="suno:voc:set:gender")],
        [InlineKeyboardButton(text="✅ Запустить", callback_data="suno:voc:submit")],
        [InlineKeyboardButton(text="🔙 В меню Suno", callback_data="suno:menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def suno_lyrics_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="📨 Ввести описание", callback_data="suno:lyr:set:prompt")],
        [InlineKeyboardButton(text="🔙 В меню Suno", callback_data="suno:menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def suno_separation_keyboard(sep_type: str) -> InlineKeyboardMarkup:
    type_label = "Vocals vs Instrumental" if sep_type == "separate_vocal" else "Split Stems"
    rows = [
        [InlineKeyboardButton(text=f"Тип: {type_label}", callback_data="suno:sep:toggle:type")],
        [InlineKeyboardButton(text="🆔 Ввести taskId", callback_data="suno:sep:set:task")],
        [InlineKeyboardButton(text="🎵 Ввести audioId", callback_data="suno:sep:set:audio")],
        [InlineKeyboardButton(text="✅ Запустить", callback_data="suno:sep:submit")],
        [InlineKeyboardButton(text="🔙 В меню Suno", callback_data="suno:menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def suno_extend_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🆔 Вставить audioId", callback_data="suno:ext:set:audio")],
        [InlineKeyboardButton(text="✅ Продлить", callback_data="suno:ext:submit")],
        [InlineKeyboardButton(text="🔙 В меню Suno", callback_data="suno:menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


