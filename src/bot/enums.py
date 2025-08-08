from enum import StrEnum, auto


class BotModeEnum(StrEnum):
    passive = "Не выбран"
    gpt5 = "GPT-5"
    dalle3 = "DALL-E 3"
    veo = "Veo-3"
