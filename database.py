import sqlite3
from contextlib import contextmanager
from datetime import datetime

from config import DB_PATH


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                phone TEXT,
                role TEXT,
                is_active_driver INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                passenger_id INTEGER NOT NULL,
                passenger_phone TEXT,
                lat REAL,
                lon REAL,
                status TEXT NOT NULL DEFAULT 'pending',
                driver_id INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY (passenger_id) REFERENCES users (user_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS order_notifications (
                order_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                PRIMARY KEY (order_id, chat_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )


def upsert_user(user_id: int, username: str | None, full_name: str | None):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO users (user_id, username, full_name, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name
            """,
            (user_id, username, full_name, datetime.utcnow().isoformat()),
        )


def set_role(user_id: int, role: str):
    with get_conn() as conn:
        conn.execute("UPDATE users SET role = ? WHERE user_id = ?", (role, user_id))


def set_phone(user_id: int, phone: str):
    with get_conn() as conn:
        conn.execute("UPDATE users SET phone = ? WHERE user_id = ?", (phone, user_id))


def set_driver_active(user_id: int, active: bool):
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET is_active_driver = ? WHERE user_id = ?",
            (1 if active else 0, user_id),
        )


def get_user(user_id: int) -> sqlite3.Row | None:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()


def get_active_drivers() -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE role = 'driver' AND is_active_driver = 1"
        ).fetchall()


def create_order(passenger_id: int, phone: str, lat: float | None, lon: float | None) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO orders (passenger_id, passenger_phone, lat, lon, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (passenger_id, phone, lat, lon, datetime.utcnow().isoformat()),
        )
        return cur.lastrowid


def get_order(order_id: int) -> sqlite3.Row | None:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()


def accept_order(order_id: int, driver_id: int) -> bool:
    """Atomically mark an order as accepted. Returns False if it was already taken."""
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE orders SET status = 'accepted', driver_id = ? WHERE id = ? AND status = 'pending'",
            (driver_id, order_id),
        )
        return cur.rowcount == 1


def save_notification(order_id: int, chat_id: int, message_id: int):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO order_notifications (order_id, chat_id, message_id) VALUES (?, ?, ?)",
            (order_id, chat_id, message_id),
        )


def get_notifications(order_id: int) -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM order_notifications WHERE order_id = ?", (order_id,)
        ).fetchall()


def get_setting(key: str) -> str | None:
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None


def set_setting(key: str, value: str):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )


def get_all_user_ids() -> list[int]:
    with get_conn() as conn:
        rows = conn.execute("SELECT user_id FROM users").fetchall()
        return [row["user_id"] for row in rows]


def get_stats() -> dict:
    with get_conn() as conn:

        def count(query: str) -> int:
            return conn.execute(query).fetchone()["c"]

        return {
            "total_users": count("SELECT COUNT(*) c FROM users"),
            "total_passengers": count("SELECT COUNT(*) c FROM users WHERE role = 'passenger'"),
            "total_drivers": count("SELECT COUNT(*) c FROM users WHERE role = 'driver'"),
            "active_drivers": count(
                "SELECT COUNT(*) c FROM users WHERE role = 'driver' AND is_active_driver = 1"
            ),
            "total_orders": count("SELECT COUNT(*) c FROM orders"),
            "pending_orders": count("SELECT COUNT(*) c FROM orders WHERE status = 'pending'"),
            "accepted_orders": count("SELECT COUNT(*) c FROM orders WHERE status = 'accepted'"),
        }
