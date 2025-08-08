from enum import StrEnum, auto


class BotModeEnum(StrEnum):
    passive = "Не выбран"
    gpt5 = "GPT-5"
    gpt5_mini = "GPT-5 Mini"
    dalle3 = "DALL-E 3"
    veo = "Veo-3"
