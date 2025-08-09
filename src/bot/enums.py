from enum import StrEnum, auto


class BotModeEnum(StrEnum):
    passive = "Не выбран"
    gpt5 = "GPT-5"
    gpt5_mini = "GPT-5 Mini"
    dalle3 = "DALL-E 3"
    veo = "Veo-3"

class LedgerReasonEnum(StrEnum):
    welcome_bonus = auto()
    gpt5_request = auto()
    gpt5_mini_request = auto()
    dalle3_image = auto()
