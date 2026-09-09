from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

SKIP_LOCATION_TEXT = "➡️ O'tkazib yuborish"
BACK_TEXT = "⬅️ Bosh menyu"


def main_menu_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🧍 YO'LOVCHI - Taxi chaqirish", callback_data="role_passenger")],
            [InlineKeyboardButton("🚕 HAYDOVCHI - E'lon joylashtirish", callback_data="role_driver")],
        ]
    )


def contact_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def location_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📍 Joylashuvni yuborish", request_location=True)],
            [KeyboardButton(SKIP_LOCATION_TEXT)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


def order_accept_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("✅ Qabul qilish", callback_data=f"accept_{order_id}")]]
    )


def contact_driver_keyboard(username: str | None, user_id: int) -> InlineKeyboardMarkup:
    url = f"https://t.me/{username}" if username else f"tg://user?id={user_id}"
    return InlineKeyboardMarkup([[InlineKeyboardButton("✉️ Xabar yozish", url=url)]])


def contact_passenger_keyboard(username: str | None, user_id: int) -> InlineKeyboardMarkup:
    url = f"https://t.me/{username}" if username else f"tg://user?id={user_id}"
    return InlineKeyboardMarkup([[InlineKeyboardButton("✉️ Yo'lovchiga yozish", url=url)]])
