import logging

from dependency_injector.wiring import Provide, inject

from bot.container import Container
from bot.interfaces.services import AbcUserService
from bot.interfaces.services.settings import AbcSettingsService

logger = logging.getLogger(__name__)

@inject
async def run_daily_topup(
    user_service: AbcUserService = Provide[Container.user_service],
    settings_service: AbcSettingsService = Provide[Container.settings_service],
):
    try:
        daily_bonus = await settings_service.get_value("daily_bonus")
        updated = await user_service.daily_min_balance_topup(int(daily_bonus))
        logger.info("daily_topup_completed count=%s", updated)
    except Exception:
        logger.exception("daily_topup_failed")
