from aiogram import Bot
from aiogram.types import FSInputFile
from pathlib import Path
from aiohttp import web
import logging

from dependency_injector.wiring import inject, Provide
from sqlalchemy import select

from bot.container import Container
from bot.enums import BotModeEnum, TransactionReasonEnum
from bot.entities.transaction import TransactionEntity
from bot.database.models import TransactionOrm
from bot.interfaces.services import AbcUserService
from bot.interfaces.services.settings import AbcSettingsService
from bot.interfaces.services.subscription import AbcSubscriptionService
from bot.interfaces.services.payments import AbcPaymentsService
from bot.interfaces.uow import AbcUnitOfWork
from bot.keyboards import start_keyboard
from bot.keyboards.referral import referral_bonus_keyboard

logger = logging.getLogger(__name__)

@inject
async def yookassa_handle(
    request: web.Request,
    bot: Bot = Provide[Container.bot],
    admin_bot: Bot = Provide[Container.admin_bot],
    user_service: AbcUserService = Provide[Container.user_service],
    payments: AbcPaymentsService = Provide[Container.payments_service],
    subscription_service: AbcSubscriptionService = Provide[Container.subscription_service],
    settings: AbcSettingsService = Provide[Container.settings_service],
    uow: AbcUnitOfWork = Provide[Container.uow],
):
    logger.info(f"JSON FOR DEBUGGING: \n\n\n{await request.json()}\n\n\n")
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"status": "bad json"}, status=400)

    event = body.get("event")
    if event == "payment.succeeded":
        payment_id = body.get("object", {}).get("id")
        if payment_id:
            try:
                obj = body.get("object", {})
                metadata = obj.get("metadata", {}) or {}
                telegram_id = (
                    int(metadata.get("user_id"))
                    if metadata.get("user_id")
                    else None
                )
                credited = await payments.check_payment_and_credit(payment_id)
                try:
                    tokens = (
                        int(metadata.get("tokens"))
                        if metadata.get("tokens")
                        else None
                    )
                    if telegram_id and tokens:
                        user = await user_service.get_user(telegram_id)
                        if user:
                            # Try to award referral purchase bonus (+100) to inviter once per referred user
                            try:
                                ref_raw = getattr(user, 'from_', None)
                                inviter_tid = int(ref_raw) if ref_raw else None
                            except Exception:
                                inviter_tid = None
                            if inviter_tid and inviter_tid != telegram_id:
                                try:
                                    async with uow:
                                        inviter = await uow.user.get_by_telegram_id(inviter_tid)
                                        if inviter:
                                            meta_tag = f"referred:{telegram_id}"
                                            stmt = (
                                                select(TransactionOrm.id)
                                                .where(
                                                    TransactionOrm.user_id == inviter.id,
                                                    TransactionOrm.reason == str(TransactionReasonEnum.referral_purchase_bonus),
                                                    TransactionOrm.meta == meta_tag,
                                                )
                                                .limit(1)
                                            )
                                            res = await uow.transaction.session.execute(stmt)
                                            if res.first() is None:
                                                updated = await uow.user.update_balance_by_user_id(inviter.id, 100)
                                                if updated:
                                                    await uow.transaction.add(
                                                        TransactionEntity(
                                                            user_id=inviter.id,
                                                            delta=100,
                                                            reason=TransactionReasonEnum.referral_purchase_bonus,
                                                            meta=meta_tag,
                                                        )
                                                    )
                                                    try:
                                                        uname = getattr(user, 'username', None)
                                                        suffix = f" за пользователя {uname}" if uname else ""
                                                        text = (
                                                            f"🎉 Поздравляем, ты получил реферальный бонус{suffix}: 100 токенов!\n\n"
                                                            "🎞️ Копи бонусные токены или выбирай модель и твори!"
                                                        )
                                                        await bot.send_message(inviter_tid, text, reply_markup=referral_bonus_keyboard(), parse_mode=None)
                                                    except Exception:
                                                        pass
                                except Exception:
                                    pass
                            sent_custom = False
                            if tokens in (1100, 2400, 3800, 7000):
                                special_text = (
                                    "🎉 Спасибо за покупку!\n\n"
                                    "Вы получили:\n"
                                    f"🛸 {tokens} токенов — ваш личный запас для общения с ИИ\n"
                                    "🎁 Гайд по использованию — пошаговое руководство, как извлечь максимум из возможностей нашего бота.\n\n"
                                    "В гайде вы найдёте:\n"
                                    "✨ как правильно формулировать запросы,\n"
                                    "⚙️ примеры эффективных промтов,\n"
                                    "💡 способы ускорить и улучшить ответы ИИ,\n"
                                    "🚀 идеи для реальных задач — от работы до творчества.\n\n"
                                    "Приятного изучения и продуктивного общения с ИИ!"
                                )
                                await bot.send_message(
                                    telegram_id,
                                    special_text,
                                    reply_markup=start_keyboard(BotModeEnum.passive),
                                    parse_mode=None,
                                )
                                try:
                                    guide_path = (Path(__file__).resolve().parents[2] / "media" / "files" / "guide.pdf")
                                    await bot.send_document(
                                        telegram_id,
                                        document=FSInputFile(guide_path.as_posix()),
                                    )
                                except Exception:
                                    pass
                                sent_custom = True
                            if not sent_custom:
                                text = (
                                f"✅ Оплата прошла успешно! Зачислено {tokens} токенов.\n\n"
                                f"🪙 Твой баланс: *{user.balance}* токенов\n\n"
                                "👇 Что хочешь сделать?"
                            )
                                await bot.send_message(
                                telegram_id,
                                text,
                                reply_markup=start_keyboard(BotModeEnum.passive),
                                )
                            try:
                                admins = await user_service.list_admins()
                                try:
                                    _raw = await settings.get_value(f"{tokens}_bundle_price")
                                    _price_val = int(_raw) if _raw is not None else None
                                except Exception:
                                    _price_val = None
                                amount_text = f"{_price_val} ₽" if isinstance(_price_val, int) and _price_val > 0 else "-"
                                uname = getattr(user, 'username', None)
                                username = f"@{uname}" if uname else "—"
                                admin_text = (
                                    "🎉 Поступила оплата!\n\n"
                                    f"👤 Пользователь: {username} ({telegram_id})\n"
                                    f"📦 Количество токенов: {tokens}\n"
                                    f"💳 Способ оплаты: YooKassa\n\n"
                                    f"💵 Сумма: {amount_text}"
                                )
                                for admin in admins:
                                    try:
                                        await admin_bot.send_message(admin.telegram_id, admin_text, parse_mode=None)
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                            return web.json_response({"ok": credited})
                except Exception:
                    pass
                return web.json_response({"ok": credited})
            except Exception:
                logger.exception("yookassa webhook error")
                return web.json_response({"ok": False}, status=500)
    elif event == "payment.canceled":
        logger.info(
            "YooKassa payment.canceled: %s", body.get("object", {}).get("id")
        )
        return web.json_response({"ok": True})
    elif event == "refund.succeeded":
        logger.info(
            "YooKassa refund.succeeded: %s", body.get("object", {}).get("id")
        )
        return web.json_response({"ok": True})
    return web.json_response({"ok": True})
