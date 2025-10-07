from aiohttp import web

from bot.webhooks.bepaid import bepaid_handle
from bot.webhooks.gpt_image import kie_image_handle
from bot.webhooks.nano_banana import kie_nano_handle
from bot.webhooks.suno import suno_handle
from bot.webhooks.veo import veo_handle
from bot.webhooks.yookassa import yookassa_handle
from bot.settings import settings


async def init_api_webhooks():
    app = web.Application()
    webhooks_app = web.Application()

    webhooks_app.router.add_post("/yookassa", yookassa_handle)
    webhooks_app.router.add_post("/bepaid", bepaid_handle)
    webhooks_app.router.add_post("/kie-image", kie_image_handle)
    webhooks_app.router.add_post("/kie-nano", kie_nano_handle)
    webhooks_app.router.add_post("/suno", suno_handle)
    webhooks_app.router.add_post("/veo", veo_handle)

    app.add_subapp("/webhooks", webhooks_app)

    runner = web.AppRunner(app)

    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", settings.WEBHOOKS.PORT)
    await site.start()
