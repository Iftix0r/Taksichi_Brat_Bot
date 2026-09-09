from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes, ConversationHandler

import database as db
from keyboards import (
    contact_driver_keyboard,
    contact_keyboard,
    contact_passenger_keyboard,
    main_menu_inline,
    remove_keyboard,
)

DRIVER_PHONE = 0


async def role_driver(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user = query.from_user
    db.upsert_user(user.id, user.username, user.full_name)
    db.set_role(user.id, "driver")

    await query.edit_message_text("🚕 HAYDOVCHI rejimi tanlandi.")
    await context.bot.send_message(
        chat_id=user.id,
        text="Telefon raqamingizni yuboring:",
        reply_markup=contact_keyboard(),
    )
    return DRIVER_PHONE


async def driver_phone_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    contact = update.message.contact
    if contact.user_id and contact.user_id != update.effective_user.id:
        await update.message.reply_text(
            "Iltimos, o'zingizning telefon raqamingizni yuboring.",
            reply_markup=contact_keyboard(),
        )
        return DRIVER_PHONE

    user_id = update.effective_user.id
    db.set_phone(user_id, contact.phone_number)
    db.set_driver_active(user_id, True)

    await update.message.reply_text(
        "Siz faol haydovchi sifatida ro'yxatdan o'tdingiz. "
        "Yangi buyurtmalar haqida xabar berib boramiz.",
        reply_markup=remove_keyboard(),
    )
    await update.message.reply_text("Bosh menyu:", reply_markup=main_menu_inline())
    return ConversationHandler.END


async def accept_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    order_id = int(query.data.split("_", 1)[1])
    driver = query.from_user

    success = db.accept_order(order_id, driver.id)

    if not success:
        await query.answer("Bu buyurtma allaqachon band qilingan.", show_alert=True)
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except TelegramError:
            pass
        return

    await query.answer("Buyurtma qabul qilindi!")

    order = db.get_order(order_id)
    passenger = db.get_user(order["passenger_id"])

    try:
        await query.edit_message_text(
            f"✅ Siz ushbu buyurtmani qabul qildingiz.\n\nYo'lovchi: {passenger['full_name']}\n"
            f"Telefon: {passenger['phone']}",
            reply_markup=contact_passenger_keyboard(passenger["username"], passenger["user_id"]),
        )
    except TelegramError:
        pass

    await context.bot.send_message(
        chat_id=passenger["user_id"],
        text=(
            "✅ Sizning buyurtmangizni haydovchi qabul qildi!\n\n"
            f"Haydovchi: {driver.full_name}\n"
            "Tez orada siz bilan bog'lanadi!"
        ),
        reply_markup=contact_driver_keyboard(driver.username, driver.id),
    )

    for notif in db.get_notifications(order_id):
        if notif["driver_id"] == driver.id:
            continue
        try:
            await context.bot.edit_message_text(
                chat_id=notif["driver_id"],
                message_id=notif["message_id"],
                text="❌ Bu buyurtma boshqa haydovchi tomonidan qabul qilindi.",
            )
        except TelegramError:
            continue
