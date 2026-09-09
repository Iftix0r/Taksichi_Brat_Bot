from telegram import Update
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import ContextTypes, ConversationHandler

import database as db
from formatting import mention_html
from handlers.admin import DRIVERS_GROUP_KEY
from keyboards import (
    SKIP_TEXT,
    contact_driver_keyboard,
    contact_keyboard,
    contact_passenger_keyboard,
    main_menu_inline,
    remove_keyboard,
    skip_keyboard,
)

DRIVER_PHONE, DRIVER_AD = range(2)


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
        "✍️ E'loningizni yozing (yo'nalish, narx, mashina turi va h.k.):",
        reply_markup=skip_keyboard(),
    )
    return DRIVER_AD


async def driver_ad_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    ad_text = None if text == SKIP_TEXT else text
    user = update.effective_user
    driver = db.get_user(user.id)

    await update.message.reply_text(
        "Siz faol haydovchi sifatida ro'yxatdan o'tdingiz. "
        "Yangi buyurtmalar haqida xabar berib boramiz.",
        reply_markup=remove_keyboard(),
    )
    await update.message.reply_text("Bosh menyu:", reply_markup=main_menu_inline())

    await _post_driver_ad(context, user, driver, ad_text)
    return ConversationHandler.END


async def _post_driver_ad(context: ContextTypes.DEFAULT_TYPE, user, driver, ad_text: str | None):
    drivers_group_id = db.get_setting(DRIVERS_GROUP_KEY)
    if not drivers_group_id:
        return

    lines = [
        "🚕 Yangi haydovchi!",
        "",
        f"Ism: {mention_html(user.id, user.full_name)}",
        f"Telefon: {driver['phone']}",
    ]
    if ad_text:
        lines += ["", ad_text]

    try:
        await context.bot.send_message(
            chat_id=int(drivers_group_id),
            text="\n".join(lines),
            reply_markup=contact_driver_keyboard(user.username, user.id),
            parse_mode=ParseMode.HTML,
        )
    except TelegramError:
        pass


async def accept_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    order_id = int(query.data.split("_", 1)[1])
    driver = query.from_user
    origin_chat_id = query.message.chat_id
    origin_message_id = query.message.message_id

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
            f"✅ Ushbu buyurtmani {mention_html(driver.id, driver.full_name)} qabul qildi.\n\n"
            f"Yo'lovchi: {mention_html(passenger['user_id'], passenger['full_name'])}\n"
            f"Telefon: {passenger['phone']}",
            reply_markup=contact_passenger_keyboard(passenger["username"], passenger["user_id"]),
            parse_mode=ParseMode.HTML,
        )
    except TelegramError:
        pass

    await context.bot.send_message(
        chat_id=passenger["user_id"],
        text=(
            "✅ Sizning buyurtmangizni haydovchi qabul qildi!\n\n"
            f"Haydovchi: {mention_html(driver.id, driver.full_name)}\n"
            "Tez orada siz bilan bog'lanadi!"
        ),
        reply_markup=contact_driver_keyboard(driver.username, driver.id),
        parse_mode=ParseMode.HTML,
    )

    for notif in db.get_notifications(order_id):
        if notif["chat_id"] == origin_chat_id and notif["message_id"] == origin_message_id:
            continue
        try:
            await context.bot.edit_message_text(
                chat_id=notif["chat_id"],
                message_id=notif["message_id"],
                text="❌ Bu buyurtma boshqa haydovchi tomonidan qabul qilindi.",
            )
        except TelegramError:
            continue
