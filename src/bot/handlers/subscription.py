import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, LabeledPrice, Message
from dependency_injector.wiring import Provide, inject

from bot.container import Container
from bot.enums import BotModeEnum
from bot.interfaces.services.payments import AbcPaymentsService
from bot.interfaces.services.subscription import AbcSubscriptionService
from bot.keyboards.payments import pay_link_keyboard, payments_back_keyboard
from bot.keyboards.start import start_keyboard
from bot.settings import settings

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "pay:ru_sub")
@inject
async def pay_ru_sub(
    call: CallbackQuery,
    payments: AbcPaymentsService = Provide[Container.payments_service],
):
    await call.answer()
    try:
        url = await payments.create_ru_subscription(user_id=call.from_user.id, price_rub=2999)
        await call.message.edit_text(
            text=(
                "🔖 Подписка GPT + 2000 токенов — 2999₽\n\n"
                "Оплата через YooKassa."
            ),
            reply_markup=pay_link_keyboard(url),
        )
    except Exception as e:
        await call.message.edit_text(
            text=f"Не удалось создать ссылку на оплату: {e}",
            reply_markup=payments_back_keyboard(),
        )


@router.callback_query(F.data == "pay:card_sub")
@inject
async def pay_card_sub(
    call: CallbackQuery,
    payments: AbcPaymentsService = Provide[Container.payments_service],
):
    await call.answer()
    try:
        url = await payments.create_card_subscription(user_id=call.from_user.id, price_rub=2999)
        await call.message.edit_text(
            text=(
                "🔖 Подписка GPT + 2000 токенов — 2999₽\n\n"
                "Оплата картой (BePaid)."
            ),
            reply_markup=pay_link_keyboard(url),
        )
    except Exception as e:
        await call.message.edit_text(
            text=f"Не удалось создать ссылку на оплату: {e}",
            reply_markup=payments_back_keyboard(),
        )


@router.callback_query(F.data == "pay:card_byn_sub")
@inject
async def pay_card_byn_sub(
    call: CallbackQuery,
    payments: AbcPaymentsService = Provide[Container.payments_service],
):
    await call.answer()
    try:
        url = await payments.create_card_byn_subscription(user_id=call.from_user.id, price_byn=110)
        await call.message.edit_text(
            text=(
                "🔖 Подписка GPT + 2000 токенов — 110 BYN (~$37.04)\n\n"
                "Оплата картой (BePaid)."
            ),
            reply_markup=pay_link_keyboard(url),
        )
    except Exception as e:
        await call.message.edit_text(
            text=f"Не удалось создать ссылку на оплату: {e}",
            reply_markup=payments_back_keyboard(),
        )


@router.callback_query(F.data == "pay:stars_sub")
async def pay_stars_sub(call: CallbackQuery):
    await call.answer()
    try:
        await call.bot.send_invoice(
            chat_id=call.from_user.id,
            title="Подписка GPT + 2000 токенов",
            description="Доступ к GPT без списания токенов + 2000 токенов на баланс. Срок 30 дней.",
            payload="stars_sub:2999",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label="Подписка GPT", amount=2999)],
            is_flexible=False,
            need_email=False,
            need_name=False,
            need_phone_number=False,
            need_shipping_address=False,
        )
    except Exception as e:
        await call.message.edit_text(
            text=f"Не удалось выставить счет в Stars: {e}",
            reply_markup=payments_back_keyboard(),
        )


@router.message(F.successful_payment)
@inject
async def stars_sub_success(
    message: Message,
    subscription_service: AbcSubscriptionService = Provide[Container.subscription_service],
):
    sp = message.successful_payment
    if not sp or (sp.currency or "").upper() != "XTR":
        return
    payload = sp.invoice_payload or ""
    if not payload.startswith("stars_sub:"):
        return
    try:
        await subscription_service.activate_or_extend_for_telegram(message.from_user.id, days=30, bonus_tokens=2000)
        await message.answer(
            text=(
                "🚀 Подписка GPT активирована на 30 дней.\n"
                "2000 токенов зачислены на баланс."
            ),
            reply_markup=start_keyboard(BotModeEnum.passive),
        )
    except Exception:
        await message.answer(
            text=f"Не удалось активировать подписку. Напишите @{settings.SUPPORT_USERNAME}.",
            reply_markup=start_keyboard(BotModeEnum.passive),
        )

