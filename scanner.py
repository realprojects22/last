"""
scanner.py - HALOL CRYPTO AI BOT V3.5
Bozor skanerlash mexanizmi — faqat halol spot savdo
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple

import aiohttp
import numpy as np

from config import (
    HALAL_COINS, TIMEFRAMES, CACHE_TTL, ALERT_COOLDOWN,
    ALERT_THRESHOLD, SCAN_INTERVAL
)
from signals import (
    OHLCV, Indicators, MarketStructure, SignalResult,
    parse_klines, compute_indicators, analyze_market_structure,
    compute_confidence, compute_risk_levels, determine_signal_type,
    determine_risk_level, combine_mtf_signals, compute_market_health
)
from database import (
    cache_get, cache_set, cache_clear_expired,
    get_all_active_users, get_watchlist, check_alert_cooldown,
    record_alert, save_signal
)
from utils import fetch_klines, fetch_ticker, fetch_all_tickers, safe_float

logger = logging.getLogger(__name__)


# ============================================================
# TANGA TAHLILI
# ============================================================

async def analyze_coin(session: aiohttp.ClientSession,
                        symbol: str,
                        primary_tf: str = "1h",
                        full_mtf: bool = True) -> Optional[SignalResult]:
    """
    Bir tangani to'liq tahlil qilish.
    Ko'p vaqt oraliq, smart money, risk boshqaruvi.
    """
    cache_key = f"signal:{symbol}:{primary_tf}"
    cached = cache_get(cache_key)
    if cached:
        return _dict_to_signal(cached)

    result = SignalResult(symbol=symbol)

    # ---- TICKER MA'LUMOTLARI ----
    ticker = await fetch_ticker(session, symbol)
    if ticker:
        result.price = safe_float(ticker.get("lastPrice", 0))
        result.change_24h = safe_float(ticker.get("priceChangePercent", 0))

    if result.price <= 0:
        return None

    # ---- ASOSIY VAQT ORALIQ TAHLILI ----
    tf_conf = TIMEFRAMES.get(primary_tf, TIMEFRAMES["1h"])
    raw = await fetch_klines(session, symbol, tf_conf["interval"], tf_conf["limit"])
    ohlcv = parse_klines(raw)
    if not ohlcv:
        return None

    ind = compute_indicators(ohlcv)
    ms = analyze_market_structure(ohlcv)
    confidence, entry_quality, reasoning = compute_confidence(ind, ms, result.price)

    # ---- KO'P VAQT ORALIQ TAHLILI ----
    if full_mtf:
        mtf_scores: Dict[str, int] = {primary_tf: confidence}
        for tf_name in ["15m", "1h", "4h", "1d"]:
            if tf_name == primary_tf:
                continue
            tf_raw = await fetch_klines(
                session, symbol,
                TIMEFRAMES[tf_name]["interval"],
                TIMEFRAMES[tf_name]["limit"]
            )
            tf_ohlcv = parse_klines(tf_raw)
            if tf_ohlcv:
                tf_ind = compute_indicators(tf_ohlcv)
                tf_ms = analyze_market_structure(tf_ohlcv)
                tf_conf_val, _, _ = compute_confidence(tf_ind, tf_ms, result.price)
                mtf_scores[tf_name] = tf_conf_val

        combined_conf, mtf_reasoning = combine_mtf_signals(mtf_scores)
        confidence = combined_conf
        reasoning.extend(mtf_reasoning)

    # ---- SIGNAL ANIQLASH ----
    signal_type = determine_signal_type(confidence, ms)
    risk_level = determine_risk_level(confidence)

    # ---- RISK BOSHQARUVI ----
    stop_loss, tp1, tp2, tp3, risk_reward = compute_risk_levels(
        result.price, ind, ms
    )

    # ---- NATIJANI TO'LDIRISH ----
    result.signal_type = signal_type
    result.confidence = confidence
    result.entry_quality = entry_quality
    result.risk_level = risk_level
    result.stop_loss = stop_loss
    result.tp1 = tp1
    result.tp2 = tp2
    result.tp3 = tp3
    result.risk_reward = risk_reward
    result.rvol = ind.rvol
    result.trend = ms.trend
    result.timeframe = primary_tf
    result.reasoning = reasoning

    result.indicators = {
        "rsi": ind.rsi,
        "ema20": ind.ema20,
        "ema50": ind.ema50,
        "ema200": ind.ema200,
        "macd_line": ind.macd_line,
        "macd_signal": ind.macd_signal,
        "macd_hist": ind.macd_hist,
        "adx": ind.adx,
        "di_plus": ind.di_plus,
        "di_minus": ind.di_minus,
        "bb_upper": ind.bb_upper,
        "bb_lower": ind.bb_lower,
        "atr": ind.atr,
        "rvol": ind.rvol,
        "volume_ma": ind.volume_ma,
    }

    result.structure = {
        "trend": ms.trend,
        "support": float(ms.support),
        "resistance": float(ms.resistance),
        "order_block_bull": list(ms.order_block_bull) if ms.order_block_bull else None,
        "order_block_bear": list(ms.order_block_bear) if ms.order_block_bear else None,
        "fvg_bull": list(ms.fvg_bull) if ms.fvg_bull else None,
        "bos_bullish": bool(ms.bos_bullish),
        "choch_bullish": bool(ms.choch_bullish),
        "liquidity_sweep_bull": bool(ms.liquidity_sweep_bull),
        "breakout_detected": bool(ms.breakout_detected),
        "retest_confirmed": bool(ms.retest_confirmed),
        "higher_highs": bool(ms.higher_highs),
        "higher_lows": bool(ms.higher_lows),
    }

    # Keshga saqlash
    cache_set(cache_key, _signal_to_dict(result), CACHE_TTL)

    # Signal tarixini saqlash
    try:
        save_signal(symbol, _signal_to_dict(result))
    except Exception:
        pass

    return result


# ============================================================
# BARCHA TANGALARNI SKANERLASH
# ============================================================

async def scan_all_coins(session: aiohttp.ClientSession,
                          coins: Optional[List[str]] = None) -> List[SignalResult]:
    """Barcha halol tangalarni parallel skanerlash."""
    target_coins = coins or HALAL_COINS
    results: List[SignalResult] = []

    logger.info(f"🔍 {len(target_coins)} tanga skanerlash boshlanmoqda...")

    # Concurrency chegarasi: API limitlarini hurmat qilish
    semaphore = asyncio.Semaphore(5)

    async def analyze_with_limit(symbol: str):
        async with semaphore:
            try:
                result = await analyze_coin(session, symbol, "1h", full_mtf=False)
                if result:
                    results.append(result)
            except Exception as e:
                logger.debug(f"Skanerlash xatosi {symbol}: {e}")

    await asyncio.gather(*[analyze_with_limit(sym) for sym in target_coins])
    logger.info(f"✅ Skanerlash yakunlandi: {len(results)}/{len(target_coins)} tanga")
    return results


# ============================================================
# KUCHLI SIGNALLARNI TOPISH
# ============================================================

async def find_strong_signals(session: aiohttp.ClientSession,
                               threshold: int = None) -> List[SignalResult]:
    """Barcha tangalar orasidan kuchli signallarni topish."""
    min_threshold = threshold or ALERT_THRESHOLD
    all_signals = await scan_all_coins(session)
    strong = [
        s for s in all_signals
        if s.confidence >= min_threshold and s.signal_type in ("STRONG_BUY", "BUY")
    ]
    strong.sort(key=lambda x: x.confidence, reverse=True)
    return strong


# ============================================================
# TREND REYTINGI
# ============================================================

async def get_coin_rankings(session: aiohttp.ClientSession,
                             limit: int = 20) -> Dict[str, List[SignalResult]]:
    """Tangalarni turli mezonlar bo'yicha reytinglash."""
    all_signals = await scan_all_coins(session)

    # Eng kuchli trend
    by_confidence = sorted(all_signals, key=lambda x: x.confidence, reverse=True)[:limit]

    # Eng yuqori RVOL
    by_rvol = sorted(all_signals, key=lambda x: x.rvol, reverse=True)[:limit]

    # Eng yaxshi R:R
    by_rr = sorted(
        [s for s in all_signals if s.risk_reward > 0],
        key=lambda x: x.risk_reward, reverse=True
    )[:limit]

    # Eng yaxshi kirish sifati
    by_quality = sorted(all_signals, key=lambda x: x.entry_quality, reverse=True)[:limit]

    return {
        "by_confidence": by_confidence,
        "by_rvol": by_rvol,
        "by_rr": by_rr,
        "by_quality": by_quality,
    }


# ============================================================
# WATCHLIST YANGILASH
# ============================================================

async def update_watchlist_signals(
        session: aiohttp.ClientSession,
        user_id: int,
        symbols: List[str]
) -> List[SignalResult]:
    """Foydalanuvchi kuzatuv ro'yxatini yangilash."""
    results = []
    for symbol in symbols:
        try:
            result = await analyze_coin(session, symbol, "1h", full_mtf=True)
            if result:
                results.append(result)
        except Exception as e:
            logger.debug(f"Watchlist yangilash xatosi {symbol}: {e}")
    return results


# ============================================================
# FOYDALANUVCHILARGA OGOHLANTIRISH YUBORISH
# ============================================================

async def check_and_alert_users(
        session: aiohttp.ClientSession,
        application,
        strong_signals: List[SignalResult]
) -> int:
    """Kuchli signallar uchun foydalanuvchilarga ogohlantirish yuborish."""
    from bot import format_signal_message  # Circular import dan saqlanish

    if not strong_signals:
        return 0

    users = get_all_active_users()
    sent_count = 0

    for user in users:
        uid = user["user_id"]
        user_watchlist = get_watchlist(uid)

        for signal in strong_signals:
            # Faqat kuzatuv ro'yxatidagi tangalar
            if signal.symbol not in user_watchlist:
                continue

            # Cooldown tekshiruvi
            if check_alert_cooldown(uid, signal.symbol, ALERT_COOLDOWN):
                continue

            try:
                msg = format_signal_message(signal)
                await application.bot.send_message(
                    chat_id=uid,
                    text=msg,
                    parse_mode="HTML"
                )
                record_alert(uid, signal.symbol, signal.signal_type,
                             signal.confidence, signal.price)
                sent_count += 1
                await asyncio.sleep(0.1)  # Flood protection
            except Exception as e:
                logger.warning(f"Xabar yuborish xatosi {uid}: {e}")

    return sent_count


# ============================================================
# GLOBAL SKANERLASH TSIKLI
# ============================================================

async def continuous_scanner(application, interval: int = SCAN_INTERVAL):
    """Uzluksiz bozor skaneri."""
    logger.info(f"🚀 Uzluksiz skaner ishga tushdi (interval: {interval}s)")

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                start_time = time.time()
                logger.info("📡 Bozor skanerlash boshlandi...")

                # Barcha kuchli signallarni topish
                strong_signals = await find_strong_signals(session)

                if strong_signals:
                    logger.info(f"🔥 {len(strong_signals)} kuchli signal topildi")
                    sent = await check_and_alert_users(session, application, strong_signals)
                    logger.info(f"📨 {sent} ogohlantirish yuborildi")

                # Muddati o'tgan keshni tozalash
                cache_clear_expired()

                elapsed = time.time() - start_time
                sleep_time = max(0, interval - elapsed)
                logger.info(f"⏱️ Keyingi skan: {sleep_time:.0f}s")
                await asyncio.sleep(sleep_time)

            except asyncio.CancelledError:
                logger.info("Skaner to'xtatildi")
                break
            except Exception as e:
                logger.error(f"Skaner xatosi: {e}")
                await asyncio.sleep(60)


# ============================================================
# YORDAMCHI FUNKSIYALAR
# ============================================================

def _sanitize(obj):
    """Numpy/non-JSON tiplarini Python native tiplarga o'tkazish."""
    import numpy as np
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_sanitize(i) for i in obj]
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


def _signal_to_dict(signal: SignalResult) -> dict:
    """SignalResult ni dictionary ga aylantirish (JSON-safe)."""
    raw = {
        "symbol": signal.symbol,
        "signal_type": signal.signal_type,
        "confidence": signal.confidence,
        "entry_quality": signal.entry_quality,
        "risk_level": signal.risk_level,
        "price": signal.price,
        "change_24h": signal.change_24h,
        "stop_loss": signal.stop_loss,
        "tp1": signal.tp1,
        "tp2": signal.tp2,
        "tp3": signal.tp3,
        "risk_reward": signal.risk_reward,
        "rvol": signal.rvol,
        "trend": signal.trend,
        "indicators": signal.indicators,
        "structure": signal.structure,
        "reasoning": signal.reasoning,
        "timeframe": signal.timeframe,
    }
    return _sanitize(raw)


def _dict_to_signal(d: dict) -> SignalResult:
    """Dictionary ni SignalResult ga aylantirish."""
    s = SignalResult()
    for k, v in d.items():
        if hasattr(s, k):
            setattr(s, k, v)
    return s
