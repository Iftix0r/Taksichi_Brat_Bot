import logging

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

import database as db
from config import BOT_TOKEN
from handlers.driver import DRIVER_PHONE, accept_order, driver_phone_received, role_driver
from handlers.passenger import (
    LOCATION,
    PHONE,
    location_received,
    location_skipped,
    phone_received,
    role_passenger,
)
from handlers.start import cancel, start
from keyboards import SKIP_LOCATION_TEXT

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def main() -> None:
    db.init_db()

    application = Application.builder().token(BOT_TOKEN).build()

    passenger_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(role_passenger, pattern="^role_passenger$")],
        states={
            PHONE: [MessageHandler(filters.CONTACT, phone_received)],
            LOCATION: [
                MessageHandler(filters.LOCATION, location_received),
                MessageHandler(filters.Regex(f"^{SKIP_LOCATION_TEXT}$"), location_skipped),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    driver_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(role_driver, pattern="^role_driver$")],
        states={
            DRIVER_PHONE: [MessageHandler(filters.CONTACT, driver_phone_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(passenger_conv)
    application.add_handler(driver_conv)
    application.add_handler(CallbackQueryHandler(accept_order, pattern=r"^accept_\d+$"))

    logger.info("Bot ishga tushdi...")
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
