import logging

from dependency_injector.wiring import Provide, inject

from bot.container import Container
from bot.interfaces.services import AbcUserService

logger = logging.getLogger(__name__)

@inject
async def run_daily_topup(
    user_service: AbcUserService = Provide[Container.user_service],
):
    try:
        updated = await user_service.daily_min_balance_topup(50)
        logger.info("daily_topup_completed count=%s", updated)
    except Exception:
        logger.exception("daily_topup_failed")
