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
from handlers.admin import (
    WAITING_DRIVERS_ID,
    WAITING_ORDERS_ID,
    admin_cancel,
    admin_panel,
    admin_refresh,
    ask_drivers_id,
    ask_orders_id,
    receive_drivers_id,
    receive_orders_id,
)
from handlers.driver import (
    DRIVER_AD,
    DRIVER_PHONE,
    accept_order,
    driver_ad_received,
    driver_phone_received,
    role_driver,
)
from handlers.passenger import (
    LOCATION,
    PHONE,
    location_received,
    location_skipped,
    phone_received,
    role_passenger,
)
from handlers.start import cancel, start
from keyboards import SKIP_TEXT

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
                MessageHandler(filters.Regex(f"^{SKIP_TEXT}$"), location_skipped),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    driver_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(role_driver, pattern="^role_driver$")],
        states={
            DRIVER_PHONE: [MessageHandler(filters.CONTACT, driver_phone_received)],
            DRIVER_AD: [MessageHandler(filters.TEXT & ~filters.COMMAND, driver_ad_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    admin_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(ask_orders_id, pattern="^admin_ask_orders_id$"),
            CallbackQueryHandler(ask_drivers_id, pattern="^admin_ask_drivers_id$"),
        ],
        states={
            WAITING_ORDERS_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_orders_id)],
            WAITING_DRIVERS_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_drivers_id)],
        },
        fallbacks=[CommandHandler("cancel", admin_cancel)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CallbackQueryHandler(admin_refresh, pattern="^admin_refresh$"))
    application.add_handler(admin_conv)
    application.add_handler(passenger_conv)
    application.add_handler(driver_conv)
    application.add_handler(CallbackQueryHandler(accept_order, pattern=r"^accept_\d+$"))

    logger.info("Bot ishga tushdi...")
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
