"""
utils.py - HALOL CRYPTO AI BOT V3.5
Yordamchi funksiyalar va formatlash vositalari
"""

import logging
import asyncio
import time
from typing import Optional, List, Tuple
from datetime import datetime

import aiohttp
import numpy as np

from config import (
    BINANCE_BASE_URL, BINANCE_KLINES_URL, BINANCE_TICKER_URL,
    API_REQUEST_DELAY, HALAL_COINS, EXCLUDED_PATTERNS
)

logger = logging.getLogger(__name__)


# ============================================================
# BINANCE API SO'ROVLARI
# ============================================================

async def fetch_klines(session: aiohttp.ClientSession, symbol: str,
                       interval: str, limit: int = 200) -> Optional[List]:
    """Binance'dan OHLCV ma'lumotlarini olish."""
    try:
        await asyncio.sleep(API_REQUEST_DELAY)
        url = f"{BINANCE_KLINES_URL}?symbol={symbol}&interval={interval}&limit={limit}"
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                logger.warning(f"Kline xatosi {symbol} {interval}: {resp.status}")
                return None
    except asyncio.TimeoutError:
        logger.warning(f"Timeout: {symbol} {interval}")
        return None
    except Exception as e:
        logger.error(f"Kline fetch xatosi {symbol}: {e}")
        return None


async def fetch_ticker(session: aiohttp.ClientSession,
                       symbol: str) -> Optional[dict]:
    """Binance'dan 24h ticker ma'lumotlarini olish."""
    try:
        url = f"{BINANCE_TICKER_URL}?symbol={symbol}"
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 200:
                return await resp.json()
            return None
    except Exception as e:
        logger.error(f"Ticker fetch xatosi {symbol}: {e}")
        return None


async def fetch_all_tickers(session: aiohttp.ClientSession) -> Optional[List]:
    """Barcha tickerlarni bir so'rovda olish."""
    try:
        url = BINANCE_TICKER_URL
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status == 200:
                return await resp.json()
            return None
    except Exception as e:
        logger.error(f"All tickers fetch xatosi: {e}")
        return None


# ============================================================
# NARX FORMATLASH
# ============================================================

def format_price(price: float) -> str:
    """Narxni o'qilishi qulay formatda ko'rsatish."""
    if price == 0:
        return "0"
    if price >= 1000:
        return f"{price:,.2f}"
    elif price >= 1:
        return f"{price:.4f}"
    elif price >= 0.01:
        return f"{price:.5f}"
    elif price >= 0.0001:
        return f"{price:.6f}"
    else:
        return f"{price:.8f}"


def format_pct(pct: float) -> str:
    """Foizni formatlash."""
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.2f}%"


def format_volume(vol: float) -> str:
    """Hajmni formatlash (K, M, B)."""
    if vol >= 1_000_000_000:
        return f"{vol / 1_000_000_000:.2f}B"
    elif vol >= 1_000_000:
        return f"{vol / 1_000_000:.2f}M"
    elif vol >= 1_000:
        return f"{vol / 1_000:.2f}K"
    else:
        return f"{vol:.2f}"


def get_symbol_base(symbol: str) -> str:
    """BTCUSDT -> BTC."""
    for quote in ["USDT", "BTC", "ETH", "BNB"]:
        if symbol.endswith(quote):
            return symbol[: -len(quote)]
    return symbol


# ============================================================
# HALOLLIK TEKSHIRUVI
# ============================================================

def is_halal_symbol(symbol: str) -> bool:
    """Tanganing halol va qo'llab-quvvatlanishini tekshirish."""
    symbol_upper = symbol.upper()
    for pattern in EXCLUDED_PATTERNS:
        if pattern in symbol_upper:
            return False
    return symbol_upper in [s.upper() for s in HALAL_COINS]


def normalize_symbol(symbol: str) -> str:
    """Tanga belgisini normallashtirish."""
    symbol = symbol.upper().strip()
    if not symbol.endswith("USDT"):
        symbol = symbol + "USDT"
    return symbol


# ============================================================
# NUMPY YORDAMCHI FUNKSIYALARI
# ============================================================

def safe_float(value, default: float = 0.0) -> float:
    """Xavfsiz float konvertatsiya."""
    try:
        f = float(value)
        return f if not (np.isnan(f) or np.isinf(f)) else default
    except (TypeError, ValueError):
        return default


def ema(data: np.ndarray, period: int) -> np.ndarray:
    """Eksponensial harakatlanuvchi o'rtacha hisoblash."""
    result = np.zeros(len(data))
    if len(data) < period:
        return result
    multiplier = 2.0 / (period + 1)
    result[period - 1] = np.mean(data[:period])
    for i in range(period, len(data)):
        result[i] = (data[i] - result[i - 1]) * multiplier + result[i - 1]
    return result


def sma(data: np.ndarray, period: int) -> np.ndarray:
    """Oddiy harakatlanuvchi o'rtacha hisoblash."""
    result = np.full(len(data), np.nan)
    for i in range(period - 1, len(data)):
        result[i] = np.mean(data[i - period + 1: i + 1])
    return result


def rsi(close: np.ndarray, period: int = 14) -> np.ndarray:
    """RSI hisoblash."""
    if len(close) < period + 1:
        return np.zeros(len(close))
    deltas = np.diff(close)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    avg_gain = np.zeros(len(close))
    avg_loss = np.zeros(len(close))
    avg_gain[period] = np.mean(gains[:period])
    avg_loss[period] = np.mean(losses[:period])

    for i in range(period + 1, len(close)):
        avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gains[i - 1]) / period
        avg_loss[i] = (avg_loss[i - 1] * (period - 1) + losses[i - 1]) / period

    rs = np.where(avg_loss != 0, avg_gain / avg_loss, 100.0)
    rsi_values = np.where(avg_loss == 0, 100.0, 100.0 - (100.0 / (1.0 + rs)))
    return rsi_values


def atr(high: np.ndarray, low: np.ndarray, close: np.ndarray,
        period: int = 14) -> np.ndarray:
    """ATR hisoblash."""
    if len(high) < 2:
        return np.zeros(len(high))
    tr = np.maximum(
        high[1:] - low[1:],
        np.maximum(
            np.abs(high[1:] - close[:-1]),
            np.abs(low[1:] - close[:-1])
        )
    )
    atr_values = np.zeros(len(high))
    if len(tr) >= period:
        atr_values[period] = np.mean(tr[:period])
        for i in range(period + 1, len(high)):
            atr_values[i] = (atr_values[i - 1] * (period - 1) + tr[i - 1]) / period
    return atr_values


def adx(high: np.ndarray, low: np.ndarray, close: np.ndarray,
        period: int = 14) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """ADX, +DI, -DI hisoblash."""
    n = len(high)
    if n < period + 1:
        return np.zeros(n), np.zeros(n), np.zeros(n)

    plus_dm = np.zeros(n)
    minus_dm = np.zeros(n)
    tr_arr = np.zeros(n)

    for i in range(1, n):
        h_diff = high[i] - high[i - 1]
        l_diff = low[i - 1] - low[i]
        plus_dm[i] = h_diff if (h_diff > l_diff and h_diff > 0) else 0
        minus_dm[i] = l_diff if (l_diff > h_diff and l_diff > 0) else 0
        tr_arr[i] = max(high[i] - low[i],
                        abs(high[i] - close[i - 1]),
                        abs(low[i] - close[i - 1]))

    atr14 = np.zeros(n)
    sm_plus = np.zeros(n)
    sm_minus = np.zeros(n)

    atr14[period] = np.sum(tr_arr[1: period + 1])
    sm_plus[period] = np.sum(plus_dm[1: period + 1])
    sm_minus[period] = np.sum(minus_dm[1: period + 1])

    for i in range(period + 1, n):
        atr14[i] = atr14[i - 1] - atr14[i - 1] / period + tr_arr[i]
        sm_plus[i] = sm_plus[i - 1] - sm_plus[i - 1] / period + plus_dm[i]
        sm_minus[i] = sm_minus[i - 1] - sm_minus[i - 1] / period + minus_dm[i]

    di_plus = np.where(atr14 > 0, 100 * sm_plus / atr14, 0)
    di_minus = np.where(atr14 > 0, 100 * sm_minus / atr14, 0)
    di_diff = np.abs(di_plus - di_minus)
    di_sum = di_plus + di_minus
    dx = np.where(di_sum > 0, 100 * di_diff / di_sum, 0)

    adx_values = np.zeros(n)
    start = 2 * period
    if n > start:
        adx_values[start] = np.mean(dx[period: start + 1])
        for i in range(start + 1, n):
            adx_values[i] = (adx_values[i - 1] * (period - 1) + dx[i]) / period

    return adx_values, di_plus, di_minus


def bollinger_bands(close: np.ndarray, period: int = 20,
                    std_dev: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Bollinger Bands hisoblash."""
    mid = sma(close, period)
    std = np.array([
        np.std(close[max(0, i - period + 1): i + 1])
        if i >= period - 1 else np.nan
        for i in range(len(close))
    ])
    upper = mid + std_dev * std
    lower = mid - std_dev * std
    return upper, mid, lower


def macd(close: np.ndarray, fast: int = 12, slow: int = 26,
         signal: int = 9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """MACD hisoblash."""
    ema_fast = ema(close, fast)
    ema_slow = ema(close, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


# ============================================================
# VAQT FORMATLASH
# ============================================================

def now_str() -> str:
    """Hozirgi vaqtni string ko'rinishida qaytarish."""
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")


def timestamp_to_str(ts_ms: int) -> str:
    """Millisekund timestampni string ko'rinishiga o'tkazish."""
    dt = datetime.utcfromtimestamp(ts_ms / 1000)
    return dt.strftime("%Y-%m-%d %H:%M")


# ============================================================
# KUZATUV YORDAMCHISI
# ============================================================

def setup_logging(level: str = "INFO") -> None:
    """Logging tizimini sozlash."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
