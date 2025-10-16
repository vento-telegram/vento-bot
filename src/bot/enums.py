from enum import StrEnum, auto


class BotModeEnum(StrEnum):
    passive = "Не выбран"
    gpt = "GPT-5"
    gpt_mini = "GPT-5 Mini"
    nano_banana = "Nano Banana"
    suno_music = "Suno"
    veo_video = "Veo 3.1"
    sora2_video = "Sora 2"


class TransactionReasonEnum(StrEnum):
    welcome_bonus = auto()
    gpt_request = auto()
    gpt_mini_request = auto()
    gpt_refund = auto()
    gpt_mini_refund = auto()
    nano_banana_request = auto()
    nano_banana_refund = auto()
    suno_request = auto()
    suno_refund = auto()
    purchase_stars = auto()
    purchase_bepaid = auto()
    purchase_yookassa = auto()
    purchase_subscription_stars = auto()
    purchase_subscription_bepaid = auto()
    purchase_subscription_yookassa = auto()
    purchase_subscription_bonus = auto()
    veo_request = auto()
    veo_refund = auto()
    daily_bonus = auto()
    admin_adjustment = auto()
    sora2_request = auto()
    sora2_refund = auto()
