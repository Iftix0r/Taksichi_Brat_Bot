from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes, ConversationHandler

import database as db
from config import ADMIN_IDS
from keyboards import admin_menu_keyboard, remove_keyboard

ORDERS_GROUP_KEY = "orders_group_id"
DRIVERS_GROUP_KEY = "drivers_group_id"

WAITING_ORDERS_ID, WAITING_DRIVERS_ID = range(2)


def _admin_menu_text() -> str:
    orders_group = db.get_setting(ORDERS_GROUP_KEY)
    drivers_group = db.get_setting(DRIVERS_GROUP_KEY)
    return (
        "⚙️ Admin panel\n\n"
        f"📦 Buyurtmalar guruhi: {orders_group or 'o‘rnatilmagan'}\n"
        f"🚕 Haydovchilar guruhi: {drivers_group or 'o‘rnatilmagan'}\n\n"
        "Guruhni ulash uchun pastdagi tugmalardan birini bosing va guruh ID sini yuboring.\n\n"
        "Guruh ID sini olish uchun botni o'sha guruhga a'zo qiling va guruhdan istalgan "
        "xabarni @userinfobot ga forward qiling (yoki guruh ID odatda -100 bilan boshlanadi)."
    )


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("Sizda admin panelga kirish huquqi yo'q.")
        return
    await update.message.reply_text(_admin_menu_text(), reply_markup=admin_menu_keyboard())


async def admin_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query.from_user.id not in ADMIN_IDS:
        await query.answer("Sizda ruxsat yo'q.", show_alert=True)
        return
    await query.answer()
    await query.edit_message_text(_admin_menu_text(), reply_markup=admin_menu_keyboard())


async def ask_orders_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query.from_user.id not in ADMIN_IDS:
        await query.answer("Sizda ruxsat yo'q.", show_alert=True)
        return ConversationHandler.END
    await query.answer()
    await query.edit_message_text(
        "📦 Buyurtmalar guruhining ID sini yuboring (masalan: -1001234567890):\n\n"
        "Bekor qilish uchun /cancel yuboring."
    )
    return WAITING_ORDERS_ID


async def ask_drivers_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query.from_user.id not in ADMIN_IDS:
        await query.answer("Sizda ruxsat yo'q.", show_alert=True)
        return ConversationHandler.END
    await query.answer()
    await query.edit_message_text(
        "🚕 Haydovchilar guruhining ID sini yuboring (masalan: -1001234567890):\n\n"
        "Bekor qilish uchun /cancel yuboring."
    )
    return WAITING_DRIVERS_ID


async def _link_group(update: Update, context: ContextTypes.DEFAULT_TYPE, setting_key: str, label: str) -> int:
    raw = update.message.text.strip()
    try:
        chat_id = int(raw)
    except ValueError:
        await update.message.reply_text(
            "Bu to'g'ri ID emas. Guruh ID raqam bo'lishi kerak (masalan: -1001234567890). Qaytadan yuboring:"
        )
        return WAITING_ORDERS_ID if setting_key == ORDERS_GROUP_KEY else WAITING_DRIVERS_ID

    try:
        chat = await context.bot.get_chat(chat_id)
    except TelegramError:
        await update.message.reply_text(
            "Bot bu guruhga a'zo emas yoki ID noto'g'ri. Botni guruhga qo'shib, qaytadan urinib ko'ring.\n\n"
            "Qayta ID yuborishingiz mumkin yoki /cancel bilan bekor qiling."
        )
        return WAITING_ORDERS_ID if setting_key == ORDERS_GROUP_KEY else WAITING_DRIVERS_ID

    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text(
            "Bu ID guruhga tegishli emas. Guruh ID sini yuboring yoki /cancel bilan bekor qiling."
        )
        return WAITING_ORDERS_ID if setting_key == ORDERS_GROUP_KEY else WAITING_DRIVERS_ID

    db.set_setting(setting_key, str(chat_id))
    await update.message.reply_text(
        f"✅ \"{chat.title}\" guruhi endi {label} sifatida ulandi.",
        reply_markup=remove_keyboard(),
    )
    await update.message.reply_text(_admin_menu_text(), reply_markup=admin_menu_keyboard())
    return ConversationHandler.END


async def receive_orders_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await _link_group(update, context, ORDERS_GROUP_KEY, "buyurtmalar guruhi")


async def receive_drivers_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await _link_group(update, context, DRIVERS_GROUP_KEY, "haydovchilar e'lonlari guruhi")


async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Bekor qilindi.", reply_markup=remove_keyboard())
    return ConversationHandler.END
