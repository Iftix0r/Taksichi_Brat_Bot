from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler, filters

import database as db
from formatting import mention_html
from handlers.admin import ORDERS_GROUP_KEY
from keyboards import (
    SKIP_TEXT,
    contact_keyboard,
    location_keyboard,
    main_menu_inline,
    order_accept_keyboard,
    remove_keyboard,
)

PHONE, LOCATION = range(2)


async def role_passenger(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user = query.from_user
    db.upsert_user(user.id, user.username, user.full_name)
    db.set_role(user.id, "passenger")

    await query.edit_message_text("🧍 YO'LOVCHI rejimi tanlandi.")
    await context.bot.send_message(
        chat_id=user.id,
        text="Telefon raqamingizni yuboring:",
        reply_markup=contact_keyboard(),
    )
    return PHONE


async def phone_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    contact = update.message.contact
    if contact.user_id and contact.user_id != update.effective_user.id:
        await update.message.reply_text(
            "Iltimos, o'zingizning telefon raqamingizni yuboring.",
            reply_markup=contact_keyboard(),
        )
        return PHONE

    db.set_phone(update.effective_user.id, contact.phone_number)
    context.user_data["phone"] = contact.phone_number

    await update.message.reply_text(
        "Joylashuvingizni yuboring (ixtiyoriy):",
        reply_markup=location_keyboard(),
    )
    return LOCATION


async def _finish_order(update: Update, context: ContextTypes.DEFAULT_TYPE, lat, lon) -> int:
    user = update.effective_user
    phone = context.user_data.get("phone")
    order_id = db.create_order(user.id, phone, lat, lon)

    await update.message.reply_text(
        "Tez orada haydovchilarimiz siz bilan bog'lanishadi!",
        reply_markup=remove_keyboard(),
    )
    await update.message.reply_text("Bosh menyu:", reply_markup=main_menu_inline())

    await _notify_drivers(context, order_id, user)
    return ConversationHandler.END


async def location_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    loc = update.message.location
    return await _finish_order(update, context, loc.latitude, loc.longitude)


async def location_skipped(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await _finish_order(update, context, None, None)


async def _notify_drivers(context: ContextTypes.DEFAULT_TYPE, order_id: int, passenger) -> None:
    order = db.get_order(order_id)

    text = (
        "🚕 Yangi buyurtma!\n\n"
        f"Yo'lovchi: {mention_html(passenger.id, passenger.full_name)}\n"
        f"Telefon: {order['passenger_phone']}\n"
    )

    orders_group_id = db.get_setting(ORDERS_GROUP_KEY)
    if orders_group_id:
        target_chat_ids = [int(orders_group_id)]
    else:
        target_chat_ids = [driver["user_id"] for driver in db.get_active_drivers()]

    for chat_id in target_chat_ids:
        try:
            if order["lat"] is not None and order["lon"] is not None:
                await context.bot.send_location(
                    chat_id=chat_id, latitude=order["lat"], longitude=order["lon"]
                )
            message = await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=order_accept_keyboard(order_id),
                parse_mode=ParseMode.HTML,
            )
            db.save_notification(order_id, chat_id, message.message_id)
        except Exception:
            continue
