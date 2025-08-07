from enum import StrEnum, auto


class BotModeEnum(StrEnum):
    passive = auto()
    chatgpt = auto()
    dalle = auto()
    veo = auto()
