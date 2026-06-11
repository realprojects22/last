"""
charts.py - HALOL CRYPTO AI BOT V3.5
Professional qoʻngʻiroq grafiklari - Kirish, Stop Loss, TP darajalari
"""

import io
import logging
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from matplotlib.gridspec import GridSpec
from typing import Optional, List, Tuple

from signals import SignalResult, OHLCV
from config import CHART_CONFIG, INDICATOR_PARAMS
from utils import ema, sma, calc_rsi, calc_macd

logger = logging.getLogger(__name__)

# Qoʻngʻiroq konfiguratsiyasini tortib olish
CC = CHART_CONFIG
P = INDICATOR_PARAMS


# ============================================================
# ASOSIY GRAFIK YARATISH
# ============================================================

def generate_chart(ohlcv: OHLCV, signal: SignalResult) -> Optional[bytes]:
    """
    Professional dark theme grafik yaratish.
    Candlestick + EMA + Support/Resistance + Order Blocks +
    FVG + Entry/SL/TP + Volume + RSI + MACD panellari.
    """
    try:
        n = min(ohlcv.length, 100)  # Oxirgi 100 mum
        o = ohlcv.open[-n:]
        h = ohlcv.high[-n:]
        lo = ohlcv.low[-n:]
        c = ohlcv.close[-n:]
        v = ohlcv.volume[-n:]
        x = np.arange(n)

        fig = plt.figure(figsize=CC["FIGSIZE"], dpi=CC["DPI"])
        fig.patch.set_facecolor(CC["BACKGROUND_COLOR"])

        gs = GridSpec(
            4, 1, figure=fig,
            height_ratios=[5, 1.5, 1.5, 1.5],
            hspace=0.04
        )

        ax_price  = fig.add_subplot(gs[0])
        ax_vol    = fig.add_subplot(gs[1], sharex=ax_price)
        ax_rsi    = fig.add_subplot(gs[2], sharex=ax_price)
        ax_macd   = fig.add_subplot(gs[3], sharex=ax_price)

        for ax in [ax_price, ax_vol, ax_rsi, ax_macd]:
            ax.set_facecolor(CC["BACKGROUND_COLOR"])
            ax.tick_params(colors=CC["TEXT_COLOR"], labelsize=8)
            ax.spines[:].set_color(CC["GRID_COLOR"])
            ax.grid(color=CC["GRID_COLOR"], linewidth=0.5, alpha=0.7)

        # ---- MUBDIR GRAFIK (CANDLESTICK) ----
        _draw_candlesticks(ax_price, x, o, h, lo, c)

        # ---- EMA CHIZIQLARI ----
        _draw_emas(ax_price, c, x, n)

        # ---- SUPPORT & RESISTANCE ----
        struct = signal.structure
        if struct.get("support"):
            ax_price.axhline(
                struct["support"], color=CC["SUPPORT_COLOR"],
                linewidth=1.5, linestyle="--", alpha=0.8, label="Support"
            )
        if struct.get("resistance"):
            ax_price.axhline(
                struct["resistance"], color=CC["RESISTANCE_COLOR"],
                linewidth=1.5, linestyle="--", alpha=0.8, label="Resistance"
            )

        # ---- ORDER BLOCKS ----
        ob_bull = struct.get("order_block_bull")
        if ob_bull and isinstance(ob_bull, (list, tuple)) and len(ob_bull) == 2:
            _draw_zone(ax_price, x, ob_bull[0], ob_bull[1], CC["OB_BULL_COLOR"], "Bull OB")

        ob_bear = struct.get("order_block_bear")
        if ob_bear and isinstance(ob_bear, (list, tuple)) and len(ob_bear) == 2:
            _draw_zone(ax_price, x, ob_bear[0], ob_bear[1], CC["OB_BEAR_COLOR"], "Bear OB")

        # ---- FVG ZONASI ----
        fvg_bull = struct.get("fvg_bull")
        if fvg_bull and isinstance(fvg_bull, (list, tuple)) and len(fvg_bull) == 2:
            _draw_zone(ax_price, x, fvg_bull[0], fvg_bull[1], CC["FVG_COLOR"], "FVG")

        # ---- KIRISH, STOP LOSS, TP DARAJALARI ----
        price = signal.price
        if price > 0:
            ax_price.axhline(price, color=CC["ENTRY_COLOR"],
                             linewidth=2, linestyle="-", alpha=0.9)
            ax_price.annotate(
                f"📍 Kirish: {_fmt(price)}",
                xy=(n - 1, price), xytext=(n - 15, price),
                color=CC["ENTRY_COLOR"], fontsize=8, fontweight="bold",
                va="center"
            )

        if signal.stop_loss > 0:
            ax_price.axhline(signal.stop_loss, color=CC["SL_COLOR"],
                             linewidth=1.5, linestyle="-.", alpha=0.9)
            ax_price.annotate(
                f"🛑 SL: {_fmt(signal.stop_loss)}",
                xy=(n - 1, signal.stop_loss), xytext=(n - 15, signal.stop_loss),
                color=CC["SL_COLOR"], fontsize=7, va="center"
            )

        _draw_tp_levels(ax_price, signal, n)

        # ---- GRAFIK SARLAVHASI ----
        from config import SIGNALS
        sig_info = SIGNALS.get(signal.signal_type, {})
        sig_emoji = sig_info.get("emoji", "📊")
        sig_name = sig_info.get("name", signal.signal_type)

        title = (
            f"{signal.symbol} | {sig_emoji} {sig_name} | "
            f"Ishonch: {signal.confidence}% | Kirish Sifati: {signal.entry_quality}/100 | "
            f"{signal.timeframe.upper()}"
        )
        ax_price.set_title(title, color=CC["TEXT_COLOR"], fontsize=10,
                           fontweight="bold", pad=8)
        ax_price.set_ylabel("Narx", color=CC["TEXT_COLOR"], fontsize=8)

        # ---- HAJM PANELI ----
        _draw_volume(ax_vol, x, v, o, c)
        ax_vol.set_ylabel("Hajm", color=CC["TEXT_COLOR"], fontsize=7)

        # ---- RSI PANELI ----
        _draw_rsi(ax_rsi, c, x, n)
        ax_rsi.set_ylabel("RSI", color=CC["TEXT_COLOR"], fontsize=7)

        # ---- MACD PANELI ----
        _draw_macd(ax_macd, c, x, n)
        ax_macd.set_ylabel("MACD", color=CC["TEXT_COLOR"], fontsize=7)
        ax_macd.set_xlabel("Mumlar", color=CC["TEXT_COLOR"], fontsize=8)

        # X o'qi belgilari
        plt.setp(ax_price.get_xticklabels(), visible=False)
        plt.setp(ax_vol.get_xticklabels(), visible=False)
        plt.setp(ax_rsi.get_xticklabels(), visible=False)

        plt.tight_layout(pad=0.5)

        # Byte formatida eksport
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight",
                    facecolor=CC["BACKGROUND_COLOR"], dpi=CC["DPI"])
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    except Exception as e:
        logger.error(f"Grafik yaratish xatosi: {e}")
        try:
            plt.close("all")
        except Exception:
            pass
        return None


# ============================================================
# CANDLESTICK CHIZISH
# ============================================================

def _draw_candlesticks(ax, x, o, h, lo, c):
    """Candlestick mumlarni chizish."""
    width = 0.6
    for i in range(len(x)):
        color = CC["UP_COLOR"] if c[i] >= o[i] else CC["DOWN_COLOR"]
        # Shadow (fil)
        ax.plot([x[i], x[i]], [lo[i], h[i]], color=color, linewidth=0.8, alpha=0.9)
        # Tana
        body_low = min(o[i], c[i])
        body_high = max(o[i], c[i])
        ax.add_patch(FancyBboxPatch(
            (x[i] - width / 2, body_low),
            width, body_high - body_low,
            linewidth=0, color=color, alpha=0.85
        ))


# ============================================================
# EMA CHIZIQLARI
# ============================================================

def _draw_emas(ax, close: np.ndarray, x, n: int):
    """EMA20, EMA50, EMA200 chizish."""
    full_close = close  # To'liq ma'lumot kerak
    ema20 = ema(full_close, P["EMA_SHORT"])[-n:]
    ema50 = ema(full_close, P["EMA_MID"])[-n:]
    ema200 = ema(full_close, P["EMA_LONG"])[-n:]

    valid20 = ema20[ema20 > 0]
    valid50 = ema50[ema50 > 0]
    valid200 = ema200[ema200 > 0]

    if len(valid20) > 5:
        start20 = n - len(valid20)
        ax.plot(x[start20:], valid20, color=CC["EMA20_COLOR"],
                linewidth=1.2, label="EMA20", alpha=0.9)
    if len(valid50) > 5:
        start50 = n - len(valid50)
        ax.plot(x[start50:], valid50, color=CC["EMA50_COLOR"],
                linewidth=1.2, label="EMA50", alpha=0.9)
    if len(valid200) > 5:
        start200 = n - len(valid200)
        ax.plot(x[start200:], valid200, color=CC["EMA200_COLOR"],
                linewidth=1.5, label="EMA200", alpha=0.9)

    ax.legend(loc="upper left", fontsize=7, facecolor=CC["BACKGROUND_COLOR"],
              labelcolor=CC["TEXT_COLOR"], framealpha=0.7)


# ============================================================
# ZONA CHIZISH (Order Block / FVG)
# ============================================================

def _draw_zone(ax, x, low_price: float, high_price: float, color: str, label: str):
    """Rang zonasini chizish."""
    ax.axhspan(low_price, high_price, color=color, alpha=0.3)
    mid = (low_price + high_price) / 2
    ax.annotate(label, xy=(len(x) - 1, mid), color=color,
                fontsize=7, va="center", alpha=0.8)


# ============================================================
# TP DARAJALARI
# ============================================================

def _draw_tp_levels(ax, signal: SignalResult, n: int):
    """TP1, TP2, TP3 darajalarini chizish."""
    tp_data = [
        (signal.tp1, CC["TP1_COLOR"], "TP1"),
        (signal.tp2, CC["TP2_COLOR"], "TP2"),
        (signal.tp3, CC["TP3_COLOR"], "TP3"),
    ]
    for tp_price, color, label in tp_data:
        if tp_price > 0:
            ax.axhline(tp_price, color=color, linewidth=1.2,
                       linestyle=":", alpha=0.8)
            ax.annotate(
                f"🎯 {label}: {_fmt(tp_price)}",
                xy=(n - 1, tp_price), xytext=(n - 15, tp_price),
                color=color, fontsize=7, va="center"
            )


# ============================================================
# HAJM PANELI
# ============================================================

def _draw_volume(ax, x, v, o, c):
    """Hajm panelini chizish."""
    colors = [CC["UP_COLOR"] if c[i] >= o[i] else CC["DOWN_COLOR"] for i in range(len(x))]
    ax.bar(x, v, color=colors, alpha=0.7, width=0.7)

    vol_ma = sma(v, min(20, len(v)))
    valid_ma = vol_ma[~np.isnan(vol_ma)]
    if len(valid_ma) > 5:
        start = len(v) - len(valid_ma)
        ax.plot(x[start:], valid_ma, color="#ffa657", linewidth=1.0, alpha=0.8)


# ============================================================
# RSI PANELI
# ============================================================

def _draw_rsi(ax, close: np.ndarray, x, n: int):
    """RSI panelini chizish."""
    from utils import rsi as calc_rsi_util  # noqa
    rsi_vals = calc_rsi_util(close, P["RSI_PERIOD"])[-n:]

    valid_mask = rsi_vals > 0
    if valid_mask.sum() > 5:
        ax.plot(x[valid_mask], rsi_vals[valid_mask],
                color="#79c0ff", linewidth=1.2, alpha=0.9)

    ax.axhline(70, color=CC["DOWN_COLOR"], linewidth=0.8, linestyle="--", alpha=0.6)
    ax.axhline(30, color=CC["UP_COLOR"], linewidth=0.8, linestyle="--", alpha=0.6)
    ax.fill_between(x[valid_mask], rsi_vals[valid_mask], 70,
                    where=(rsi_vals[valid_mask] > 70), color=CC["DOWN_COLOR"],
                    alpha=0.15)
    ax.fill_between(x[valid_mask], rsi_vals[valid_mask], 30,
                    where=(rsi_vals[valid_mask] < 30), color=CC["UP_COLOR"],
                    alpha=0.15)
    ax.set_ylim(0, 100)


# ============================================================
# MACD PANELI
# ============================================================

def _draw_macd(ax, close: np.ndarray, x, n: int):
    """MACD panelini chizish."""
    from utils import macd as calc_macd_util  # noqa
    macd_line, signal_line, histogram = calc_macd_util(
        close, P["MACD_FAST"], P["MACD_SLOW"], P["MACD_SIGNAL"]
    )
    macd_line = macd_line[-n:]
    signal_line = signal_line[-n:]
    histogram = histogram[-n:]

    colors = [CC["UP_COLOR"] if h >= 0 else CC["DOWN_COLOR"] for h in histogram]
    ax.bar(x, histogram, color=colors, alpha=0.5, width=0.7)

    valid_macd = macd_line != 0
    if valid_macd.sum() > 5:
        ax.plot(x[valid_macd], macd_line[valid_macd],
                color="#79c0ff", linewidth=1.0, alpha=0.9, label="MACD")
        ax.plot(x[valid_macd], signal_line[valid_macd],
                color="#ffa657", linewidth=1.0, alpha=0.9, label="Signal")
    ax.axhline(0, color=CC["GRID_COLOR"], linewidth=0.8, alpha=0.8)
    ax.legend(loc="upper left", fontsize=6, facecolor=CC["BACKGROUND_COLOR"],
              labelcolor=CC["TEXT_COLOR"], framealpha=0.5)


# ============================================================
# YORDAMCHI FUNKSIYA
# ============================================================

def _fmt(price: float) -> str:
    """Narxni qisqacha formatlash."""
    if price >= 1000:
        return f"${price:,.2f}"
    elif price >= 1:
        return f"${price:.4f}"
    elif price >= 0.001:
        return f"${price:.6f}"
    else:
        return f"${price:.8f}"
