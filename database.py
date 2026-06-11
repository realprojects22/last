"""
database.py - HALOL CRYPTO AI BOT V3.5
SQLite ma'lumotlar bazasi boshqaruvi
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from config import DB_NAME, DEFAULT_WATCHLIST

logger = logging.getLogger(__name__)


# ============================================================
# MA'LUMOTLAR BAZASI KONTEKST MENEJERI
# ============================================================

@contextmanager
def get_db():
    """Thread-safe SQLite ulanish kontekst menejeri."""
    conn = sqlite3.connect(DB_NAME, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database xatosi: {e}")
        raise
    finally:
        conn.close()


# ============================================================
# JADVALLARNI YARATISH
# ============================================================

def init_database() -> None:
    """Barcha jadvallarni yaratish va boshlang'ich ma'lumotlarni kiritish."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Foydalanuvchilar jadvali
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                first_name  TEXT,
                last_name   TEXT,
                language    TEXT DEFAULT 'uz',
                is_active   INTEGER DEFAULT 1,
                alerts_on   INTEGER DEFAULT 1,
                created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
                last_seen   TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Guruhlar jadvali
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                group_id    INTEGER PRIMARY KEY,
                title       TEXT,
                is_active   INTEGER DEFAULT 1,
                alerts_on   INTEGER DEFAULT 1,
                created_at  TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Kuzatuv ro'yxati jadvali
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlists (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                symbol      TEXT NOT NULL,
                added_at    TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, symbol),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)

        # Ogohlantirishlar tarixi jadvali
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER,
                group_id    INTEGER,
                symbol      TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                confidence  INTEGER,
                price       REAL,
                sent_at     TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Signal tarixi jadvali
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signal_history (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol          TEXT NOT NULL,
                signal_type     TEXT NOT NULL,
                confidence      INTEGER,
                price           REAL,
                stop_loss       REAL,
                tp1             REAL,
                tp2             REAL,
                tp3             REAL,
                risk_reward     REAL,
                entry_quality   INTEGER,
                rvol            REAL,
                trend           TEXT,
                indicators      TEXT,
                timeframe       TEXT DEFAULT '1h',
                created_at      TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Sozlamalar jadvali
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                user_id     INTEGER PRIMARY KEY,
                alert_threshold INTEGER DEFAULT 70,
                scan_interval   INTEGER DEFAULT 600,
                default_tf      TEXT DEFAULT '1h',
                show_chart      INTEGER DEFAULT 1,
                notify_strong   INTEGER DEFAULT 1,
                notify_buy      INTEGER DEFAULT 1,
                notify_risk     INTEGER DEFAULT 1,
                updated_at      TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)

        # Kesh jadvali
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key         TEXT PRIMARY KEY,
                value       TEXT NOT NULL,
                expires_at  TEXT NOT NULL
            )
        """)

        logger.info("✅ Ma'lumotlar bazasi muvaffaqiyatli ishga tushirildi")


# ============================================================
# FOYDALANUVCHI OPERATSIYALARI
# ============================================================

def upsert_user(user_id: int, username: str = "", first_name: str = "",
                last_name: str = "") -> None:
    """Foydalanuvchini yaratish yoki yangilash."""
    with get_db() as conn:
        conn.execute("""
            INSERT INTO users (user_id, username, first_name, last_name, last_seen)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                username   = excluded.username,
                first_name = excluded.first_name,
                last_name  = excluded.last_name,
                last_seen  = CURRENT_TIMESTAMP
        """, (user_id, username, first_name, last_name))


def get_user(user_id: int) -> Optional[Dict]:
    """Foydalanuvchi ma'lumotlarini olish."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None


def get_all_active_users() -> List[Dict]:
    """Barcha faol foydalanuvchilarni olish."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM users WHERE is_active = 1 AND alerts_on = 1"
        ).fetchall()
        return [dict(r) for r in rows]


def toggle_user_alerts(user_id: int, enabled: bool) -> None:
    """Foydalanuvchi ogohlantirishlarini yoqish/o'chirish."""
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET alerts_on = ? WHERE user_id = ?",
            (1 if enabled else 0, user_id)
        )


# ============================================================
# KUZATUV RO'YXATI OPERATSIYALARI
# ============================================================

def get_watchlist(user_id: int) -> List[str]:
    """Foydalanuvchi kuzatuv ro'yxatini olish."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT symbol FROM watchlists WHERE user_id = ? ORDER BY added_at",
            (user_id,)
        ).fetchall()
        if not rows:
            return list(DEFAULT_WATCHLIST)
        return [r["symbol"] for r in rows]


def add_to_watchlist(user_id: int, symbol: str) -> bool:
    """Kuzatuv ro'yxatiga tanga qo'shish."""
    try:
        with get_db() as conn:
            count = conn.execute(
                "SELECT COUNT(*) as cnt FROM watchlists WHERE user_id = ?",
                (user_id,)
            ).fetchone()["cnt"]

            from config import MAX_WATCHLIST_SIZE
            if count >= MAX_WATCHLIST_SIZE:
                return False

            conn.execute(
                "INSERT OR IGNORE INTO watchlists (user_id, symbol) VALUES (?, ?)",
                (user_id, symbol.upper())
            )
            return True
    except Exception as e:
        logger.error(f"Watchlist qo'shish xatosi: {e}")
        return False


def remove_from_watchlist(user_id: int, symbol: str) -> bool:
    """Kuzatuv ro'yxatidan tanga o'chirish."""
    try:
        with get_db() as conn:
            cursor = conn.execute(
                "DELETE FROM watchlists WHERE user_id = ? AND symbol = ?",
                (user_id, symbol.upper())
            )
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Watchlist o'chirish xatosi: {e}")
        return False


def clear_watchlist(user_id: int) -> None:
    """Kuzatuv ro'yxatini to'liq tozalash."""
    with get_db() as conn:
        conn.execute("DELETE FROM watchlists WHERE user_id = ?", (user_id,))


# ============================================================
# OGOHLANTIRISH OPERATSIYALARI
# ============================================================

def record_alert(user_id: Optional[int], symbol: str, signal_type: str,
                 confidence: int, price: float, group_id: Optional[int] = None) -> None:
    """Yuborilgan ogohlantirishni qayd etish."""
    with get_db() as conn:
        conn.execute("""
            INSERT INTO alert_history
                (user_id, group_id, symbol, signal_type, confidence, price)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, group_id, symbol, signal_type, confidence, price))


def check_alert_cooldown(user_id: int, symbol: str, cooldown_seconds: int) -> bool:
    """Ogohlantirish cooldown tekshiruvi. True = cooldown davom etmoqda."""
    with get_db() as conn:
        cutoff = (datetime.utcnow() - timedelta(seconds=cooldown_seconds)).isoformat()
        row = conn.execute("""
            SELECT COUNT(*) as cnt FROM alert_history
            WHERE user_id = ? AND symbol = ? AND sent_at > ?
        """, (user_id, symbol, cutoff)).fetchone()
        return row["cnt"] > 0


def get_alert_history(user_id: int, limit: int = 20) -> List[Dict]:
    """Foydalanuvchi ogohlantirish tarixini olish."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM alert_history
            WHERE user_id = ?
            ORDER BY sent_at DESC LIMIT ?
        """, (user_id, limit)).fetchall()
        return [dict(r) for r in rows]


# ============================================================
# SIGNAL TARIXI OPERATSIYALARI
# ============================================================

def save_signal(symbol: str, signal_data: Dict) -> None:
    """Signal ma'lumotlarini saqlash."""
    with get_db() as conn:
        conn.execute("""
            INSERT INTO signal_history
                (symbol, signal_type, confidence, price, stop_loss,
                 tp1, tp2, tp3, risk_reward, entry_quality, rvol,
                 trend, indicators, timeframe)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            symbol,
            signal_data.get("signal_type", "WAIT"),
            signal_data.get("confidence", 0),
            signal_data.get("price", 0),
            signal_data.get("stop_loss", 0),
            signal_data.get("tp1", 0),
            signal_data.get("tp2", 0),
            signal_data.get("tp3", 0),
            signal_data.get("risk_reward", 0),
            signal_data.get("entry_quality", 0),
            signal_data.get("rvol", 1.0),
            signal_data.get("trend", "SIDEWAYS"),
            json.dumps(signal_data.get("indicators", {})),
            signal_data.get("timeframe", "1h"),
        ))


def get_signal_history(symbol: str, limit: int = 10) -> List[Dict]:
    """Tanga signal tarixini olish."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM signal_history
            WHERE symbol = ?
            ORDER BY created_at DESC LIMIT ?
        """, (symbol, limit)).fetchall()
        return [dict(r) for r in rows]


# ============================================================
# SOZLAMALAR OPERATSIYALARI
# ============================================================

def get_settings(user_id: int) -> Dict:
    """Foydalanuvchi sozlamalarini olish."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM settings WHERE user_id = ?", (user_id,)
        ).fetchone()
        if row:
            return dict(row)
        # Standart sozlamalar
        return {
            "user_id": user_id,
            "alert_threshold": 70,
            "scan_interval": 600,
            "default_tf": "1h",
            "show_chart": 1,
            "notify_strong": 1,
            "notify_buy": 1,
            "notify_risk": 1,
        }


def update_setting(user_id: int, key: str, value: Any) -> None:
    """Foydalanuvchi sozlamasini yangilash."""
    with get_db() as conn:
        conn.execute("""
            INSERT INTO settings (user_id, {key})
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                {key} = excluded.{key},
                updated_at = CURRENT_TIMESTAMP
        """.format(key=key), (user_id, value))


# ============================================================
# KESH OPERATSIYALARI
# ============================================================

def cache_set(key: str, value: Any, ttl_seconds: int = 300) -> None:
    """Keshga ma'lumot saqlash."""
    expires_at = (datetime.utcnow() + timedelta(seconds=ttl_seconds)).isoformat()
    with get_db() as conn:
        conn.execute("""
            INSERT INTO cache (key, value, expires_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                expires_at = excluded.expires_at
        """, (key, json.dumps(value), expires_at))


def cache_get(key: str) -> Optional[Any]:
    """Keshdan ma'lumot olish."""
    with get_db() as conn:
        row = conn.execute("""
            SELECT value FROM cache
            WHERE key = ? AND expires_at > ?
        """, (key, datetime.utcnow().isoformat())).fetchone()
        if row:
            return json.loads(row["value"])
        return None


def cache_clear_expired() -> None:
    """Muddati o'tgan kesh yozuvlarini tozalash."""
    with get_db() as conn:
        conn.execute(
            "DELETE FROM cache WHERE expires_at <= ?",
            (datetime.utcnow().isoformat(),)
        )
