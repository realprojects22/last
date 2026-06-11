"""
signals.py - HALOL CRYPTO AI BOT V3.5
Texnik tahlil va signal yaratish mexanizmi
Spot savdo faqat — futures, leveraj, short pozitsiyalar yo'q
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

from config import (
    INDICATOR_PARAMS, SCORING_WEIGHTS, RISK_PENALTY_WEIGHTS,
    TIMEFRAMES, RVOL_THRESHOLDS
)
from utils import (
    ema, sma, rsi as calc_rsi, atr as calc_atr,
    adx as calc_adx, bollinger_bands, macd as calc_macd,
    safe_float
)

logger = logging.getLogger(__name__)

P = INDICATOR_PARAMS


# ============================================================
# MA'LUMOTLAR TUZILMALARI
# ============================================================

@dataclass
class OHLCV:
    """Mum (candle) ma'lumotlari."""
    open:   np.ndarray = field(default_factory=lambda: np.array([]))
    high:   np.ndarray = field(default_factory=lambda: np.array([]))
    low:    np.ndarray = field(default_factory=lambda: np.array([]))
    close:  np.ndarray = field(default_factory=lambda: np.array([]))
    volume: np.ndarray = field(default_factory=lambda: np.array([]))
    times:  np.ndarray = field(default_factory=lambda: np.array([]))

    @property
    def length(self) -> int:
        return len(self.close)

    @property
    def last_close(self) -> float:
        return float(self.close[-1]) if self.length > 0 else 0.0

    @property
    def last_volume(self) -> float:
        return float(self.volume[-1]) if self.length > 0 else 0.0


@dataclass
class Indicators:
    """Hisoblangan indikatorlar."""
    rsi: float = 50.0
    ema20: float = 0.0
    ema50: float = 0.0
    ema200: float = 0.0
    macd_line: float = 0.0
    macd_signal: float = 0.0
    macd_hist: float = 0.0
    adx: float = 0.0
    di_plus: float = 0.0
    di_minus: float = 0.0
    bb_upper: float = 0.0
    bb_mid: float = 0.0
    bb_lower: float = 0.0
    atr: float = 0.0
    volume_ma: float = 0.0
    rvol: float = 1.0


@dataclass
class MarketStructure:
    """Bozor tuzilmasi."""
    trend: str = "SIDEWAYS"          # BULLISH / BEARISH / SIDEWAYS
    higher_highs: bool = False
    higher_lows: bool = False
    lower_highs: bool = False
    lower_lows: bool = False
    support: float = 0.0
    resistance: float = 0.0
    order_block_bull: Optional[Tuple[float, float]] = None
    order_block_bear: Optional[Tuple[float, float]] = None
    fvg_bull: Optional[Tuple[float, float]] = None
    fvg_bear: Optional[Tuple[float, float]] = None
    bos_bullish: bool = False
    choch_bullish: bool = False
    liquidity_sweep_bull: bool = False
    liquidity_sweep_bear: bool = False
    breakout_detected: bool = False
    retest_confirmed: bool = False


@dataclass
class SignalResult:
    """To'liq signal natijasi."""
    symbol: str = ""
    signal_type: str = "WAIT"
    confidence: int = 0
    entry_quality: int = 0
    risk_level: str = "HIGH"
    price: float = 0.0
    change_24h: float = 0.0
    stop_loss: float = 0.0
    tp1: float = 0.0
    tp2: float = 0.0
    tp3: float = 0.0
    risk_reward: float = 0.0
    rvol: float = 1.0
    trend: str = "SIDEWAYS"
    indicators: Dict = field(default_factory=dict)
    structure: Dict = field(default_factory=dict)
    reasoning: List[str] = field(default_factory=list)
    timeframe: str = "1h"


# ============================================================
# OHLCV PARSE
# ============================================================

def parse_klines(raw: List) -> Optional[OHLCV]:
    """Binance kline javobini OHLCV ga aylantirish."""
    if not raw or len(raw) < 20:
        return None
    try:
        data = OHLCV(
            open=np.array([safe_float(k[1]) for k in raw]),
            high=np.array([safe_float(k[2]) for k in raw]),
            low=np.array([safe_float(k[3]) for k in raw]),
            close=np.array([safe_float(k[4]) for k in raw]),
            volume=np.array([safe_float(k[5]) for k in raw]),
            times=np.array([int(k[0]) for k in raw]),
        )
        return data
    except Exception as e:
        logger.error(f"Kline parse xatosi: {e}")
        return None


# ============================================================
# INDIKATOR HISOBLASH
# ============================================================

def compute_indicators(ohlcv: OHLCV) -> Indicators:
    """Barcha texnik indikatorlarni hisoblash."""
    c = ohlcv.close
    h = ohlcv.high
    lo = ohlcv.low
    v = ohlcv.volume
    n = ohlcv.length

    ind = Indicators()

    # RSI
    rsi_arr = calc_rsi(c, P["RSI_PERIOD"])
    ind.rsi = safe_float(rsi_arr[-1], 50.0)

    # EMA
    ema20_arr = ema(c, P["EMA_SHORT"])
    ema50_arr = ema(c, P["EMA_MID"])
    ema200_arr = ema(c, P["EMA_LONG"])
    ind.ema20 = safe_float(ema20_arr[-1])
    ind.ema50 = safe_float(ema50_arr[-1])
    ind.ema200 = safe_float(ema200_arr[-1])

    # MACD
    macd_line, macd_sig, macd_hist = calc_macd(
        c, P["MACD_FAST"], P["MACD_SLOW"], P["MACD_SIGNAL"]
    )
    ind.macd_line = safe_float(macd_line[-1])
    ind.macd_signal = safe_float(macd_sig[-1])
    ind.macd_hist = safe_float(macd_hist[-1])

    # ADX
    adx_arr, dip, dim = calc_adx(h, lo, c, P["ADX_PERIOD"])
    ind.adx = safe_float(adx_arr[-1])
    ind.di_plus = safe_float(dip[-1])
    ind.di_minus = safe_float(dim[-1])

    # Bollinger Bands
    bb_up, bb_mid, bb_low = bollinger_bands(c, P["BB_PERIOD"], P["BB_STD"])
    ind.bb_upper = safe_float(bb_up[-1])
    ind.bb_mid = safe_float(bb_mid[-1])
    ind.bb_lower = safe_float(bb_low[-1])

    # ATR
    atr_arr = calc_atr(h, lo, c, P["ATR_PERIOD"])
    ind.atr = safe_float(atr_arr[-1])

    # Volume MA & RVOL
    vol_period = P["VOLUME_MA_PERIOD"]
    if n >= vol_period:
        ind.volume_ma = safe_float(np.mean(v[-vol_period:]))
        if ind.volume_ma > 0:
            ind.rvol = safe_float(v[-1] / ind.volume_ma, 1.0)

    return ind


# ============================================================
# BOZOR TUZILMASI TAHLILI
# ============================================================

def analyze_market_structure(ohlcv: OHLCV) -> MarketStructure:
    """Smart Money kontseptsiyalarini va bozor tuzilmasini tahlil qilish."""
    ms = MarketStructure()
    c = ohlcv.close
    h = ohlcv.high
    lo = ohlcv.low
    n = ohlcv.length

    if n < 30:
        return ms

    # ---- Yuqori / Pastki Nuqtalar ----
    lookback = min(P["SUPPORT_RESISTANCE_LOOKBACK"], n - 1)
    recent_highs = h[-lookback:]
    recent_lows = lo[-lookback:]

    # Swing nuqtalarini aniqlash (oddiy lokal ekstremal)
    swings_h = _find_swings(recent_highs, mode="high")
    swings_l = _find_swings(recent_lows, mode="low")

    if len(swings_h) >= 2:
        ms.higher_highs = swings_h[-1] > swings_h[-2]
        ms.lower_highs = swings_h[-1] < swings_h[-2]

    if len(swings_l) >= 2:
        ms.higher_lows = swings_l[-1] > swings_l[-2]
        ms.lower_lows = swings_l[-1] < swings_l[-2]

    # ---- Trend Aniqlash ----
    if ms.higher_highs and ms.higher_lows:
        ms.trend = "BULLISH"
    elif ms.lower_highs and ms.lower_lows:
        ms.trend = "BEARISH"
    else:
        ms.trend = "SIDEWAYS"

    # ---- Support & Resistance ----
    ms.support = safe_float(np.min(lo[-lookback:]))
    ms.resistance = safe_float(np.max(h[-lookback:]))

    # O'rta oraliq support/resistance
    pivot = float(c[-1])
    mid_range = (ms.resistance - ms.support) / 4
    ms.support = ms.resistance - 3 * mid_range
    ms.resistance = ms.support + 3 * mid_range

    # Real support/resistance: lokal minimumlar/maksimumlar
    ms.support = _find_nearest_support(lo, c[-1])
    ms.resistance = _find_nearest_resistance(h, c[-1])

    # ---- Order Blocks ----
    ob_lb = P["OB_LOOKBACK"]
    ms.order_block_bull = _detect_bullish_ob(ohlcv, ob_lb)
    ms.order_block_bear = _detect_bearish_ob(ohlcv, ob_lb)

    # ---- Fair Value Gaps ----
    fvg_lb = P["FVG_LOOKBACK"]
    ms.fvg_bull = _detect_fvg(ohlcv, fvg_lb, bullish=True)
    ms.fvg_bear = _detect_fvg(ohlcv, fvg_lb, bullish=False)

    # ---- BOS & CHoCH ----
    ms.bos_bullish = _detect_bos(ohlcv, bullish=True)
    ms.choch_bullish = _detect_choch(ohlcv)

    # ---- Liquidity Sweeps ----
    liq_lb = P["LIQUIDITY_LOOKBACK"]
    ms.liquidity_sweep_bull = _detect_liquidity_sweep(ohlcv, liq_lb, bullish=True)
    ms.liquidity_sweep_bear = _detect_liquidity_sweep(ohlcv, liq_lb, bullish=False)

    # ---- Breakout & Retest ----
    ms.breakout_detected, ms.retest_confirmed = _detect_breakout_retest(
        ohlcv, P["BREAKOUT_LOOKBACK"]
    )

    return ms


def _find_swings(arr: np.ndarray, mode: str = "high", window: int = 5) -> List[float]:
    """Lokal swing nuqtalarini topish."""
    swings = []
    for i in range(window, len(arr) - window):
        seg = arr[i - window: i + window + 1]
        if mode == "high" and arr[i] == np.max(seg):
            swings.append(float(arr[i]))
        elif mode == "low" and arr[i] == np.min(seg):
            swings.append(float(arr[i]))
    return swings


def _find_nearest_support(low: np.ndarray, current_price: float,
                           lookback: int = 50) -> float:
    """Eng yaqin support darajasini topish."""
    lows = low[-lookback:]
    candidates = []
    for i in range(2, len(lows) - 2):
        if lows[i] < lows[i - 1] and lows[i] < lows[i + 1] and lows[i] < current_price:
            candidates.append(float(lows[i]))
    if not candidates:
        return float(np.min(lows))
    return max(candidates)  # Eng yaqin pastki support


def _find_nearest_resistance(high: np.ndarray, current_price: float,
                              lookback: int = 50) -> float:
    """Eng yaqin resistance darajasini topish."""
    highs = high[-lookback:]
    candidates = []
    for i in range(2, len(highs) - 2):
        if highs[i] > highs[i - 1] and highs[i] > highs[i + 1] and highs[i] > current_price:
            candidates.append(float(highs[i]))
    if not candidates:
        return float(np.max(highs))
    return min(candidates)  # Eng yaqin yuqori resistance


def _detect_bullish_ob(ohlcv: OHLCV, lookback: int) -> Optional[Tuple[float, float]]:
    """Bullish Order Block aniqlash (kuchli pastga tushishdan oldingi qizil mum)."""
    o, h, lo, c = ohlcv.open, ohlcv.high, ohlcv.low, ohlcv.close
    n = min(lookback, ohlcv.length - 2)
    for i in range(ohlcv.length - 2, ohlcv.length - n - 1, -1):
        # Keyingi mum kuchli yuqoriga ko'tarilishi va o'tgan mum ayiqli bo'lishi
        if i + 1 < ohlcv.length:
            next_bullish = c[i + 1] > o[i + 1] and (c[i + 1] - o[i + 1]) > (h[i + 1] - lo[i + 1]) * 0.5
            curr_bearish = c[i] < o[i]
            if next_bullish and curr_bearish:
                return (float(lo[i]), float(o[i]))
    return None


def _detect_bearish_ob(ohlcv: OHLCV, lookback: int) -> Optional[Tuple[float, float]]:
    """Bearish Order Block aniqlash."""
    o, h, lo, c = ohlcv.open, ohlcv.high, ohlcv.low, ohlcv.close
    n = min(lookback, ohlcv.length - 2)
    for i in range(ohlcv.length - 2, ohlcv.length - n - 1, -1):
        if i + 1 < ohlcv.length:
            next_bearish = c[i + 1] < o[i + 1] and (o[i + 1] - c[i + 1]) > (h[i + 1] - lo[i + 1]) * 0.5
            curr_bullish = c[i] > o[i]
            if next_bearish and curr_bullish:
                return (float(o[i]), float(h[i]))
    return None


def _detect_fvg(ohlcv: OHLCV, lookback: int,
                bullish: bool = True) -> Optional[Tuple[float, float]]:
    """Fair Value Gap aniqlash (3 mumlik tuzilma)."""
    h = ohlcv.high
    lo = ohlcv.low
    n = min(lookback, ohlcv.length - 3)
    for i in range(ohlcv.length - 3, ohlcv.length - n - 2, -1):
        if bullish:
            # Bullish FVG: [i] pastki - [i+2] yuqori orasida bo'sh joy
            if lo[i + 2] > h[i]:
                return (float(h[i]), float(lo[i + 2]))
        else:
            # Bearish FVG: [i] yuqori - [i+2] pastki orasida bo'sh joy
            if h[i + 2] < lo[i]:
                return (float(h[i + 2]), float(lo[i]))
    return None


def _detect_bos(ohlcv: OHLCV, bullish: bool = True) -> bool:
    """Break of Structure aniqlash."""
    if ohlcv.length < 20:
        return False
    h = ohlcv.high
    lo = ohlcv.low
    if bullish:
        # So'nggi past yuksakni sinib o'tish
        prev_high = np.max(h[-20:-5])
        return float(h[-1]) > prev_high or float(h[-2]) > prev_high
    else:
        prev_low = np.min(lo[-20:-5])
        return float(lo[-1]) < prev_low or float(lo[-2]) < prev_low


def _detect_choch(ohlcv: OHLCV) -> bool:
    """Change of Character aniqlash (trendi o'zgarishi)."""
    if ohlcv.length < 30:
        return False
    c = ohlcv.close
    lo = ohlcv.low
    h = ohlcv.high

    # Pastga tushish tendentsiyasida yuqoriroq past paydo bo'lishi
    recent_low = np.min(lo[-10:])
    prev_low = np.min(lo[-20:-10])
    recent_high = np.max(h[-10:])
    prev_high = np.max(h[-20:-10])

    # Ayiqli trenddan bullish CHoCH
    return bool(recent_low > prev_low and recent_high > prev_high)


def _detect_liquidity_sweep(ohlcv: OHLCV, lookback: int,
                             bullish: bool = True) -> bool:
    """Likvidlik oqimi aniqlash."""
    if ohlcv.length < lookback + 5:
        return False
    h = ohlcv.high
    lo = ohlcv.low
    c = ohlcv.close

    if bullish:
        # Past support darajasini qisqa muddatga sinib, tez qaytish
        prev_low = np.min(lo[-(lookback + 5):-5])
        recent_low = np.min(lo[-5:])
        recent_close = float(c[-1])
        # Narx pastga tushdi, lekin tez qaytdi
        return bool(recent_low < prev_low and recent_close > prev_low)
    else:
        # Yuqori resistance darajasini sinib, tez qaytish
        prev_high = np.max(h[-(lookback + 5):-5])
        recent_high = np.max(h[-5:])
        recent_close = float(c[-1])
        return bool(recent_high > prev_high and recent_close < prev_high)


def _detect_breakout_retest(ohlcv: OHLCV,
                             lookback: int) -> Tuple[bool, bool]:
    """Breakout va retest aniqlash."""
    if ohlcv.length < lookback + 10:
        return False, False
    h = ohlcv.high
    lo = ohlcv.low
    c = ohlcv.close

    resistance = np.max(h[-(lookback + 10):-10])
    current_close = float(c[-1])
    recent_high = float(np.max(h[-5:]))
    recent_low = float(np.min(lo[-5:]))

    breakout = recent_high > resistance
    if breakout:
        # Retest: narx resistance darajasiga qaytib, yuqori yopildi
        retest = bool(recent_low <= resistance * 1.02 and current_close > resistance * 0.99)
        return True, retest
    return False, False


# ============================================================
# CONFIDENCE BALL HISOBLASH
# ============================================================

def compute_confidence(ind: Indicators, ms: MarketStructure,
                       price: float) -> Tuple[int, int, List[str]]:
    """
    Ishonch ballini, entry sifat ballini va asoslarni hisoblash.
    Qaytaradi: (confidence_0_100, entry_quality_0_100, [reasoning])
    """
    score = 0.0
    reasoning = []
    w = SCORING_WEIGHTS
    p = RISK_PENALTY_WEIGHTS

    # ---- TREND ALIGNMENT ----
    if ms.trend == "BULLISH":
        score += w["trend_alignment"]
        reasoning.append("✅ Bullish trend aniqlandi")
    elif ms.trend == "BEARISH":
        score += p["bearish_structure"]
        reasoning.append("⚠️ Bearish trend — xavf yuqori")

    # ---- EMA ALIGNMENT ----
    ema_bull = (ind.ema20 > ind.ema50 > ind.ema200 and price > ind.ema200)
    ema_bear = (ind.ema20 < ind.ema50 < ind.ema200)
    if ema_bull:
        score += w["ema_alignment"]
        reasoning.append("✅ EMA20 > EMA50 > EMA200 — bullish joylashuv")
    elif price < ind.ema200 and ind.ema200 > 0:
        score += p["below_ema200"]
        reasoning.append("⚠️ Narx EMA200 dan past")

    # ---- RSI ----
    if 40 <= ind.rsi <= 60:
        score += w["rsi_bullish"] * 0.5
        reasoning.append(f"✅ RSI neytral: {ind.rsi:.1f}")
    elif 55 <= ind.rsi <= 70:
        score += w["rsi_bullish"]
        reasoning.append(f"✅ RSI bullish: {ind.rsi:.1f}")
    elif ind.rsi > 70:
        score += p["overbought_rsi"]
        reasoning.append(f"⚠️ RSI haddan tashqari yuqori: {ind.rsi:.1f}")
    elif ind.rsi < 30:
        score += w["rsi_bullish"] * 0.7
        reasoning.append(f"✅ RSI haddan tashqari past — tiklash mumkin: {ind.rsi:.1f}")

    # ---- MACD ----
    if ind.macd_hist > 0 and ind.macd_line > ind.macd_signal:
        score += w["macd_bullish"]
        reasoning.append("✅ MACD bullish — momentum ijobiy")
    elif ind.macd_hist > 0:
        score += w["macd_bullish"] * 0.5
        reasoning.append("✅ MACD histogramm ijobiy")

    # ---- ADX ----
    if ind.adx >= 25 and ind.di_plus > ind.di_minus:
        score += w["adx_strong"]
        reasoning.append(f"✅ ADX kuchli trend: {ind.adx:.1f}, +DI > -DI")
    elif ind.adx >= 20:
        score += w["adx_strong"] * 0.5

    # ---- VOLUME ----
    if ind.rvol >= RVOL_THRESHOLDS["STRONG"]:
        score += w["volume_strong"]
        reasoning.append(f"✅ Kuchli hajm — RVOL: {ind.rvol:.2f}x")
    elif ind.rvol >= RVOL_THRESHOLDS["NORMAL_LOW"]:
        score += w["volume_strong"] * 0.5
    else:
        score += p["weak_volume"]
        reasoning.append(f"⚠️ Zaif hajm — RVOL: {ind.rvol:.2f}x")

    # ---- RVOL ----
    if ind.rvol >= RVOL_THRESHOLDS["EXCEPTIONAL"]:
        score += w["rvol_high"]
        reasoning.append(f"🔥 Istisnoli hajm — RVOL: {ind.rvol:.2f}x")
    elif ind.rvol >= RVOL_THRESHOLDS["STRONG"]:
        score += w["rvol_high"] * 0.7

    # ---- ORDER BLOCKS ----
    if ms.order_block_bull and price > 0:
        ob_low, ob_high = ms.order_block_bull
        if ob_low <= price <= ob_high * 1.05:
            score += w["order_block"]
            reasoning.append("✅ Bullish Order Block zonasida")
    if ms.order_block_bear:
        ob_low, ob_high = ms.order_block_bear
        if ob_low <= price <= ob_high:
            score += p.get("bearish_ob", -5.0)
            reasoning.append("⚠️ Bearish Order Block yaqinida")

    # ---- FVG ----
    if ms.fvg_bull and price > 0:
        fvg_low, fvg_high = ms.fvg_bull
        if fvg_low <= price <= fvg_high:
            score += w["fvg_bullish"]
            reasoning.append("✅ Bullish FVG zonasida")

    # ---- BOS ----
    if ms.bos_bullish:
        score += w["bos_bullish"]
        reasoning.append("✅ Bullish BOS aniqlandi")

    # ---- CHOCH ----
    if ms.choch_bullish:
        score += w["choch_bullish"]
        reasoning.append("✅ Bullish CHoCH — trend o'zgarishi")

    # ---- SUPPORT ----
    if ms.support > 0 and price > 0:
        dist_to_support = (price - ms.support) / price
        if 0 < dist_to_support <= 0.03:
            score += w["support_nearby"]
            reasoning.append("✅ Support darajasiga yaqin kirish")

    # ---- RESISTANCE ----
    if ms.resistance > 0 and price > 0:
        dist_to_resistance = (ms.resistance - price) / price
        if 0 < dist_to_resistance <= 0.02:
            score += p["resistance_nearby"]
            reasoning.append("⚠️ Resistance yaqinida — chiqish xavfi")

    # ---- LIQUIDITY SWEEP ----
    if ms.liquidity_sweep_bull:
        score += w["liquidity_sweep"]
        reasoning.append("✅ Bullish likvidlik oqimi — kuchli ishlat")
    if ms.liquidity_sweep_bear:
        score += -w["liquidity_sweep"]
        reasoning.append("⚠️ Bearish likvidlik oqimi")

    # ---- BREAKOUT & RETEST ----
    if ms.breakout_detected and ms.retest_confirmed:
        score += w["breakout_retest"]
        reasoning.append("✅ Breakout va muvaffaqiyatli retest tasdiqlandi")
    elif ms.breakout_detected:
        score += w["breakout_retest"] * 0.4
        reasoning.append("⚠️ Breakout aniqlandi — retest kutilmoqda")

    # ---- BOLLINGER BANDS ----
    if ind.bb_lower > 0 and price > 0:
        bb_range = ind.bb_upper - ind.bb_lower
        if bb_range > 0:
            bb_pos = (price - ind.bb_lower) / bb_range
            if 0.3 <= bb_pos <= 0.6:
                score += w["bb_position"]
                reasoning.append("✅ Bollinger Bands o'rta zonasida")

    # Ball oraliq chegaralash
    confidence = max(0, min(100, int(score)))

    # ---- ENTRY QUALITY SCORE ----
    eq_factors = [
        ms.trend == "BULLISH",
        ema_bull,
        ind.rvol >= RVOL_THRESHOLDS["NORMAL_LOW"],
        ms.order_block_bull is not None,
        ms.fvg_bull is not None,
        ms.bos_bullish,
        ms.choch_bullish,
        ms.liquidity_sweep_bull,
        ms.breakout_detected and ms.retest_confirmed,
        ind.adx >= 25 and ind.di_plus > ind.di_minus,
    ]
    eq_score = int(sum(eq_factors) / len(eq_factors) * 100)

    return confidence, eq_score, reasoning


# ============================================================
# RISK BOSHQARUVI
# ============================================================

def compute_risk_levels(price: float, ind: Indicators,
                        ms: MarketStructure) -> Tuple[float, float, float, float, float]:
    """
    Stop Loss va Take Profit darajalarini hisoblash.
    Qaytaradi: (stop_loss, tp1, tp2, tp3, risk_reward)
    """
    atr_val = ind.atr if ind.atr > 0 else price * 0.02

    # ---- STOP LOSS ----
    # ATR asosida, support darajasini hisobga olgan holda
    sl_atr = price - (atr_val * 1.5)
    sl_support = ms.support * 0.99 if ms.support > 0 else sl_atr

    # Order Block pastki darajasi
    sl_ob = 0.0
    if ms.order_block_bull:
        ob_low, _ = ms.order_block_bull
        sl_ob = ob_low * 0.99

    # Eng yuqori stop lossni tanlash (narxga eng yaqin)
    sl_candidates = [c for c in [sl_atr, sl_support, sl_ob] if c > 0]
    stop_loss = max(sl_candidates) if sl_candidates else sl_atr
    stop_loss = min(stop_loss, price * 0.97)  # Kamida 3% past

    # ---- TAKE PROFIT ----
    risk = price - stop_loss
    if risk <= 0:
        risk = price * 0.02

    # TP darajalar: resistance va R:R nisbatiga asoslangan
    resistance = ms.resistance if ms.resistance > price else price * 1.10

    tp1_rr = price + risk * 1.5
    tp2_rr = price + risk * 2.5
    tp3_rr = price + risk * 4.0

    # Resistance chegarasini hisobga olish
    tp1 = min(tp1_rr, resistance * 0.98)
    tp2 = min(tp2_rr, resistance * 1.05)
    tp3 = tp3_rr  # Tajovuzkor maqsad

    # TP1 pastki chegarasi
    tp1 = max(tp1, price + risk * 1.2)

    # FVG zonasini hisobga olish
    if ms.fvg_bull:
        fvg_low, fvg_high = ms.fvg_bull
        if fvg_high > price:
            tp1 = max(tp1, fvg_high)

    # Risk:Reward nisbati
    risk_reward = round((tp2 - price) / risk, 2) if risk > 0 else 0.0

    return stop_loss, tp1, tp2, tp3, risk_reward


# ============================================================
# SIGNAL TURI ANIQLASH
# ============================================================

def determine_signal_type(confidence: int, ms: MarketStructure) -> str:
    """Confidence ball va tuzilmaga asosida signal turini aniqlash.
    
    MUHIM: Short, futures, leveraj signallari HECH QACHON yaratilmaydi.
    Bearish sharoitlarda FOYDA_OLISH yoki XAVF_OSHDI qaytariladi.
    """
    if ms.trend == "BEARISH" or confidence < 40:
        if confidence < 30:
            return "RISK"
        return "PROFIT"

    if confidence >= 80:
        return "STRONG_BUY"
    elif confidence >= 60:
        return "BUY"
    elif confidence >= 40:
        return "WAIT"
    else:
        return "PROFIT"


def determine_risk_level(confidence: int) -> str:
    """Risk darajasini aniqlash."""
    if confidence >= 80:
        return "VERY_LOW"
    elif confidence >= 60:
        return "LOW"
    elif confidence >= 40:
        return "MEDIUM"
    else:
        return "HIGH"


# ============================================================
# KO'P VAQT ORALIG'I TAHLILI
# ============================================================

def combine_mtf_signals(signals: Dict[str, int]) -> Tuple[int, List[str]]:
    """Ko'p vaqt oralig'i signallarini birlashtirish."""
    weights = {
        "15m": 1.0,
        "1h":  1.5,
        "4h":  2.0,
        "1d":  3.0,
    }
    total_weight = 0.0
    weighted_sum = 0.0
    reasoning = []

    for tf, score in signals.items():
        w = weights.get(tf, 1.0)
        weighted_sum += score * w
        total_weight += w

    if total_weight == 0:
        return 0, []

    combined = int(weighted_sum / total_weight)

    # MTF moslik tekshiruvi
    scores = list(signals.values())
    if all(s >= 60 for s in scores):
        combined = min(100, combined + 8)
        reasoning.append("✅ Barcha vaqt oraliqlarida moslik")
    elif all(s >= 40 for s in scores):
        combined = min(100, combined + 4)
        reasoning.append("✅ Ko'p vaqt oraliqlarida moslik")

    return combined, reasoning


# ============================================================
# BOZOR SALOMATLIGI HISOBLASH
# ============================================================

def compute_market_health(all_signals: List[SignalResult]) -> Dict:
    """Global bozor sog'lomligini hisoblash."""
    if not all_signals:
        return {"score": 50, "trend": "Noaniq", "momentum": "O'rta",
                "volume": "O'rta", "volatility": "O'rta"}

    scores = [s.confidence for s in all_signals]
    bull_count = sum(1 for s in all_signals if s.trend == "BULLISH")
    bear_count = sum(1 for s in all_signals if s.trend == "BEARISH")
    avg_rvol = np.mean([s.rvol for s in all_signals])

    avg_score = int(np.mean(scores))

    total = len(all_signals)
    bull_pct = bull_count / total if total > 0 else 0.5

    trend_label = "Bullish ✅" if bull_pct > 0.6 else ("Bearish ❌" if bull_pct < 0.4 else "Neytral ⚖️")
    momentum_label = "Kuchli ✅" if avg_score >= 65 else ("O'rta ⚠️" if avg_score >= 45 else "Zaif ❌")
    volume_label = ("Kuchli ✅" if avg_rvol >= 2 else ("O'rta ⚠️" if avg_rvol >= 1 else "Zaif ❌"))
    volatility_label = "O'rta ✅"

    return {
        "score": avg_score,
        "trend": trend_label,
        "momentum": momentum_label,
        "volume": volume_label,
        "volatility": volatility_label,
        "bull_count": bull_count,
        "bear_count": bear_count,
        "total": total,
    }
