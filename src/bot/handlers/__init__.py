from aiogram import Router

from bot.handlers.admin import router as admin_router
from bot.handlers.message import router as message_router
from bot.handlers.start.callbacks import router as start_callbacks_router
from bot.handlers.start.regular import router as start_regular_router
from bot.handlers.subscription import router as subscription_router

handlers_router = Router()

handlers_router.include_routers(
    start_callbacks_router,
    subscription_router,
    start_regular_router,
    admin_router,
    message_router,
)
