from enum import StrEnum, auto


class BotModeEnum(StrEnum):
    passive = "Не выбран"
    gpt = "GPT-5"
    gpt_mini = "GPT-5 Mini"


class LedgerReasonEnum(StrEnum):
    welcome_bonus = auto()
    gpt_request = auto()
    gpt_mini_request = auto()
    purchase_stars = auto()
