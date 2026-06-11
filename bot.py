"""
bot.py - HALOL CRYPTO AI BOT V3.5
Asosiy Telegram bot — to'liq qayta yozilgan
✅ Button watchlist  ✅ Chart rasmlar  ✅ 15min signallar  ✅ Strong alerts
"""

import asyncio
import logging
import io
from typing import Optional, List

import aiohttp
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    BotCommand, InputMediaPhoto
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from telegram.constants import ParseMode

from config import (
    TELEGRAM_BOT_TOKEN, SIGNALS, RISK_LEVELS,
    HALAL_COINS, LOG_LEVEL, SCAN_INTERVAL,
    ALERT_THRESHOLD, RVOL_THRESHOLDS, DEFAULT_WATCHLIST
)
from database import (
    init_database, upsert_user, get_user,
    get_watchlist, add_to_watchlist, remove_from_watchlist,
    get_settings, update_setting, get_alert_history,
    get_all_active_users, check_alert_cooldown, record_alert
)
from signals import SignalResult, compute_market_health
from scanner import (
    analyze_coin, scan_all_coins, find_strong_signals,
    get_coin_rankings, _signal_to_dict
)
from ai_helper import (
    search_knowledge, AI_MENU_SECTIONS, get_section_topics,
    get_topic_content, get_all_topics
)
from utils import (
    format_price, format_pct, format_volume,
    get_symbol_base, normalize_symbol, setup_logging,
    fetch_klines
)
from signals import parse_klines

logger = logging.getLogger(__name__)


# ============================================================
# GRAFIK YORDAMCHI
# ============================================================

async def send_chart(bot, chat_id: int, signal: SignalResult,
                     session: aiohttp.ClientSession, caption: str = ""):
    """Grafik rasmini yuborish — xatolik bo'lsa jim o'tish."""
    try:
        from charts import generate_chart
        tf = signal.timeframe or "1h"
        raw = await fetch_klines(session, signal.symbol, tf, 120)
        ohlcv = parse_klines(raw)
        if not ohlcv:
            return
        chart_bytes = generate_chart(ohlcv, signal)
        if not chart_bytes:
            return
        base = get_symbol_base(signal.symbol)
        cap = caption or f"📊 {base}/USDT — {tf.upper()} Grafik"
        await bot.send_photo(
            chat_id=chat_id,
            photo=io.BytesIO(chart_bytes),
            caption=cap,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.warning(f"Grafik yuborish xatosi {signal.symbol}: {e}")


# ============================================================
# XABAR FORMATLASH
# ============================================================

def format_signal_message(signal: SignalResult, detailed: bool = False) -> str:
    sig_cfg = SIGNALS.get(signal.signal_type, SIGNALS["WAIT"])
    risk_cfg = RISK_LEVELS.get(signal.risk_level, RISK_LEVELS["HIGH"])
    base = get_symbol_base(signal.symbol)

    rvol = signal.rvol
    if rvol >= RVOL_THRESHOLDS["EXCEPTIONAL"]:
        rvol_badge = f"🚀 {rvol:.2f}x"
    elif rvol >= RVOL_THRESHOLDS["STRONG"]:
        rvol_badge = f"🔥 {rvol:.2f}x"
    elif rvol >= RVOL_THRESHOLDS["NORMAL_LOW"]:
        rvol_badge = f"✅ {rvol:.2f}x"
    else:
        rvol_badge = f"⚠️ {rvol:.2f}x"

    trend_badges = {"BULLISH": "📈 Bullish", "BEARISH": "📉 Bearish", "SIDEWAYS": "↔️ Yandeq"}
    trend_badge = trend_badges.get(signal.trend, "↔️ Yandeq")
    chg = signal.change_24h
    chg_str = f"{'🟢' if chg >= 0 else '🔴'} {format_pct(chg)}"

    msg = (
        f"{sig_cfg['emoji']} <b>{sig_cfg['name']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🪙 <b>{base}/USDT</b>  |  {chg_str}\n"
        f"💵 Narx: <code>${format_price(signal.price)}</code>\n"
        f"📊 Ishonch: <b>{signal.confidence}/100</b>  |  "
        f"🎯 Kirish Sifati: <b>{signal.entry_quality}/100</b>\n"
        f"📉 Trend: {trend_badge}  |  🔁 RVOL: {rvol_badge}\n"
        f"⚠️ Xavf: {risk_cfg['emoji']} {risk_cfg['name']}\n"
    )

    if signal.signal_type in ("BUY", "STRONG_BUY") and signal.stop_loss > 0:
        msg += (
            f"\n<b>📐 Risk Boshqaruvi:</b>\n"
            f"  🟢 Kirish:    <code>${format_price(signal.price)}</code>\n"
            f"  🛑 Stop Loss: <code>${format_price(signal.stop_loss)}</code>\n"
            f"  🎯 TP1:       <code>${format_price(signal.tp1)}</code>\n"
            f"  🎯 TP2:       <code>${format_price(signal.tp2)}</code>\n"
            f"  🎯 TP3:       <code>${format_price(signal.tp3)}</code>\n"
            f"  ⚖️ R:R:       <b>1:{signal.risk_reward}</b>\n"
        )

    if detailed:
        ind = signal.indicators
        struct = signal.structure

        msg += f"\n<b>📊 Indikatorlar:</b>\n"
        msg += (f"  RSI: <b>{ind.get('rsi', 0):.1f}</b>  "
                f"ADX: <b>{ind.get('adx', 0):.1f}</b>  "
                f"ATR: <b>${format_price(ind.get('atr', 0))}</b>\n")
        msg += (f"  EMA20: <code>${format_price(ind.get('ema20', 0))}</code>  "
                f"EMA50: <code>${format_price(ind.get('ema50', 0))}</code>  "
                f"EMA200: <code>${format_price(ind.get('ema200', 0))}</code>\n")
        macd_hist = ind.get("macd_hist", 0)
        msg += f"  MACD: {'🟢' if macd_hist > 0 else '🔴'} <b>{macd_hist:.6f}</b>\n"

        msg += f"\n<b>🏗️ Bozor Tuzilmasi:</b>\n"
        msg += (f"  Support: <code>${format_price(struct.get('support', 0))}</code>  "
                f"Resistance: <code>${format_price(struct.get('resistance', 0))}</code>\n")

        flags = []
        if struct.get("order_block_bull"):     flags.append("🟦 Bull OB")
        if struct.get("fvg_bull"):             flags.append("📐 FVG")
        if struct.get("bos_bullish"):          flags.append("💥 BOS")
        if struct.get("choch_bullish"):        flags.append("🔄 CHoCH")
        if struct.get("liquidity_sweep_bull"): flags.append("💧 Likvidlik")
        if struct.get("breakout_detected") and struct.get("retest_confirmed"):
            flags.append("✅ Breakout+Retest")
        elif struct.get("breakout_detected"):  flags.append("💥 Breakout")
        if struct.get("higher_highs"):         flags.append("📈 HH")
        if struct.get("higher_lows"):          flags.append("📈 HL")
        if flags:
            msg += "  " + "  ".join(flags) + "\n"

        if signal.reasoning:
            msg += f"\n<b>🔍 Nega bu signal?</b>\n"
            for r in signal.reasoning[:6]:
                msg += f"  {r}\n"

    msg += f"\n⏱ <i>Vaqt oralig'i: {signal.timeframe.upper()}</i>"
    return msg


def format_market_health(health: dict) -> str:
    score = health.get("score", 50)
    bars = ["🟥⬜⬜⬜⬜", "🟨🟨⬜⬜⬜", "🟩🟩🟩⬜⬜", "🟩🟩🟩🟩⬜", "🟩🟩🟩🟩🟩"]
    bar = bars[min(int(score / 20), 4)]
    bull = health.get("bull_count", 0)
    bear = health.get("bear_count", 0)
    total = health.get("total", 1)
    return (
        f"📊 <b>Bozor Holati</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌡 Ball: <b>{score}/100</b>  {bar}\n\n"
        f"📈 Trend:      {health.get('trend', 'Noaniq')}\n"
        f"⚡ Momentum:   {health.get('momentum', 'O\'rta')}\n"
        f"📦 Hajm:       {health.get('volume', 'O\'rta')}\n"
        f"🌊 Volatillik: {health.get('volatility', 'O\'rta')}\n\n"
        f"🐂 Buqali: <b>{bull}</b>  🐻 Ayiqli: <b>{bear}</b>  Jami: <b>{total}</b>\n"
    )


# ============================================================
# INLINE KLAVIATURALAR
# ============================================================

def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Signal",           callback_data="menu_signal"),
         InlineKeyboardButton("📈 Coin Tahlili",     callback_data="menu_analysis")],
        [InlineKeyboardButton("⭐ Watchlist",         callback_data="menu_watchlist"),
         InlineKeyboardButton("🚨 Kuchli Signallar", callback_data="menu_strong")],
        [InlineKeyboardButton("📚 AI Yordamchi",     callback_data="menu_ai"),
         InlineKeyboardButton("📊 Bozor Holati",     callback_data="menu_market")],
        [InlineKeyboardButton("🏆 Imkoniyatlar",     callback_data="menu_opps"),
         InlineKeyboardButton("📈 Reyting",           callback_data="menu_ranking")],
        [InlineKeyboardButton("⚙️ Sozlamalar",        callback_data="menu_settings"),
         InlineKeyboardButton("ℹ️ Yordam",             callback_data="menu_help")],
    ])


def back_keyboard(target: str = "menu_main", label: str = "🏠 Asosiy Menyu") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data=target)]])


def watchlist_view_keyboard(symbols: List[str]) -> InlineKeyboardMarkup:
    """Watchlist ko'rish + tanga tahlili tugmalari."""
    buttons = []
    row = []
    for sym in symbols:
        base = get_symbol_base(sym)
        row.append(InlineKeyboardButton(f"📊 {base}", callback_data=f"analyze_{sym}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([
        InlineKeyboardButton("➕ Qo'shish",   callback_data="wl_add_page_0"),
        InlineKeyboardButton("➖ O'chirish",  callback_data="wl_remove_menu"),
    ])
    buttons.append([InlineKeyboardButton("🏠 Asosiy Menyu", callback_data="menu_main")])
    return InlineKeyboardMarkup(buttons)


def watchlist_add_keyboard(page: int = 0) -> InlineKeyboardMarkup:
    """Watchlistga qo'shish uchun tanga tanlash tugmalari (sahifalash)."""
    page_size = 21  # 7 qator x 3
    start = page * page_size
    end = start + page_size
    coins_page = HALAL_COINS[start:end]

    buttons = []
    row = []
    for sym in coins_page:
        base = get_symbol_base(sym)
        row.append(InlineKeyboardButton(base, callback_data=f"wl_pick_{sym}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    # Sahifalash
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Oldingi", callback_data=f"wl_add_page_{page-1}"))
    if end < len(HALAL_COINS):
        nav.append(InlineKeyboardButton("Keyingi ▶️", callback_data=f"wl_add_page_{page+1}"))
    if nav:
        buttons.append(nav)

    total_pages = (len(HALAL_COINS) + page_size - 1) // page_size
    buttons.append([InlineKeyboardButton(
        f"📄 Sahifa {page+1}/{total_pages}", callback_data="noop"
    )])
    buttons.append([InlineKeyboardButton("◀️ Watchlist", callback_data="menu_watchlist")])
    return InlineKeyboardMarkup(buttons)


def watchlist_remove_keyboard(symbols: List[str]) -> InlineKeyboardMarkup:
    """Watchlistdan o'chirish tugmalari."""
    buttons = []
    row = []
    for sym in symbols:
        base = get_symbol_base(sym)
        row.append(InlineKeyboardButton(f"❌ {base}", callback_data=f"wl_del_{sym}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("◀️ Watchlist", callback_data="menu_watchlist")])
    return InlineKeyboardMarkup(buttons)


def coin_select_keyboard(coins: List[str], prefix: str = "analyze",
                          cols: int = 3, back: str = "menu_main") -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for sym in coins[:30]:
        base = get_symbol_base(sym)
        row.append(InlineKeyboardButton(base, callback_data=f"{prefix}_{sym}"))
        if len(row) == cols:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🏠 Asosiy Menyu", callback_data=back)])
    return InlineKeyboardMarkup(buttons)


def ai_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 Kripto Asoslari",  callback_data="ai_basics")],
        [InlineKeyboardButton("📈 Texnik Tahlil",    callback_data="ai_technical")],
        [InlineKeyboardButton("💰 Spot Savdo",       callback_data="ai_spot_trading")],
        [InlineKeyboardButton("🕌 Halol Kripto",     callback_data="ai_halal_crypto")],
        [InlineKeyboardButton("⚠️ Risk Boshqaruvi", callback_data="ai_risk_management")],
        [InlineKeyboardButton("🏦 Smart Money",      callback_data="ai_smart_money")],
        [InlineKeyboardButton("🔍 Savol Berish",     callback_data="ai_search")],
        [InlineKeyboardButton("🏠 Asosiy Menyu",     callback_data="menu_main")],
    ])


def ai_section_keyboard(section_key: str) -> InlineKeyboardMarkup:
    topics = get_section_topics(section_key)
    buttons = [[InlineKeyboardButton(t["title"], callback_data=f"ai_topic_{t['key']}")] for t in topics]
    buttons.append([InlineKeyboardButton("◀️ AI Menyu", callback_data="menu_ai")])
    return InlineKeyboardMarkup(buttons)


def ranking_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏆 Eng Kuchli Ishonch", callback_data="rank_confidence")],
        [InlineKeyboardButton("🔥 Eng Yuqori RVOL",    callback_data="rank_rvol")],
        [InlineKeyboardButton("⚖️ Eng Yaxshi R:R",     callback_data="rank_rr")],
        [InlineKeyboardButton("🎯 Kirish Sifati",       callback_data="rank_quality")],
        [InlineKeyboardButton("🏠 Asosiy Menyu",        callback_data="menu_main")],
    ])


def settings_keyboard(settings: dict) -> InlineKeyboardMarkup:
    alert_icon = "🔔" if settings.get("notify_strong") else "🔕"
    chart_icon = "📊" if settings.get("show_chart") else "📉"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{alert_icon} Ogohlantirishlar", callback_data="settings_alerts")],
        [InlineKeyboardButton(f"{chart_icon} Grafiklar",        callback_data="settings_charts")],
        [InlineKeyboardButton("🎯 Signal Chegarasi",            callback_data="settings_threshold")],
        [InlineKeyboardButton("🏠 Asosiy Menyu",                callback_data="menu_main")],
    ])


# ============================================================
# /START
# ============================================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    upsert_user(user.id, username=user.username or "",
                first_name=user.first_name or "", last_name=user.last_name or "")
    welcome = (
        f"🕌 <b>Assalomu alaykum, {user.first_name}!</b>\n\n"
        f"<b>HALOL CRYPTO AI BOT V3.5</b> ga xush kelibsiz!\n\n"
        f"✅ Spot savdo signallari + grafiklar\n"
        f"✅ RSI, EMA, MACD, ADX, ATR, BB, RVOL\n"
        f"✅ Smart Money: OB, FVG, BOS, CHoCH\n"
        f"✅ 15 daqiqalik watchlist signallari\n"
        f"✅ Kuchli signallarda avtomatik ogohlantirish\n"
        f"✅ Har signal bilan professional grafik\n\n"
        f"❌ Futures/Leveraj/Short — <b>HECH QACHON</b>\n\n"
        f"Quyidagi menyudan boshlang:"
    )
    await update.message.reply_text(welcome, parse_mode=ParseMode.HTML,
                                    reply_markup=main_menu_keyboard())


async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📋 <b>Asosiy Menyu</b>",
                                    parse_mode=ParseMode.HTML,
                                    reply_markup=main_menu_keyboard())


# ============================================================
# ASOSIY CALLBACK HANDLER
# ============================================================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user
    upsert_user(user.id, username=user.username or "", first_name=user.first_name or "")

    # ---- NOOP ----
    if data == "noop":
        return

    # ---- ASOSIY MENYU ----
    if data == "menu_main":
        await query.edit_message_text("📋 <b>Asosiy Menyu</b>",
                                      parse_mode=ParseMode.HTML,
                                      reply_markup=main_menu_keyboard())

    # ---- SIGNAL ----
    elif data == "menu_signal":
        watchlist = get_watchlist(user.id)
        await query.edit_message_text(
            "📊 <b>Signal</b>\n\nWatchlistdagi tanga tanlang:",
            parse_mode=ParseMode.HTML,
            reply_markup=coin_select_keyboard(watchlist, "analyze")
        )

    # ---- COIN TAHLILI ----
    elif data == "menu_analysis":
        await query.edit_message_text(
            "📈 <b>Coin Tahlili</b>\n\nTanga tanlang:",
            parse_mode=ParseMode.HTML,
            reply_markup=coin_select_keyboard(HALAL_COINS[:24], "analyze")
        )

    # ---- TANGA TAHLILI ----
    elif data.startswith("analyze_"):
        symbol = data[len("analyze_"):]
        await _do_coin_analysis(query, context, symbol, user.id)

    # ---- WATCHLIST KO'RISH ----
    elif data == "menu_watchlist":
        watchlist = get_watchlist(user.id)
        if not watchlist:
            text = "⭐ <b>Watchlist</b>\n\nHali hech qanday tanga yo'q. Qo'shing!"
        else:
            bases = " | ".join(get_symbol_base(s) for s in watchlist)
            text = f"⭐ <b>Watchlist</b>\n\n<code>{bases}</code>\n\nTahlil uchun tanga bosing:"
        await query.edit_message_text(text, parse_mode=ParseMode.HTML,
                                      reply_markup=watchlist_view_keyboard(watchlist))

    # ---- WATCHLIST QO'SHISH (tugmalar orqali) ----
    elif data.startswith("wl_add_page_"):
        page = int(data.split("_")[-1])
        total = len(HALAL_COINS)
        await query.edit_message_text(
            f"➕ <b>Watchlistga Qo'shish</b>\n\n"
            f"Tanga tanlang ({total} ta halol tanga):",
            parse_mode=ParseMode.HTML,
            reply_markup=watchlist_add_keyboard(page)
        )

    elif data.startswith("wl_pick_"):
        symbol = data[len("wl_pick_"):]
        success = add_to_watchlist(user.id, symbol)
        base = get_symbol_base(symbol)
        if success:
            await query.answer(f"✅ {base} qo'shildi!", show_alert=True)
        else:
            await query.answer(f"⚠️ {base} allaqachon bor yoki limit to'ldi.", show_alert=True)
        # Sahifani yangilash
        page = 0
        await query.edit_message_text(
            f"➕ <b>Watchlistga Qo'shish</b>\n\nTanga tanlang:",
            parse_mode=ParseMode.HTML,
            reply_markup=watchlist_add_keyboard(page)
        )

    # ---- WATCHLIST O'CHIRISH ----
    elif data == "wl_remove_menu":
        watchlist = get_watchlist(user.id)
        if not watchlist:
            await query.answer("Watchlist bo'sh!", show_alert=True)
            return
        await query.edit_message_text(
            "➖ <b>Qaysi tangani o'chirish?</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=watchlist_remove_keyboard(watchlist)
        )

    elif data.startswith("wl_del_"):
        symbol = data[len("wl_del_"):]
        remove_from_watchlist(user.id, symbol)
        base = get_symbol_base(symbol)
        await query.answer(f"✅ {base} o'chirildi!", show_alert=True)
        watchlist = get_watchlist(user.id)
        if not watchlist:
            text = "⭐ <b>Watchlist</b>\n\nHali hech qanday tanga yo'q."
        else:
            bases = " | ".join(get_symbol_base(s) for s in watchlist)
            text = f"⭐ <b>Watchlist</b>\n\n<code>{bases}</code>"
        await query.edit_message_text(text, parse_mode=ParseMode.HTML,
                                      reply_markup=watchlist_view_keyboard(watchlist))

    # ---- KUCHLI SIGNALLAR ----
    elif data == "menu_strong":
        await query.edit_message_text(
            "🚨 <b>Kuchli Signallar Skanerlanmoqda...</b>\n\n⏳ 20-60 soniya kuting...",
            parse_mode=ParseMode.HTML
        )
        await _do_strong_signals(query, context, user.id)

    # ---- BOZOR HOLATI ----
    elif data == "menu_market":
        await query.edit_message_text(
            "📊 <b>Bozor Holati Hisoblanmoqda...</b>\n\n⏳ Kuting...",
            parse_mode=ParseMode.HTML
        )
        await _do_market_health(query, context)

    # ---- TOP IMKONIYATLAR ----
    elif data == "menu_opps":
        await query.edit_message_text(
            "🏆 <b>Eng Kuchli Imkoniyatlar Skanerlanmoqda...</b>\n\n⏳ Kuting...",
            parse_mode=ParseMode.HTML
        )
        await _do_top_opportunities(query, context, user.id)

    # ---- REYTING ----
    elif data == "menu_ranking":
        await query.edit_message_text("📈 <b>Reyting</b>\n\nMezon tanlang:",
                                      parse_mode=ParseMode.HTML,
                                      reply_markup=ranking_keyboard())

    elif data.startswith("rank_"):
        rank_type = data[5:]
        await query.edit_message_text("📊 <b>Reyting hisoblanmoqda...</b>\n\n⏳ Kuting...",
                                      parse_mode=ParseMode.HTML)
        await _do_ranking(query, context, rank_type)

    # ---- AI YORDAMCHI ----
    elif data == "menu_ai":
        await query.edit_message_text(
            "🤖 <b>AI Yordamchi</b>\n\nMavzu tanlang yoki savol bering:",
            parse_mode=ParseMode.HTML, reply_markup=ai_menu_keyboard()
        )

    elif data.startswith("ai_") and not data.startswith("ai_topic_"):
        section_key = data[3:]
        if section_key == "search":
            await query.edit_message_text(
                "🔍 <b>Savol Berish</b>\n\nMavzu nomini yozing:\n\n"
                "<code>rsi  macd  ema  adx  atr  bollinger\n"
                "volume  support  resistance  trend\n"
                "orderblock  fvg  bos  choch  candlestick\n"
                "breakout  liquidity  spot  halol\n"
                "risk  position  portfolio</code>",
                parse_mode=ParseMode.HTML,
                reply_markup=back_keyboard("menu_ai", "◀️ AI Menyu")
            )
            context.user_data["awaiting"] = "ai_search"
        elif section_key in AI_MENU_SECTIONS:
            section = AI_MENU_SECTIONS[section_key]
            await query.edit_message_text(
                f"{section['emoji']} <b>{section['title']}</b>\n\nMavzu tanlang:",
                parse_mode=ParseMode.HTML,
                reply_markup=ai_section_keyboard(section_key)
            )

    elif data.startswith("ai_topic_"):
        topic_key = data[len("ai_topic_"):]
        content = get_topic_content(topic_key)
        if content:
            await query.edit_message_text(
                content, parse_mode=ParseMode.HTML,
                reply_markup=back_keyboard("menu_ai", "◀️ AI Menyu")
            )

    # ---- SOZLAMALAR ----
    elif data == "menu_settings":
        settings = get_settings(user.id)
        msg = (
            f"⚙️ <b>Sozlamalar</b>\n\n"
            f"🔔 Kuchli signal: {'✅ Yoqilgan' if settings.get('notify_strong') else '❌ O\'chirilgan'}\n"
            f"📊 Grafik: {'✅ Ha' if settings.get('show_chart') else '❌ Yo\'q'}\n"
            f"🎯 Signal chegarasi: <b>{settings.get('alert_threshold', 70)}/100</b>\n"
        )
        await query.edit_message_text(msg, parse_mode=ParseMode.HTML,
                                      reply_markup=settings_keyboard(settings))

    elif data == "settings_alerts":
        settings = get_settings(user.id)
        new_val = 0 if settings.get("notify_strong", 1) else 1
        update_setting(user.id, "notify_strong", new_val)
        await query.answer(f"Ogohlantirishlar: {'Yoqildi ✅' if new_val else 'O\'chirildi ❌'}")
        settings["notify_strong"] = new_val
        msg = (
            f"⚙️ <b>Sozlamalar</b>\n\n"
            f"🔔 Kuchli signal: {'✅ Yoqilgan' if new_val else '❌ O\'chirilgan'}\n"
            f"📊 Grafik: {'✅ Ha' if settings.get('show_chart') else '❌ Yo\'q'}\n"
            f"🎯 Signal chegarasi: <b>{settings.get('alert_threshold', 70)}/100</b>\n"
        )
        await query.edit_message_text(msg, parse_mode=ParseMode.HTML,
                                      reply_markup=settings_keyboard(settings))

    elif data == "settings_charts":
        settings = get_settings(user.id)
        new_val = 0 if settings.get("show_chart", 1) else 1
        update_setting(user.id, "show_chart", new_val)
        await query.answer(f"Grafiklar: {'Yoqildi ✅' if new_val else 'O\'chirildi ❌'}")
        settings["show_chart"] = new_val
        msg = (
            f"⚙️ <b>Sozlamalar</b>\n\n"
            f"🔔 Kuchli signal: {'✅ Yoqilgan' if settings.get('notify_strong') else '❌ O\'chirilgan'}\n"
            f"📊 Grafik: {'✅ Ha' if new_val else '❌ Yo\'q'}\n"
            f"🎯 Signal chegarasi: <b>{settings.get('alert_threshold', 70)}/100</b>\n"
        )
        await query.edit_message_text(msg, parse_mode=ParseMode.HTML,
                                      reply_markup=settings_keyboard(settings))

    elif data == "settings_threshold":
        await query.edit_message_text(
            "🎯 <b>Signal Chegarasi</b>\n\n"
            "Minimal ishonch ballini yuboring (40–95).\n"
            "Masalan: <code>65</code> yoki <code>75</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=back_keyboard("menu_settings", "◀️ Sozlamalar")
        )
        context.user_data["awaiting"] = "threshold_input"

    # ---- YORDAM ----
    elif data == "menu_help":
        await query.edit_message_text(
            "ℹ️ <b>Yordam</b>\n\n"
            "<b>Signal turlari:</b>\n"
            "🔥 KUCHLI SOTIB OLISH (80-100)\n"
            "🟢 SOTIB OLISH (60-79)\n"
            "🟡 KUTISH (40-59)\n"
            "🔵 FOYDA OLISH (bearish)\n"
            "🟠 XAVF OSHDI\n\n"
            "<b>Komandalar:</b>\n"
            "/start /menu /signal /watchlist /market\n\n"
            "<b>🕌 Halol tamoyillar:</b>\n"
            "✅ Faqat spot  ✅ Faqat long\n"
            "❌ Futures/Leveraj/Short yo'q\n\n"
            "<b>⏱ Avtomatik signallar:</b>\n"
            "• Har 15 daqiqada watchlist skaneri\n"
            "• Kuchli signallarda darhol ogohlantirish\n"
            "• Har signal bilan grafik rasm",
            parse_mode=ParseMode.HTML,
            reply_markup=back_keyboard()
        )


# ============================================================
# TANGA TAHLILI (GRAFIK BILAN)
# ============================================================

async def _do_coin_analysis(query, context, symbol: str, user_id: int):
    base = get_symbol_base(symbol)
    await query.edit_message_text(
        f"🔍 <b>{base}/USDT</b> tahlil qilinmoqda...\n\n⏳ 5-15 soniya kuting...",
        parse_mode=ParseMode.HTML
    )
    try:
        async with aiohttp.ClientSession() as session:
            signal = await analyze_coin(session, symbol, "1h", full_mtf=True)

        if not signal:
            await query.edit_message_text(
                f"❌ <b>{base}/USDT</b> uchun ma'lumot olib bo'lmadi.",
                parse_mode=ParseMode.HTML, reply_markup=back_keyboard()
            )
            return

        msg = format_signal_message(signal, detailed=True)
        settings = get_settings(user_id)

        # Avval grafik yuborish
        if settings.get("show_chart", 1):
            async with aiohttp.ClientSession() as session:
                await send_chart(
                    context.bot,
                    query.message.chat_id,
                    signal, session,
                    caption=f"📊 <b>{base}/USDT</b> — {signal.timeframe.upper()} Grafik\n"
                            f"{SIGNALS.get(signal.signal_type, {}).get('emoji', '')} "
                            f"Ishonch: <b>{signal.confidence}%</b>"
                )

        # Keyin signal xabari
        await query.edit_message_text(
            msg, parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Yangilash",   callback_data=f"analyze_{symbol}"),
                 InlineKeyboardButton("⭐ Watchlistga", callback_data=f"wl_pick_{symbol}")],
                [InlineKeyboardButton("🏠 Asosiy Menyu", callback_data="menu_main")]
            ])
        )
    except Exception as e:
        logger.error(f"Coin tahlil xatosi {symbol}: {e}")
        await query.edit_message_text(
            f"❌ Xato: {str(e)[:150]}",
            parse_mode=ParseMode.HTML, reply_markup=back_keyboard()
        )


# ============================================================
# KUCHLI SIGNALLAR (GRAFIK BILAN)
# ============================================================

async def _do_strong_signals(query, context, user_id: int):
    try:
        async with aiohttp.ClientSession() as session:
            signals = await find_strong_signals(session, ALERT_THRESHOLD)

        if not signals:
            await query.edit_message_text(
                f"🚨 <b>Kuchli Signallar</b>\n\n"
                f"Hozirda {ALERT_THRESHOLD}+ ishonch darajasida signal topilmadi.\n"
                f"Keyinroq qayta urinib ko'ring.",
                parse_mode=ParseMode.HTML, reply_markup=back_keyboard()
            )
            return

        msg = f"🚨 <b>Kuchli Signallar</b> ({len(signals)} ta)\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        for s in signals[:10]:
            sig_cfg = SIGNALS.get(s.signal_type, {})
            base = get_symbol_base(s.symbol)
            chg = f"{'🟢' if s.change_24h >= 0 else '🔴'} {format_pct(s.change_24h)}"
            msg += (
                f"{sig_cfg.get('emoji','📊')} <b>{base}/USDT</b>  {chg}\n"
                f"   💵 ${format_price(s.price)}  📊 {s.confidence}%  🔁 {s.rvol:.2f}x\n\n"
            )

        buttons = []
        row = []
        for s in signals[:9]:
            base = get_symbol_base(s.symbol)
            row.append(InlineKeyboardButton(f"📊 {base}", callback_data=f"analyze_{s.symbol}"))
            if len(row) == 3:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        buttons.append([InlineKeyboardButton("🏠 Asosiy Menyu", callback_data="menu_main")])

        await query.edit_message_text(msg, parse_mode=ParseMode.HTML,
                                      reply_markup=InlineKeyboardMarkup(buttons))

        # Eng kuchli signal uchun grafik yuborish
        settings = get_settings(user_id)
        if signals and settings.get("show_chart", 1):
            async with aiohttp.ClientSession() as session:
                top = signals[0]
                await send_chart(
                    context.bot, query.message.chat_id, top, session,
                    caption=f"🔥 <b>Eng Kuchli Signal: {get_symbol_base(top.symbol)}/USDT</b>\n"
                            f"Ishonch: <b>{top.confidence}%</b>  |  RVOL: <b>{top.rvol:.2f}x</b>"
                )

    except Exception as e:
        logger.error(f"Kuchli signallar xatosi: {e}")
        await query.edit_message_text(f"❌ Xato: {str(e)[:150]}",
                                      parse_mode=ParseMode.HTML, reply_markup=back_keyboard())


# ============================================================
# BOZOR HOLATI
# ============================================================

async def _do_market_health(query, context):
    try:
        async with aiohttp.ClientSession() as session:
            all_signals = await scan_all_coins(session, HALAL_COINS[:40])
        health = compute_market_health(all_signals)
        msg = format_market_health(health)

        top_bull = sorted(
            [s for s in all_signals if s.trend == "BULLISH"],
            key=lambda x: x.confidence, reverse=True
        )[:5]
        if top_bull:
            msg += "\n<b>🏆 Top Bullish Tangalar:</b>\n"
            for i, s in enumerate(top_bull, 1):
                base = get_symbol_base(s.symbol)
                msg += f"  {i}. <b>{base}</b> — {s.confidence}%\n"

        await query.edit_message_text(msg, parse_mode=ParseMode.HTML,
                                      reply_markup=back_keyboard())
    except Exception as e:
        logger.error(f"Bozor holati xatosi: {e}")
        await query.edit_message_text(f"❌ Xato: {str(e)[:150]}",
                                      parse_mode=ParseMode.HTML, reply_markup=back_keyboard())


# ============================================================
# TOP IMKONIYATLAR (GRAFIK BILAN)
# ============================================================

async def _do_top_opportunities(query, context, user_id: int):
    try:
        async with aiohttp.ClientSession() as session:
            signals = await find_strong_signals(session, 60)

        if not signals:
            await query.edit_message_text(
                "🏆 <b>Eng Kuchli Imkoniyatlar</b>\n\nHozirda kuchli imkoniyat topilmadi.",
                parse_mode=ParseMode.HTML, reply_markup=back_keyboard()
            )
            return

        top10 = signals[:10]
        msg = f"🏆 <b>Eng Kuchli Imkoniyatlar</b> (Top {len(top10)})\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        medals = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
        for i, s in enumerate(top10):
            sig_cfg = SIGNALS.get(s.signal_type, {})
            base = get_symbol_base(s.symbol)
            msg += (
                f"{medals[i]} {sig_cfg.get('emoji','')} <b>{base}/USDT</b>\n"
                f"   📊 {s.confidence}%  🎯 {s.entry_quality}/100  "
                f"🔁 {s.rvol:.2f}x  ⚖️ 1:{s.risk_reward}\n\n"
            )

        buttons = []
        row = []
        for s in top10[:9]:
            base = get_symbol_base(s.symbol)
            row.append(InlineKeyboardButton(f"📊 {base}", callback_data=f"analyze_{s.symbol}"))
            if len(row) == 3:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        buttons.append([InlineKeyboardButton("🏠 Asosiy Menyu", callback_data="menu_main")])

        await query.edit_message_text(msg, parse_mode=ParseMode.HTML,
                                      reply_markup=InlineKeyboardMarkup(buttons))

        # Top 1 grafik
        settings = get_settings(user_id)
        if settings.get("show_chart", 1):
            async with aiohttp.ClientSession() as session:
                top = top10[0]
                await send_chart(
                    context.bot, query.message.chat_id, top, session,
                    caption=f"🏆 <b>Top Imkoniyat: {get_symbol_base(top.symbol)}/USDT</b>\n"
                            f"Ishonch: <b>{top.confidence}%</b>  Sifat: <b>{top.entry_quality}/100</b>"
                )

    except Exception as e:
        logger.error(f"Top imkoniyatlar xatosi: {e}")
        await query.edit_message_text(f"❌ Xato: {str(e)[:150]}",
                                      parse_mode=ParseMode.HTML, reply_markup=back_keyboard())


# ============================================================
# REYTING
# ============================================================

async def _do_ranking(query, context, rank_type: str):
    try:
        async with aiohttp.ClientSession() as session:
            rankings = await get_coin_rankings(session, 20)

        rank_map = {
            "confidence": ("by_confidence", "🏆 Eng Kuchli Ishonch"),
            "rvol":       ("by_rvol",        "🔥 Eng Yuqori RVOL"),
            "rr":         ("by_rr",          "⚖️ Eng Yaxshi R:R"),
            "quality":    ("by_quality",     "🎯 Kirish Sifati"),
        }
        key, title = rank_map.get(rank_type, ("by_confidence", "🏆 Reyting"))
        ranked = rankings.get(key, [])[:10]

        msg = f"<b>{title}</b>\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        medals = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
        for i, s in enumerate(ranked):
            base = get_symbol_base(s.symbol)
            sig_cfg = SIGNALS.get(s.signal_type, {})
            if rank_type == "rvol":      metric = f"RVOL: {s.rvol:.2f}x"
            elif rank_type == "rr":      metric = f"R:R: 1:{s.risk_reward}"
            elif rank_type == "quality": metric = f"Sifat: {s.entry_quality}/100"
            else:                        metric = f"Ishonch: {s.confidence}%"
            msg += f"{medals[i]} <b>{base}</b>  {sig_cfg.get('emoji','')} {metric}  📈{s.trend[:4]}\n"

        await query.edit_message_text(msg, parse_mode=ParseMode.HTML,
                                      reply_markup=ranking_keyboard())
    except Exception as e:
        logger.error(f"Reyting xatosi: {e}")
        await query.edit_message_text(f"❌ Xato: {str(e)[:150]}",
                                      parse_mode=ParseMode.HTML, reply_markup=back_keyboard())


# ============================================================
# MATN XABARLARI
# ============================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user = update.effective_user
    upsert_user(user.id)
    awaiting = context.user_data.get("awaiting")

    if awaiting == "ai_search":
        context.user_data.pop("awaiting", None)
        result = search_knowledge(text.lower())
        if result:
            await update.message.reply_text(
                result["content"], parse_mode=ParseMode.HTML,
                reply_markup=back_keyboard("menu_ai", "◀️ AI Menyu")
            )
        else:
            await update.message.reply_text(
                f"🔍 '<b>{text}</b>' topilmadi.\n\n"
                f"Mavjud mavzular:\n<code>{' '.join(get_all_topics())}</code>",
                parse_mode=ParseMode.HTML,
                reply_markup=back_keyboard("menu_ai", "◀️ AI Menyu")
            )
        return

    if awaiting == "threshold_input":
        context.user_data.pop("awaiting", None)
        try:
            val = int(text)
            if 40 <= val <= 95:
                update_setting(user.id, "alert_threshold", val)
                await update.message.reply_text(
                    f"✅ Signal chegarasi <b>{val}</b> ga o'zgartirildi.",
                    parse_mode=ParseMode.HTML, reply_markup=back_keyboard()
                )
            else:
                await update.message.reply_text("❌ 40–95 oralig'ida raqam kiriting.")
        except ValueError:
            await update.message.reply_text("❌ Raqam kiriting (masalan: 70)")
        return

    # Tezkor tanga qidirish
    sym = normalize_symbol(text.upper())
    if sym in [s.upper() for s in HALAL_COINS]:
        base = get_symbol_base(sym)
        wait_msg = await update.message.reply_text(
            f"🔍 <b>{base}/USDT</b> tahlil qilinmoqda...",
            parse_mode=ParseMode.HTML
        )
        try:
            async with aiohttp.ClientSession() as session:
                signal = await analyze_coin(session, sym, "1h", full_mtf=True)
            if signal:
                settings = get_settings(user.id)
                if settings.get("show_chart", 1):
                    async with aiohttp.ClientSession() as session:
                        await send_chart(
                            context.bot, update.message.chat_id, signal, session,
                            caption=f"📊 <b>{base}/USDT</b> — {signal.timeframe.upper()}"
                        )
                await wait_msg.edit_text(
                    format_signal_message(signal, detailed=True),
                    parse_mode=ParseMode.HTML, reply_markup=back_keyboard()
                )
            else:
                await wait_msg.edit_text("❌ Ma'lumot olib bo'lmadi.")
        except Exception as e:
            await wait_msg.edit_text(f"❌ Xato: {str(e)[:100]}")
        return

    await update.message.reply_text("📋 Menyudan foydalaning:",
                                    reply_markup=main_menu_keyboard())


# ============================================================
# KOMANDALAR
# ============================================================

async def cmd_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    user = update.effective_user
    upsert_user(user.id)
    if args:
        symbol = normalize_symbol(args[0].upper())
        base = get_symbol_base(symbol)
        msg = await update.message.reply_text(f"🔍 <b>{base}</b> tahlil qilinmoqda...",
                                              parse_mode=ParseMode.HTML)
        try:
            async with aiohttp.ClientSession() as session:
                signal = await analyze_coin(session, symbol, "1h", full_mtf=True)
            if signal:
                settings = get_settings(user.id)
                if settings.get("show_chart", 1):
                    async with aiohttp.ClientSession() as session:
                        await send_chart(context.bot, update.message.chat_id,
                                         signal, session)
                await msg.edit_text(
                    format_signal_message(signal, detailed=True),
                    parse_mode=ParseMode.HTML, reply_markup=back_keyboard()
                )
            else:
                await msg.edit_text("❌ Ma'lumot topilmadi.")
        except Exception as e:
            await msg.edit_text(f"❌ Xato: {e}")
    else:
        wl = get_watchlist(user.id)
        await update.message.reply_text("📊 Tanga tanlang:",
                                        reply_markup=coin_select_keyboard(wl, "analyze"))


async def cmd_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    upsert_user(uid)
    watchlist = get_watchlist(uid)
    bases = " | ".join(get_symbol_base(s) for s in watchlist) or "Bo'sh"
    await update.message.reply_text(
        f"⭐ <b>Watchlist:</b> <code>{bases}</code>",
        parse_mode=ParseMode.HTML,
        reply_markup=watchlist_view_keyboard(watchlist)
    )


async def cmd_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    upsert_user(update.effective_user.id)
    msg = await update.message.reply_text("📊 Bozor holati hisoblanmoqda...")
    try:
        async with aiohttp.ClientSession() as session:
            signals = await scan_all_coins(session, HALAL_COINS[:40])
        health = compute_market_health(signals)
        await msg.edit_text(format_market_health(health),
                            parse_mode=ParseMode.HTML, reply_markup=back_keyboard())
    except Exception as e:
        await msg.edit_text(f"❌ Xato: {e}")


# ============================================================
# JOB: 15 DAQIQALIK WATCHLIST SKANERI
# ============================================================

async def job_watchlist_scan(context: ContextTypes.DEFAULT_TYPE):
    """
    Har 15 daqiqada barcha foydalanuvchilarning watchlistini skanerlash.
    Signal o'zgarganda yoki kuchli signal bo'lsa grafik bilan ogohlantirish yuborish.
    """
    logger.info("⏱️ 15-daqiqa watchlist skaneri ishga tushdi")
    users = get_all_active_users()
    if not users:
        return

    async with aiohttp.ClientSession() as session:
        for user in users:
            uid = user["user_id"]
            if not user.get("alerts_on"):
                continue
            settings = get_settings(uid)
            if not settings.get("notify_strong", 1):
                continue

            threshold = settings.get("alert_threshold", ALERT_THRESHOLD)
            watchlist = get_watchlist(uid)
            if not watchlist:
                continue

            for symbol in watchlist:
                try:
                    signal = await analyze_coin(session, symbol, "15m", full_mtf=False)
                    if not signal:
                        continue
                    if signal.confidence < threshold:
                        continue
                    if signal.signal_type not in ("STRONG_BUY", "BUY"):
                        continue
                    if check_alert_cooldown(uid, signal.symbol, 900):  # 15 daqiqa cooldown
                        continue

                    # Signal xabarini yuborish
                    msg = (
                        f"⏱️ <b>15-DAQIQALIK SIGNAL</b>\n\n"
                        + format_signal_message(signal, detailed=False)
                    )
                    await context.bot.send_message(
                        chat_id=uid, text=msg, parse_mode=ParseMode.HTML
                    )

                    # Grafik yuborish
                    if settings.get("show_chart", 1):
                        await send_chart(
                            context.bot, uid, signal, session,
                            caption=f"📊 <b>{get_symbol_base(symbol)}/USDT</b> — 15M\n"
                                    f"Ishonch: <b>{signal.confidence}%</b>"
                        )

                    record_alert(uid, symbol, signal.signal_type,
                                 signal.confidence, signal.price)
                    await asyncio.sleep(0.3)

                except Exception as e:
                    logger.debug(f"Watchlist scan xatosi {symbol}: {e}")


# ============================================================
# JOB: KUCHLI SIGNAL SKANERI (har 10 daqiqa)
# ============================================================

async def job_strong_signal_scan(context: ContextTypes.DEFAULT_TYPE):
    """
    Har 10 daqiqada barcha halol tangalarni skanerlab,
    kuchli signallarni watchlistdagi foydalanuvchilarga yuborish.
    """
    logger.info("🔍 Kuchli signal skaneri ishga tushdi")
    users = get_all_active_users()
    if not users:
        return

    async with aiohttp.ClientSession() as session:
        strong_signals = await find_strong_signals(session, ALERT_THRESHOLD)

    if not strong_signals:
        return

    logger.info(f"🔥 {len(strong_signals)} kuchli signal topildi")

    async with aiohttp.ClientSession() as session:
        for user in users:
            uid = user["user_id"]
            if not user.get("alerts_on"):
                continue
            settings = get_settings(uid)
            if not settings.get("notify_strong", 1):
                continue

            threshold = settings.get("alert_threshold", ALERT_THRESHOLD)
            watchlist = get_watchlist(uid)

            for signal in strong_signals:
                if signal.symbol not in watchlist:
                    continue
                if signal.confidence < threshold:
                    continue
                if check_alert_cooldown(uid, signal.symbol, 3600):
                    continue

                try:
                    msg = "🚨 <b>KUCHLI SIGNAL!</b>\n\n" + format_signal_message(signal, detailed=True)
                    await context.bot.send_message(
                        chat_id=uid, text=msg, parse_mode=ParseMode.HTML
                    )

                    # Grafik yuborish
                    if settings.get("show_chart", 1):
                        await send_chart(
                            context.bot, uid, signal, session,
                            caption=f"🔥 <b>{get_symbol_base(signal.symbol)}/USDT</b> — KUCHLI SIGNAL\n"
                                    f"Ishonch: <b>{signal.confidence}%</b>  "
                                    f"RVOL: <b>{signal.rvol:.2f}x</b>"
                        )

                    record_alert(uid, signal.symbol, signal.signal_type,
                                 signal.confidence, signal.price)
                    await asyncio.sleep(0.3)

                except Exception as e:
                    logger.warning(f"Kuchli signal yuborish xatosi {uid}: {e}")


# ============================================================
# BOTNI SOZLASH VA ISHGA TUSHIRISH
# ============================================================

async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("start",     "Botni ishga tushirish"),
        BotCommand("menu",      "Asosiy menyuni ko'rsatish"),
        BotCommand("signal",    "Tezkor signal olish"),
        BotCommand("watchlist", "Kuzatuv ro'yxatim"),
        BotCommand("market",    "Bozor holati"),
    ])
    logger.info("✅ Bot komandalar o'rnatildi")


def run_bot():
    setup_logging(LOG_LEVEL)

    if not TELEGRAM_BOT_TOKEN:
        logger.critical("❌ TELEGRAM_BOT_TOKEN topilmadi!")
        return

    init_database()

    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Handlerlar
    app.add_handler(CommandHandler("start",     cmd_start))
    app.add_handler(CommandHandler("menu",      cmd_menu))
    app.add_handler(CommandHandler("signal",    cmd_signal))
    app.add_handler(CommandHandler("watchlist", cmd_watchlist))
    app.add_handler(CommandHandler("market",    cmd_market))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Job queue — vaqtinchalik vazifalar
    jq = app.job_queue
    if jq:
        # Har 15 daqiqada watchlist skaneri
        jq.run_repeating(job_watchlist_scan,   interval=900,  first=60,  name="watchlist_15m")
        # Har 10 daqiqada kuchli signal skaneri
        jq.run_repeating(job_strong_signal_scan, interval=600, first=30, name="strong_scanner")
        logger.info("✅ Job queue yoqildi: 15m watchlist + 10m kuchli signal")
    else:
        logger.warning("⚠️ Job queue mavjud emas — python-telegram-bot[job-queue] o'rnating")

    logger.info("🚀 HALOL CRYPTO AI BOT V3.5 ishga tushdi!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    run_bot()
