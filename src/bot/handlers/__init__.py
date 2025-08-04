from aiogram import Router
from bot.handlers.start.regular import router as start_regular_router
from bot.handlers.start.callbacks import router as start_callbacks_router
from bot.handlers.message import router as message_router

router = Router()

router.include_routers(
    start_callbacks_router,
    start_regular_router,
    message_router,
)
