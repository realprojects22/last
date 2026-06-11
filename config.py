"""
config.py - HALOL CRYPTO AI BOT V3.5
Barcha konfiguratsiya sozlamalari va halol tangalar ro'yxati
"""

import os
from typing import List, Dict, Any
from dotenv import load_dotenv

# .env faylini yuklash
load_dotenv()


# ============================================================
# ASOSIY SOZLAMALAR
# ============================================================

TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
DB_NAME: str = os.getenv("DB_NAME", "halol_bot.db")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
SCAN_INTERVAL: int = int(os.getenv("SCAN_INTERVAL", "600"))
ALERT_THRESHOLD: int = int(os.getenv("ALERT_THRESHOLD", "70"))
CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))
MAX_WATCHLIST_SIZE: int = int(os.getenv("MAX_WATCHLIST_SIZE", "20"))
ALERT_COOLDOWN: int = int(os.getenv("ALERT_COOLDOWN", "3600"))
API_REQUEST_DELAY: float = float(os.getenv("API_REQUEST_DELAY", "100")) / 1000

# ============================================================
# SIGNAL KONFIGURATSIYASI
# ============================================================

SIGNALS = {
    "STRONG_BUY": {"emoji": "🔥", "name": "KUCHLI SOTIB OLISH", "min_score": 80},
    "BUY":        {"emoji": "🟢", "name": "SOTIB OLISH",         "min_score": 60},
    "WAIT":       {"emoji": "🟡", "name": "KUTISH",              "min_score": 40},
    "PROFIT":     {"emoji": "🔵", "name": "FOYDA OLISH",         "min_score": 0},
    "RISK":       {"emoji": "🟠", "name": "XAVF OSHDI",          "min_score": 0},
}

RISK_LEVELS = {
    "HIGH":   {"emoji": "🔴", "name": "XAVF YUQORI",  "max_score": 39},
    "MEDIUM": {"emoji": "🟡", "name": "O'RTA XAVF",   "max_score": 59},
    "LOW":    {"emoji": "🟢", "name": "PAST XAVF",    "max_score": 79},
    "VERY_LOW": {"emoji": "🔵", "name": "JUDA PAST XAVF", "max_score": 100},
}

# ============================================================
# RVOL CHEGARALARI
# ============================================================

RVOL_THRESHOLDS = {
    "EXCEPTIONAL": 3.0,
    "STRONG":      2.0,
    "NORMAL_LOW":  1.0,
}

# ============================================================
# VAQT ORALIQ SOZLAMALARI
# ============================================================

TIMEFRAMES = {
    "15m": {"interval": "15m", "limit": 200, "weight": 1.0},
    "1h":  {"interval": "1h",  "limit": 200, "weight": 1.5},
    "4h":  {"interval": "4h",  "limit": 200, "weight": 2.0},
    "1d":  {"interval": "1d",  "limit": 200, "weight": 3.0},
}

# ============================================================
# BINANCE API
# ============================================================

BINANCE_BASE_URL = "https://api.binance.com/api/v3"
BINANCE_KLINES_URL = f"{BINANCE_BASE_URL}/klines"
BINANCE_TICKER_URL = f"{BINANCE_BASE_URL}/ticker/24hr"
BINANCE_PRICE_URL  = f"{BINANCE_BASE_URL}/ticker/price"

# ============================================================
# HALOL TANGALAR RO'YXATI (SPOT FAQAT)
# ============================================================
# Leveraj tokenlar, futures mahsulotlar va shubhali tangalar
# bu ro'yxatdan chiqarib tashlangan.

HALAL_COINS: List[str] = [
    # ---- KATTA KAPITALIZATSIYA ----
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "AVAXUSDT",
    "ADAUSDT", "DOTUSDT", "LINKUSDT", "MATICUSDT", "LTCUSDT",
    "ATOMUSDT", "NEARUSDT", "ALGOUSDT", "VETUSDT", "XTZUSDT",
    "FTMUSDT", "SANDUSDT", "MANAUSDT", "AXSUSDT", "GALAUSDT",

    # ---- O'RTA KAPITALIZATSIYA ----
    "AAVEUSDT", "UNIUSDT", "CAKEUSDT", "SNXUSDT", "COMPUSDT",
    "MKRUSDT", "SUSHIUSDT", "YFIUSDT", "1INCHUSDT", "BALUSDT",
    "CRVUSDT", "LDOUSDT", "RPLUSDT", "STXUSDT", "EGLDUSDT",
    "FLOWUSDT", "IOTAUSDT", "XMRUSDT", "ZECUSDT", "DASHUSDT",

    # ---- INFRATUZILMA ----
    "OPUSDT", "ARBUSDT", "IMXUSDT", "APEUSDT", "GMTUSDT",
    "WOOUSDT", "GMXUSDT", "BLURUSDT", "SSVUSDT", "RNDRUSDT",
    "FETUSDT", "AGIXUSDT", "OCEANUSDT", "NFPUSDT", "WLDUSDT",

    # ---- LAYER 1 / LAYER 2 ----
    "APTUSDT", "SUIUSDT", "SEIUSDT", "INJUSDT", "TIAUSDT",
    "DYMUSDT", "ALTUSDT", "JUPUSDT", "STROUSDT", "PYTHUSDT",
    "JTOUSDT", "WIFUSDT", "BOMEUSDT", "TNSR",

    # ---- DEFI ----
    "RUNEUSDT", "OSMOUSDT", "JSTRUSDT", "ASTRUSDT", "KAVAUSDT",
    "BANDUSDT", "RSRUSDT", "ANKRUSDT", "CELOUSDT", "ONTUSDT",

    # ---- KICHIK KAPITALIZATSIYA (PAST XAVF) ----
    "HBARUSDT", "ICPUSDT", "FILUSDT", "ARUSDT", "THETAUSDT",
    "XRDUSDT", "MINAUSDT", "IOTXUSDT", "ZILLUSDT", "QNTUSDT",

    # ---- QIMMATLI TOKENLAR ----
    "ENAUSDT", "TAOUSDT", "NOTUSDT", "PIXELUSDT", "PORTALUSDT",
    "ACEUSDT", "XAIUSDT", "MANTAUSDT", "LSKUSDT", "AIUSDT",

    # ---- ISLOM PRINSIPLARIGA MOS ----
    "KASUSDT", "RENDERUSDT", "CFXUSDT", "SHIBUSDT", "PEPEUSDT",
]

# Chiqarib tashlangan tokenlar (leveraj, shubhali)
EXCLUDED_PATTERNS: List[str] = [
    "UPUSDT", "DOWNUSDT", "BULLUSDT", "BEARUSDT",
    "3LUSDT", "3SUSDT", "2LUSDT", "2SUSDT",
    "LEVERUSDT", "HALFUSDT",
]

# ============================================================
# STANDART KUZATUV RO'YXATI
# ============================================================

DEFAULT_WATCHLIST: List[str] = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "AVAXUSDT",
]

# ============================================================
# TEXNIK INDIKATOR PARAMETRLARI
# ============================================================

INDICATOR_PARAMS: Dict[str, Any] = {
    "RSI_PERIOD": 14,
    "EMA_SHORT": 20,
    "EMA_MID": 50,
    "EMA_LONG": 200,
    "MACD_FAST": 12,
    "MACD_SLOW": 26,
    "MACD_SIGNAL": 9,
    "ADX_PERIOD": 14,
    "BB_PERIOD": 20,
    "BB_STD": 2,
    "ATR_PERIOD": 14,
    "VOLUME_MA_PERIOD": 20,
    "OB_LOOKBACK": 10,
    "FVG_LOOKBACK": 5,
    "RVOL_PERIOD": 20,
    "SUPPORT_RESISTANCE_LOOKBACK": 50,
    "BREAKOUT_LOOKBACK": 20,
    "LIQUIDITY_LOOKBACK": 15,
}

# ============================================================
# GRAFIK SOZLAMALARI
# ============================================================

CHART_CONFIG: Dict[str, Any] = {
    "STYLE": "nightclouds",
    "FIGSIZE": (16, 12),
    "DPI": 100,
    "BACKGROUND_COLOR": "#0d1117",
    "GRID_COLOR": "#21262d",
    "TEXT_COLOR": "#e6edf3",
    "UP_COLOR": "#3fb950",
    "DOWN_COLOR": "#f85149",
    "EMA20_COLOR": "#79c0ff",
    "EMA50_COLOR": "#ffa657",
    "EMA200_COLOR": "#ff7b72",
    "SUPPORT_COLOR": "#3fb95066",
    "RESISTANCE_COLOR": "#f8514966",
    "OB_BULL_COLOR": "#3fb95033",
    "OB_BEAR_COLOR": "#f8514933",
    "FVG_COLOR": "#79c0ff22",
    "ENTRY_COLOR": "#58a6ff",
    "SL_COLOR": "#f85149",
    "TP1_COLOR": "#3fb950",
    "TP2_COLOR": "#7ee787",
    "TP3_COLOR": "#aff5b4",
}

# ============================================================
# BALL TIZIMI VAZNLARI
# ============================================================

SCORING_WEIGHTS: Dict[str, float] = {
    "trend_alignment":   20.0,
    "ema_alignment":     10.0,
    "rsi_bullish":       8.0,
    "macd_bullish":      8.0,
    "adx_strong":        5.0,
    "volume_strong":     8.0,
    "rvol_high":         7.0,
    "order_block":       8.0,
    "fvg_bullish":       5.0,
    "bos_bullish":       6.0,
    "choch_bullish":     6.0,
    "support_nearby":    5.0,
    "liquidity_sweep":   5.0,
    "breakout_retest":   7.0,
    "mtf_confirmation":  8.0,
    "bb_position":       4.0,
}

# Xavf jarimasi vaznlari
RISK_PENALTY_WEIGHTS: Dict[str, float] = {
    "resistance_nearby":   -8.0,
    "overbought_rsi":      -10.0,
    "weak_volume":         -8.0,
    "bearish_structure":   -12.0,
    "below_ema200":        -6.0,
    "low_rvol":            -5.0,
    "bearish_ob":          -5.0,
}

# ============================================================
# MENYU SOZLAMALARI
# ============================================================

MENU_ITEMS = {
    "signal":        "📊 Signal",
    "coin_analysis": "📈 Coin Tahlili",
    "watchlist":     "⭐ Watchlist",
    "strong_signals":"🚨 Kuchli Signallar",
    "ai_helper":     "📚 AI Yordamchi",
    "market_health": "📊 Bozor Holati",
    "top_opps":      "🏆 Eng Kuchli Imkoniyatlar",
    "ranking":       "📈 Reyting",
    "settings":      "⚙️ Sozlamalar",
    "help":          "ℹ️ Yordam",
}
