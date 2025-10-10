from bot.enums import BotModeEnum

settings_models_mapper = {
    BotModeEnum.gpt: "gpt_price",
    BotModeEnum.gpt_mini: "gpt_mini_price",
    BotModeEnum.gpt_image: "gpt_image_price",
    BotModeEnum.nano_banana: "nano_banana_price",
    BotModeEnum.suno_music: "suno_music_price",
    BotModeEnum.veo_video: "veo_standard_price",  # default maps to standard; improved selected in flow
    BotModeEnum.sora2_video: "sora2_video_price",
}