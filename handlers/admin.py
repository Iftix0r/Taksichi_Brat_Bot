from telegram import Update
from telegram.ext import ContextTypes

import database as db
from config import ADMIN_IDS
from keyboards import admin_menu_keyboard

ORDERS_GROUP_KEY = "orders_group_id"
DRIVERS_GROUP_KEY = "drivers_group_id"


def _admin_menu_text() -> str:
    orders_group = db.get_setting(ORDERS_GROUP_KEY)
    drivers_group = db.get_setting(DRIVERS_GROUP_KEY)
    return (
        "⚙️ Admin panel\n\n"
        f"📦 Buyurtmalar guruhi: {orders_group or 'o‘rnatilmagan'}\n"
        f"🚕 Haydovchilar guruhi: {drivers_group or 'o‘rnatilmagan'}\n\n"
        "Guruhni sozlash uchun botni kerakli guruhga a'zo (yaxshisi, admin) qilib qo'shing "
        "va o'sha guruh ichida quyidagi buyruqlardan birini yuboring:\n\n"
        "/set_orders_group — yangi buyurtmalar shu guruhga yuboriladi\n"
        "/set_drivers_group — haydovchilar e'lonlari shu guruhga yuboriladi"
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


async def set_orders_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS:
        return
    chat = update.effective_chat
    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text("Bu buyruq faqat guruh ichida ishlatiladi.")
        return
    db.set_setting(ORDERS_GROUP_KEY, str(chat.id))
    await update.message.reply_text("✅ Bu guruh endi buyurtmalar guruhi sifatida belgilandi.")


async def set_drivers_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS:
        return
    chat = update.effective_chat
    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text("Bu buyruq faqat guruh ichida ishlatiladi.")
        return
    db.set_setting(DRIVERS_GROUP_KEY, str(chat.id))
    await update.message.reply_text(
        "✅ Bu guruh endi haydovchilar e'lonlari guruhi sifatida belgilandi."
    )
