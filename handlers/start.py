from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

import database as db
from config import ADMIN_IDS
from handlers.admin import admin_menu_text
from keyboards import admin_menu_keyboard, main_menu_inline

WELCOME_TEXT = (
    "Assalomu alaykum! Taxi botiga xush kelibsiz!\n\n"
    "🧍 YO'LOVCHI - Taxi chaqirish\n"
    "🚕 HAYDOVCHI - E'lon joylashtirish"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    db.upsert_user(user.id, user.username, user.full_name)

    if user.id in ADMIN_IDS:
        await update.message.reply_text(admin_menu_text(), reply_markup=admin_menu_keyboard())
        return ConversationHandler.END

    await update.message.reply_text(WELCOME_TEXT, reply_markup=main_menu_inline())
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Bekor qilindi. Bosh menyuga qaytish uchun /start bosing.",
    )
    return ConversationHandler.END
