from bot.enums import BotModeEnum

settings_models_mapper = {
    BotModeEnum.gpt: "gpt_price",
    BotModeEnum.gpt_mini: "gpt_mini_price",
    BotModeEnum.nano_banana: "nano_banana_price",
    BotModeEnum.nano_banana_pro: "nano_banana_pro_price",
    BotModeEnum.suno_music: "suno_music_price",
    BotModeEnum.veo_video: "veo_standard_price",  # default maps to standard; improved selected in flow
    BotModeEnum.sora2_video: "sora2_video_price",
    BotModeEnum.sora2_pro_video: "sora2_pro_video_price",
}
