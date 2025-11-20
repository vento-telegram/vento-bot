from __future__ import annotations

from bot.enums import BotModeEnum

_LEGACY_MODE_ALIASES: dict[str, BotModeEnum] = {
    # Old values that were stored before we renamed GPT-5 to GPT-5.1
    "GPT-5": BotModeEnum.gpt,
}


def normalize_mode(value: BotModeEnum | str | None) -> BotModeEnum:
    """Return a valid BotModeEnum instance for arbitrary persisted values."""
    if isinstance(value, BotModeEnum):
        return value

    if isinstance(value, str):
        stripped_value = value.strip()
        if not stripped_value:
            return BotModeEnum.passive
        try:
            return BotModeEnum(stripped_value)
        except ValueError:
            alias = _LEGACY_MODE_ALIASES.get(stripped_value)
            if alias:
                return alias

    return BotModeEnum.passive


