from enum import StrEnum, auto


class BotModeEnum(StrEnum):
    passive = "Не выбран"
    gpt = "GPT-5"
    gpt_mini = "GPT-5 Mini"
    gpt_image = "GPT Image"
    nano_banana = "Nano Banana"
    suno_music = "Suno"
    veo_video = "Veo 3"


class LedgerReasonEnum(StrEnum):
    welcome_bonus = auto()
    gpt_request = auto()
    gpt_mini_request = auto()
    gpt_image_request = auto()
    nano_banana_request = auto()
    suno_request = auto()
    purchase_stars = auto()
    veo_request = auto()
    daily_bonus = auto()
    admin_adjustment = auto()
