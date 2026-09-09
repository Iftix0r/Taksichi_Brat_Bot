from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.constants import KeyboardButtonStyle

SKIP_TEXT = "➡️ O'tkazib yuborish"
BACK_TEXT = "⬅️ Bosh menyu"


def main_menu_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🧍 YO'LOVCHI - Taxi chaqirish",
                    callback_data="role_passenger",
                    style=KeyboardButtonStyle.PRIMARY,
                )
            ],
            [
                InlineKeyboardButton(
                    "🚕 HAYDOVCHI - E'lon joylashtirish",
                    callback_data="role_driver",
                    style=KeyboardButtonStyle.SUCCESS,
                )
            ],
        ]
    )


def contact_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton(
                    "📱 Telefon raqamni yuborish",
                    request_contact=True,
                    style=KeyboardButtonStyle.SUCCESS,
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def location_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton(
                    "📍 Joylashuvni yuborish",
                    request_location=True,
                    style=KeyboardButtonStyle.PRIMARY,
                )
            ],
            [KeyboardButton(SKIP_TEXT)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def skip_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton(SKIP_TEXT)]], resize_keyboard=True, one_time_keyboard=True
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


def order_accept_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Qabul qilish",
                    callback_data=f"accept_{order_id}",
                    style=KeyboardButtonStyle.SUCCESS,
                )
            ]
        ]
    )


def contact_driver_keyboard(username: str | None, user_id: int) -> InlineKeyboardMarkup:
    url = f"https://t.me/{username}" if username else f"tg://user?id={user_id}"
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("✉️ Xabar yozish", url=url, style=KeyboardButtonStyle.PRIMARY)]]
    )


def contact_passenger_keyboard(username: str | None, user_id: int) -> InlineKeyboardMarkup:
    url = f"https://t.me/{username}" if username else f"tg://user?id={user_id}"
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✉️ Yo'lovchiga yozish", url=url, style=KeyboardButtonStyle.PRIMARY
                )
            ]
        ]
    )


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📦 Buyurtmalar guruhini ID orqali ulash",
                    callback_data="admin_ask_orders_id",
                    style=KeyboardButtonStyle.PRIMARY,
                )
            ],
            [
                InlineKeyboardButton(
                    "🚕 Haydovchilar guruhini ID orqali ulash",
                    callback_data="admin_ask_drivers_id",
                    style=KeyboardButtonStyle.SUCCESS,
                )
            ],
            [InlineKeyboardButton("🔄 Yangilash", callback_data="admin_refresh")],
        ]
    )
