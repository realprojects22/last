"""
ai_helper.py - HALOL CRYPTO AI BOT V3.5
O'rnatilgan AI yordamchi va bilim bazasi (OFLAYN)
Tashqi AI API ishlatilmaydi — to'liq mustaqil tizim
"""

from typing import Dict, Optional, List
import re


# ============================================================
# BILIM BAZASI
# ============================================================

KNOWLEDGE_BASE: Dict[str, Dict] = {

    # ================================================================
    # TEXNIK TAHLIL INDIKATORLARI
    # ================================================================

    "rsi": {
        "title": "📊 RSI — Nisbiy Kuch Indeksi",
        "content": """
<b>📊 RSI — Nisbiy Kuch Indeksi (Relative Strength Index)</b>

RSI — narxning tezlik va o'zgarish kattaligini o'lchaydigan momentum indikatori.

<b>📐 Formula:</b>
RSI = 100 − [100 / (1 + (O'rtacha Yutish / O'rtacha Yo'qotish))]

<b>📊 Qiymat talqini:</b>
• <b>0–30</b>: Haddan tashqari sotilgan — tiklash ehtimoli yuqori ✅
• <b>30–50</b>: Ayiqli hududda
• <b>50</b>: Neytral zona
• <b>50–70</b>: Buqali hududda ✅
• <b>70–100</b>: Haddan tashqari sotib olingan — ehtiyotkorlik ⚠️

<b>🎯 Savdo signallari:</b>
• RSI 30 dan pastga tushib, keyin yuqoriga qaytsa — <b>BUY signali</b>
• RSI 70 dan yuqoriga ko'tarilib, keyin pastga tushsa — <b>PROFIT signali</b>
• RSI 50 chizig'idan o'tish — trend tasdiqlash

<b>⚠️ Muhim eslatma:</b>
RSI boshqa indikatorlar bilan birgalikda ishlatilganda kuchliroq signal beradi.
Kuchli trendda RSI uzoq vaqt 70+ yoki 30- da qolishi mumkin.

<b>🕌 Halol qo'llash:</b>
RSI faqat spot pozitsiyalar uchun ishlatiladi. Bot HECH QACHON short signal bermaydi.
""",
        "keywords": ["rsi", "relative strength", "momentum", "overbought", "oversold"]
    },

    "ema": {
        "title": "📈 EMA — Eksponensial Harakatlanuvchi O'rtacha",
        "content": """
<b>📈 EMA — Eksponensial Harakatlanuvchi O'rtacha</b>

EMA oxirgi narxlarga ko'proq og'irlik berib, trend yo'nalishini ko'rsatadi.

<b>📊 Bot qo'llaydigan EMA darajalari:</b>
• <b>EMA20</b>: Qisqa muddatli trend (ko'k chiziq)
• <b>EMA50</b>: O'rta muddatli trend (to'q sariq chiziq)
• <b>EMA200</b>: Uzoq muddatli trend (qizil chiziq)

<b>🎯 Talqin:</b>
<b>Bullish joylashuv:</b>
Narx > EMA20 > EMA50 > EMA200 — eng kuchli sotib olish sharoiti ✅

<b>Bearish joylashuv:</b>
Narx < EMA20 < EMA50 < EMA200 — ehtiyotkorlik ⚠️

<b>✅ EMA kesishuvi signallari:</b>
• EMA20 EMA50 dan yuqoriga kesib o'tsa — Bullish kesishuv (Golden Cross)
• EMA20 EMA50 dan pastga kesib o'tsa — Bearish kesishuv (Death Cross)

<b>🛡️ Support/Resistance sifatida:</b>
EMA20, EMA50 va EMA200 narx uchun dinamik support/resistance vazifasini bajaradi.
""",
        "keywords": ["ema", "exponential", "moving average", "trend", "golden cross"]
    },

    "macd": {
        "title": "📊 MACD — Harakatlanuvchi O'rtacha Konvergentsiya/Divergentsiya",
        "content": """
<b>📊 MACD — Harakatlanuvchi O'rtacha Konvergentsiya/Divergentsiya</b>

MACD trend yo'nalishi va momentumini o'lchaydigan mashhur indikator.

<b>📐 Komponentlar:</b>
• <b>MACD Chizig'i</b>: EMA12 − EMA26
• <b>Signal Chizig'i</b>: MACD ning EMA9
• <b>Histogram</b>: MACD − Signal

<b>🎯 Signal talqini:</b>
<b>Bullish signallar:</b>
✅ MACD signal chizig'idan yuqoriga kesib o'tsa
✅ Histogram manfiydan musbatga o'tsa
✅ MACD nol chizig'idan yuqoriga o'tsa

<b>Bearish signallar (bot PROFIT/RISK beradi):</b>
⚠️ MACD signal chizig'idan pastga kesib o'tsa
⚠️ Histogram musbatdan manfiyga o'tsa

<b>💡 Divergensiya:</b>
• Bullish divergensiya: Narx pastga ketsa, MACD yuqoriga — trendni o'zgarishi mumkin
• Bearish divergensiya: Narx yuqoriga ketsa, MACD pastga — ehtiyotkorlik

<b>🕌 Halol qo'llash:</b>
MACD faqat spot pozitsiyalarni tasdiqlash uchun ishlatiladi.
""",
        "keywords": ["macd", "convergence", "divergence", "histogram", "signal line"]
    },

    "adx": {
        "title": "📊 ADX — O'rtacha Yo'nalish Indeksi",
        "content": """
<b>📊 ADX — O'rtacha Yo'nalish Indeksi (Average Directional Index)</b>

ADX trend kuchini o'lchaydigan indikator (yo'nalishni emas, kuchni).

<b>📊 ADX qiymatlari:</b>
• <b>0–20</b>: Zaif trend yoki yoʻq trend (yandeq bozor)
• <b>20–25</b>: Trend boshlanishi
• <b>25–50</b>: Kuchli trend ✅
• <b>50+</b>: Juda kuchli trend 🔥

<b>📐 Yo'nalish Ko'rsatkichlari:</b>
• <b>+DI</b>: Buqali kuch
• <b>-DI</b>: Ayiqli kuch

<b>🎯 Signal:</b>
• ADX > 25 va +DI > -DI: Kuchli bullish trend ✅
• ADX > 25 va -DI > +DI: Kuchli bearish trend ⚠️

<b>💡 Eslatma:</b>
ADX past bo'lsa (< 20), narx yandeq bozorda yuradi —
bu davrda boshqa indikatorlar kamroq ishonchli.
""",
        "keywords": ["adx", "directional", "trend strength", "di plus", "di minus"]
    },

    "atr": {
        "title": "📊 ATR — O'rtacha Haqiqiy Oraliq",
        "content": """
<b>📊 ATR — O'rtacha Haqiqiy Oraliq (Average True Range)</b>

ATR narx volatilligini o'lchaydigan indikator — yo'nalish ko'rsatmaydi.

<b>📐 Haqiqiy Oraliq (True Range) nima?</b>
TR = max(Yuqori - Past, |Yuqori - Yopilish(oldingi)|, |Past - Yopilish(oldingi)|)
ATR = TR ning 14 kunlik o'rtachasi

<b>🎯 Bot ATR dan foydalanishi:</b>
✅ Stop Loss hisoblash: Narx − (ATR × 1.5)
✅ Take Profit darajalari: Risk/Reward asosida
✅ Pozitsiya hajmi: Kapital × Risk% / ATR

<b>📊 Talqin:</b>
• Yuqori ATR: Kuchli volatillik — katta stop loss kerak
• Past ATR: Past volatillik — tor stop loss mumkin

<b>💡 Pratik foydalanish:</b>
ATR = $2.50 bo'lsa, stop lossni kamida $3.75 (1.5×ATR) uzoqlikda qo'ying.
Bu narxning oddiy shovqinidan himoya qiladi.
""",
        "keywords": ["atr", "true range", "volatility", "stop loss", "position sizing"]
    },

    "bollinger": {
        "title": "📊 Bollinger Bands — Bollinger Tasmalari",
        "content": """
<b>📊 Bollinger Bands — Bollinger Tasmalari</b>

Narx volatilligini va ehtimoliy o'zgarish zonalarini ko'rsatadigan indikator.

<b>📐 Tarkibi:</b>
• <b>Yuqori tasma</b>: SMA20 + (2 × Standart og'ish)
• <b>O'rta chiziq</b>: SMA20 (oddiy harakatlanuvchi o'rtacha)
• <b>Pastki tasma</b>: SMA20 − (2 × Standart og'ish)

<b>🎯 Signal talqini:</b>
✅ Narx pastki tasmaga yaqinlashsa — potentsial sotib olish zonasi
✅ Tasmalar toraysa (Squeezing) — kuchli harakat kutilmoqda
⚠️ Narx yuqori tasmada — haddan tashqari sotib olingan bo'lishi mumkin

<b>📊 BB Squeezing:</b>
Tasmalar torayishi kuchli harakatning belgisi — lekin yo'nalishni bilmaydi.
Boshqa indikatorlar bilan tasdiqlang.

<b>💡 Spot savdoda qo'llash:</b>
Narx pastki tasmaga tegib, RSI past bo'lsa — kuchli BUY muhiti.
Bot bu kombinatsiyani ishonch ballini oshirish uchun ishlatadi.
""",
        "keywords": ["bollinger", "bands", "bb", "volatility", "squeeze", "overbought"]
    },

    "volume": {
        "title": "📊 Hajm Tahlili — Volume Analysis",
        "content": """
<b>📊 Hajm Tahlili — Volume Analysis</b>

Hajm — bozordagi ishtirokchilar faolligini o'lchaydigan eng muhim ko'rsatkich.

<b>📐 Asosiy tamoyillar:</b>
• <b>Narx ↑ + Hajm ↑</b>: Kuchli bullish signal ✅
• <b>Narx ↑ + Hajm ↓</b>: Zaif harakat — sinishi mumkin ⚠️
• <b>Narx ↓ + Hajm ↑</b>: Kuchli bosim — ehtiyotkorlik ⚠️
• <b>Narx ↓ + Hajm ↓</b>: Zaif ayiqli bosim — tiklash ehtimoli

<b>📊 RVOL — Nisbiy Hajm:</b>
RVOL = Joriy hajm ÷ O'rtacha hajm

• RVOL < 1.0: Zaif qiziqish
• RVOL 1.0–2.0: Odatiy qiziqish ✅
• RVOL 2.0–3.0: Kuchli qiziqish 🔥
• RVOL > 3.0: Istisnoli qiziqish 🚀

<b>💡 Hajm spike aniqlash:</b>
Kichik mumda katta hajm — "Smart Money" kirayotgan bo'lishi mumkin.
Bot bu holatni avtomatik aniqlaydi.
""",
        "keywords": ["volume", "hajm", "rvol", "relative volume", "spike", "liquidity"]
    },

    "support": {
        "title": "📊 Support — Tayanch Darajasi",
        "content": """
<b>📊 Support — Tayanch Darajasi</b>

Support — narx pashlashini to'xtatadigan narx darajasi.

<b>🎯 Support qanday shakllanadi?</b>
• Narx bir necha marta bir darajada to'xtab, yuqoriga qaytganda
• Katta buyurtmalar to'plangan joy
• Psixologik muhim darajalar (yumaloq raqamlar)

<b>📊 Support turları:</b>
• <b>Statik support</b>: Gorizontal chiziq
• <b>Dinamik support</b>: EMA20, EMA50, EMA200 darajalari
• <b>Order Block</b>: Katta buyurtmalar joylashgan zona

<b>🛡️ Savdoda support qo'llash:</b>
✅ Support yaqinida sotib olish — past risk kirish
✅ Stop lossni support dan biroz pastga qo'yish
✅ Support sinishi — pozitsiyani yopish signali

<b>💡 Support va Resistance yer almashish:</b>
Singan support keyinchalik resistance bo'lishi mumkin.
""",
        "keywords": ["support", "tayanch", "level", "bounce", "floor"]
    },

    "resistance": {
        "title": "📊 Resistance — Qarshilik Darajasi",
        "content": """
<b>📊 Resistance — Qarshilik Darajasi</b>

Resistance — narx ko'tarilishini to'xtatadigan narx darajasi.

<b>🎯 Resistance qanday shakllanadi?</b>
• Narx bir necha marta bir darajada to'xtab, pastga tushganda
• Foyda olish zonasi (Take Profit region)
• Psixologik to'siqlar

<b>📊 Resistance bilan ishlash:</b>
• <b>Resistance yaqinida</b>: Qisman foyda olish (TP1)
• <b>Resistance sinishi</b>: Kuchli bullish signal ✅
• <b>Retest</b>: Singan resistance support bo'ladi

<b>🛡️ Bot resistance qo'llashi:</b>
✅ Resistance darajalaridan TP1, TP2 hisoblash
✅ Resistance yaqinida ishonch ballini pasaytirish
✅ Breakout + retest tasdiqlash

<b>💡 Muhim:</b>
Resistance qanchalik ko'p sinab ko'rilsa, sinish shunchalik kuchli bo'ladi.
""",
        "keywords": ["resistance", "qarshilik", "level", "breakout", "ceiling"]
    },

    "orderblock": {
        "title": "🟦 Order Block — Buyurtmalar Bloki",
        "content": """
<b>🟦 Order Block — Buyurtmalar Bloki (Smart Money Konsepti)</b>

Order Block — institutional investorlar (katta pullar) buyurtmalar qo'ygan zona.

<b>📐 Bullish Order Block nima?</b>
Kuchli yuqoriga harakatdan oldingi <b>so'nggi ayiqli mum</b> (qizil mum).
Bu zona — katta pul kirgan joy, narx qaytib kelsa, yuqoriga sakrash ehtimoli yuqori.

<b>📐 Bearish Order Block nima?</b>
Kuchli pastga harakatdan oldingi <b>so'nggi buqali mum</b> (yashil mum).
Narx bu zonaga qaytib kelsa, pastga tushishi mumkin.

<b>🎯 Bot Order Block dan foydalanishi:</b>
✅ Bullish OB zonasida: Ishonch ballini oshirish
✅ Bullish OB zonasida Stop Loss hisoblash
⚠️ Bearish OB yaqinida: Xavf ballini oshirish

<b>💡 Order Block qanday topiladi?</b>
• Narx kuchli harakat qilgan joy
• Katta hajm bilan birga kelgan mum
• Qaytib test qilinmagan zona kuchli hisoblanadi
""",
        "keywords": ["order block", "ob", "institutional", "smart money", "zone", "bullish ob"]
    },

    "fvg": {
        "title": "📐 FVG — Adolatli Qiymat Bo'shlig'i",
        "content": """
<b>📐 FVG — Adolatli Qiymat Bo'shlig'i (Fair Value Gap)</b>

FVG — narx tez harakat qilganida qolgan "to'ldirilmagan zona".

<b>📐 Bullish FVG qanday shakllanadi?</b>
3 ta ardiqli mumda:
• Birinchi mumning YUQORI si
• Uchinchi mumning PASTKI si dan past bo'lsa

Bu ikki daraja orasida narx savdo ko'rmagan — bu "bo'shliq".

<b>🎯 FVG qanday ishlatiladi?</b>
Narx ko'pincha bu bo'shliqlarga qaytib keladi ("qayta to'ldirish").
• Bullish FVG: Narx qaytib kelsa, yuqoriga sakrash ehtimoli ✅
• Bearish FVG: Narx qaytib kelsa, pastga tushish ehtimoli ⚠️

<b>🛡️ Bot FVG qo'llashi:</b>
✅ Bullish FVG zonasida: Ishonch ballini oshirish (+5 ball)
✅ FVG ni TP maqsad sifatida ishlatish
✅ Stop Loss uchun FVG pastki qismini ishlatish
""",
        "keywords": ["fvg", "fair value gap", "gap", "imbalance", "inefficiency"]
    },

    "bos": {
        "title": "💥 BOS — Tuzilma Sinishi",
        "content": """
<b>💥 BOS — Tuzilma Sinishi (Break of Structure)</b>

BOS — narx oldingi muhim yuqori yoki pastni sinib o'tishi.

<b>📐 Bullish BOS:</b>
Narx oldingi yuqori (Previous High) ni yuqoriga sinib o'tishi.
Bu — bullish trendning davom etayotganini tasdiqlaydi.

<b>📐 Bearish BOS:</b>
Narx oldingi pastni (Previous Low) pastga sinib o'tishi.
Bu — bearish trendning davom etayotganini ko'rsatadi.

<b>🎯 Bot BOS dan foydalanishi:</b>
✅ Bullish BOS aniqlanganda: +6 ball qo'shiladi
✅ Bullish BOS trendni tasdiqlaydi
✅ BOS + FVG + OB kombinatsiyasi — kuchli signal

<b>💡 BOS va CHoCH farqi:</b>
• BOS: Mavjud trend davomida tuzilma sinishi
• CHoCH: Trendni o'zgarishini ko'rsatadigan sinish
""",
        "keywords": ["bos", "break of structure", "structure break", "previous high", "previous low"]
    },

    "choch": {
        "title": "🔄 CHoCH — Xarakter O'zgarishi",
        "content": """
<b>🔄 CHoCH — Xarakter O'zgarishi (Change of Character)</b>

CHoCH — bozor trendini o'zgarishi haqidagi dastlabki signal.

<b>📐 Bullish CHoCH nima?</b>
Ayiqli trendda (pastga harakat):
• Narx birinchi marta oldingi pastni sinib o'tmaydi
• Yuqoriroq past (Higher Low) shakllanadi
Bu — ayiqlar kuchi kamayganini ko'rsatadi.

<b>📐 Bearish CHoCH nima?</b>
Buqali trendda (yuqoriga harakat):
• Narx birinchi marta oldingi yuqorini sinib o'tmaydi
• Pastroq yuqori (Lower High) shakllanadi

<b>🎯 Bot CHoCH dan foydalanishi:</b>
✅ Bullish CHoCH: +6 ball — trend o'zgarishi signali
✅ BOS tasdiqlasa — yangi bullish trend boshlangan
⚠️ CHoCH bir BOS bilan tasdiqlanmasa — hali noaniq

<b>💡 Amaliy qo'llash:</b>
CHoCH kuzatib, BOS tasdiqlansa — bu kuchli kirish imkoniyati.
""",
        "keywords": ["choch", "change of character", "trend reversal", "higher low", "lower high"]
    },

    "candlestick": {
        "title": "🕯️ Mum Grafiklari — Candlestick Patterns",
        "content": """
<b>🕯️ Mum Grafiklari — Candlestick Patterns</b>

Mum grafiklar Yaponiyada 18-asrda guruch savdosi uchun ixtiro qilingan.

<b>📐 Mum tarkibi:</b>
• <b>Ochilish</b>: Vaqt oralig'i boshlanishidagi narx
• <b>Yopilish</b>: Vaqt oralig'i yakunidagi narx
• <b>Yuqori</b>: Eng yuqori narx
• <b>Past</b>: Eng past narx
• <b>Soya (Fil)</b>: Tana tashqarisidagi narx harakati

<b>🕯️ Muhim mum patternlari:</b>
✅ <b>Hammer</b>: Uzoq pastki soya — bullish signal
✅ <b>Engulfing</b>: Kuchli qarama-qarshi mum — trend o'zgarishi
✅ <b>Doji</b>: Ochilish ≈ Yopilish — noaniqlik
✅ <b>Morning Star</b>: 3 mumli bullish reversal
⚠️ <b>Shooting Star</b>: Uzoq yuqori soya — bearish signal

<b>💡 Bot qo'llashi:</b>
Bot Individual mum patternlarini Order Block va FVG bilan
birgalikda tahlil qiladi.
""",
        "keywords": ["candlestick", "mum", "hammer", "engulfing", "doji", "pattern"]
    },

    "trend": {
        "title": "📈 Trend Tahlili",
        "content": """
<b>📈 Trend Tahlili — Bozor Yo'nalishi</b>

Trend — bozorning umumiy harakatlanish yo'nalishi.

<b>📊 Trend turlari:</b>
🟢 <b>Bullish (Buqali) Trend:</b>
• Yuqoriroq yuqorilar (Higher Highs)
• Yuqoriroq pastlar (Higher Lows)
• Narx EMA lardan yuqorida

🔴 <b>Bearish (Ayiqli) Trend:</b>
• Pastroq yuqorilar (Lower Highs)
• Pastroq pastlar (Lower Lows)
• Narx EMA lardan pastda

⚖️ <b>Sideways (Yandeq) Trend:</b>
• Narx ma'lum oraliqda harakat qiladi
• Support va Resistance aniq belgilangan

<b>🎯 Bot trend aniqlash usuli:</b>
1. Higher Highs / Higher Lows tekshiruvi
2. EMA joylashuvi (EMA20 > EMA50 > EMA200)
3. ADX qiymati (> 25 = kuchli trend)
4. Ko'p vaqt oralig'i tasdiqi

<b>💡 Savdo qoidasi:</b>
Trend yo'nalishida savdo qiling. Trendga qarshi savdo — yuqori xavf.
""",
        "keywords": ["trend", "bullish", "bearish", "sideways", "higher highs", "higher lows"]
    },

    "breakout": {
        "title": "💥 Breakout va Retest",
        "content": """
<b>💥 Breakout va Retest — Sinish va Qayta Test</b>

Breakout — narxning muhim support yoki resistance darajasini sinib o'tishi.

<b>📐 Breakout turlari:</b>
🟢 <b>Bullish Breakout:</b>
Narx resistance ni yuqoriga sinib o'tadi.

🔴 <b>Bearish Breakout:</b>
Narx support ni pastga sinib o'tadi.

<b>🔄 Retest nima?</b>
Breakout dan keyin narx singan darajaga qaytib test qiladi:
• Singan resistance endi support bo'ladi
• Narx bu darajadan "sakrab" ketsa — breakout tasdiqlangan ✅

<b>🎯 Breakout ishonchliligi:</b>
| Shart | Ball |
|-------|------|
| Breakout aniqlangan | +3 ball |
| Retest tasdiqlangan | +7 ball |
| Yuqori hajm bilan | Qo'shimcha tasdiqlash |

<b>💡 Praktik qo'llash:</b>
✅ Retest vaqtida kirish — past xavf, yuqori R:R
⚠️ Retest bo'lmasa — false breakout xavfi bor
""",
        "keywords": ["breakout", "retest", "resistance break", "support break", "sinish"]
    },

    "liquidity": {
        "title": "💧 Likvidlik va Stop Ovlash",
        "content": """
<b>💧 Likvidlik va Likvidlik Oqimi (Liquidity Sweep)</b>

Likvidlik — bozorda mavjud buyurtmalar to'plami.

<b>📐 Stop ovlash (Stop Hunt) nima?</b>
Katta institutsional investorlar (Smart Money):
1. Ko'pchilik stop losslar joylashgan narxni biladi
2. Qisqa muddatda u darajani "sinadi"
3. Boshqalar stop lossini ishga tushiradi (likvidlik oladi)
4. Keyin haqiqiy yo'nalishda harakat qiladi

<b>📊 Bullish Likvidlik Oqimi:</b>
• Narx support ni qisqa muddatga sinadi (pastga)
• Ko'p odamlar stop lossga uchraydi
• Narx tez qaytadi va yuqoriga harakat qiladi ✅
→ Bu aslida kuchli bullish signal!

<b>📊 Bearish Likvidlik Oqimi:</b>
• Narx resistance ni qisqa muddatga sinadi (yuqoriga)
• Keyin tez tushadi ⚠️

<b>🎯 Bot likvidlik oqimini ishlatishi:</b>
✅ Bullish likvidlik oqimi: +5 ball
✅ Kirish imkoniyatini aniqlash
⚠️ Bearish likvidlik oqimi: -5 ball
""",
        "keywords": ["liquidity", "stop hunt", "sweep", "smart money", "institutional"]
    },

    # ================================================================
    # HALOL KRIPTO
    # ================================================================

    "halol": {
        "title": "🕌 Halol Kripto Savdo",
        "content": """
<b>🕌 Halol Kripto Savdo — Islom Tamoyillari</b>

Bu bot faqat islom shariatiga mos savdo usullarini qo'llab-quvvatlaydi.

<b>✅ RUXSAT ETILGAN:</b>
• <b>Spot savdo</b>: Real aktivni sotib olish va sotish
• <b>Uzoq muddatli ushlab turish (HODLing)</b>
• <b>Foyda olish</b>: Mulkka egalik qilib foyda topish
• <b>Risk boshqaruvi</b>: Stop loss va TP darajalar

<b>❌ TAQIQLANGAN:</b>
• <b>Futures savdo</b>: Kelajakdagi shartnomalar — riba/gharar
• <b>Leverage/Margin</b>: Qarz mablag'lar bilan savdo — riba
• <b>Short selling</b>: Mavjud bo'lmagan aktivni sotish
• <b>Options</b>: Muddatli shartnomalar
• <b>CFD</b>: Farq uchun shartnomalar

<b>🎯 Bot tamoyillari:</b>
1. Faqat spot bozor tahlili
2. Faqat LONG (sotib olish) signallari
3. Bearish sharoitda: FOYDA OLISH yoki XAVF OSHDI
4. Kapital himoyasiga ustuvorlik

<b>📚 Islom moliyasi asoslari:</b>
• Riba (foiz) yo'q
• Gharar (haddan ortiq noaniqlik) yo'q
• Maysir (qimor) yo'q
• Haqiqiy mulkka egalik talab qilinadi
""",
        "keywords": ["halol", "islom", "shariah", "spot", "riba", "gharar", "futures"]
    },

    "spot": {
        "title": "💰 Spot Savdo",
        "content": """
<b>💰 Spot Savdo — Qanday Ishlaydi?</b>

Spot savdo — aktivni hozirgi bozor narxida sotib olish va sotish.

<b>📐 Spot savdo jarayoni:</b>
1. <b>Sotib olish</b>: USDT (dollar) bilan BTC sotib olasiz
2. <b>Saqlash</b>: BTC haqiqatan sizga tegishli
3. <b>Sotish</b>: BTC ni USDT ga aylantirish orqali foyda olish

<b>✅ Spot savdoning afzalliklari:</b>
• Haqiqiy mulkchilik — aktiv sizniki
• Cheksiz ushlab turish imkoniyati
• Likvidatsiya xavfi yo'q
• Islomiy tamoyillarga mos ✅

<b>⚠️ Spot savdoning chegaralari:</b>
• Faqat sotib olgan narxdan pastga tushishi — yo'qotish
• Leveraj yo'q — faqat o'z kapitalingiz

<b>🆚 Spot vs Futures farqi:</b>
| Xususiyat | Spot | Futures |
|-----------|------|---------|
| Mulkchilik | ✅ | ❌ |
| Leveraj | Yo'q | Bor |
| Halollik | ✅ | ❌ |
| Xavf | O'rta | Juda Yuqori |

<b>💡 Bot faqat spot signallar beradi.</b>
""",
        "keywords": ["spot", "spot trading", "market", "buy", "sell", "ownership"]
    },

    # ================================================================
    # RISK BOSHQARUVI
    # ================================================================

    "risk": {
        "title": "⚠️ Risk Boshqaruvi",
        "content": """
<b>⚠️ Risk Boshqaruvi — Capital Himoyasi</b>

Muvaffaqiyatli savdoning asosi — kapitalingizni himoya qilish.

<b>🛡️ Asosiy qoidalar:</b>

<b>1. 1-2% qoidasi:</b>
Har bir savdoda kapitalingizning maksimum 1-2% ini xavf ostiga qo'ying.
💰 Kapital: $10,000 → Savdo xavfi: $100-200

<b>2. Stop Loss har doim:</b>
Har bir savdoda stop loss qo'ying.
Stop losssiz savdo — aksiz mashinada yurish.

<b>3. Risk/Reward nisbati:</b>
Minimum 1:2 (yutish ehtimoli yo'qotishdan 2x katta)
✅ 1:3 yoki undan yuqori — ideal

<b>4. Pozitsiya hajmi:</b>
PH = (Kapital × Risk%) ÷ (Narx − Stop Loss)

<b>5. Diversifikatsiya:</b>
Barcha kapitalingizni bitta tangaga qo'ymang.
Kamida 5-10 tanga — xavfni taqsimlash.

<b>📊 Bot risk boshqaruvi:</b>
✅ Har signal: Kirish + SL + TP1 + TP2 + TP3
✅ ATR asosida stop loss
✅ Resistance asosida take profit
✅ R:R nisbati har doim ko'rsatiladi
""",
        "keywords": ["risk", "stop loss", "risk reward", "position size", "capital", "management"]
    },

    "position": {
        "title": "📐 Pozitsiya Hajmi Hisoblash",
        "content": """
<b>📐 Pozitsiya Hajmi Hisoblash — Position Sizing</b>

To'g'ri pozitsiya hajmi — professional savdogarning asosiy ko'nikması.

<b>📐 Formula:</b>
Pozitsiya Hajmi = (Kapital × Risk%) ÷ (Kirish Narxi − Stop Loss)

<b>💡 Misol:</b>
• Kapital: $5,000
• Risk: 2% = $100
• BTC kirish: $65,000
• Stop Loss: $63,500
• Risk per coin: $65,000 − $63,500 = $1,500

<b>Pozitsiya Hajmi:</b>
$100 ÷ $1,500 = 0.0667 BTC

<b>📊 Muhim tamoyillar:</b>
✅ Hech qachon kapitalning 5% dan ko'pini xavf ostiga qo'ymang
✅ Kichik pozitsiyadan boshlang, tajriba ortib, oshiring
✅ Yo'qotish ketma-ketligida pozitsiya hajmini kamaytiring

<b>🛡️ Kapital himoyasi qoidalari:</b>
• Qo'shimcha mablag' sarflash tavsiya etilmaydi
• Hissiyot asosida savdo qilmang
• Reja bo'yicha ish yuring
""",
        "keywords": ["position sizing", "pozitsiya", "capital", "risk percent", "lot size"]
    },

    "portfolio": {
        "title": "📊 Portfolio Diversifikatsiya",
        "content": """
<b>📊 Portfolio Diversifikatsiya — Xavfni Taqsimlash</b>

Diversifikatsiya — turli aktivlarga kapital taqsimlash orqali xavfni kamaytirish.

<b>📊 Tavsiya etilgan taqsimlash:</b>
• <b>60%</b>: Katta kapitalizatsiyali tangalar (BTC, ETH)
• <b>25%</b>: O'rta kapitalizatsiyali tangalar
• <b>15%</b>: Kichik kapitalizatsiyali tangalar (yuqori xavf)

<b>🎯 Diversifikatsiya qoidalari:</b>
✅ Kamida 5-10 tanga
✅ Bir tangaga maksimum 20-25%
✅ Bir sektorda maksimum 40%
✅ Muntazam balanslashtirish

<b>💡 Bot portfolio strategiyasi:</b>
Watchlist orqali turli tangalarni kuzating.
Kuchli signallar aniqlanganda xavf taqsimlangan holda kiring.

<b>⚠️ Eslatma:</b>
Bu moliyaviy maslahat emas. Har doim o'z tadqiqotingizni o'tkazing.
""",
        "keywords": ["portfolio", "diversification", "allocation", "risk", "balance"]
    },

    # ================================================================
    # BOZOR TUSHUNCHALARI
    # ================================================================

    "bullmarket": {
        "title": "🐂 Bull Bozor (Buqali Bozor)",
        "content": """
<b>🐂 Bull Bozor — Yuqoriga Yo'nalgan Bozor</b>

Bull bozor — uzoq muddatli narx ko'tarilishi davri.

<b>📊 Belgilari:</b>
• Narxlar 20%+ ko'tarilgan (paslikdan)
• Investorlar kayfiyati ijobiy
• Hajm yuqori
• Media ijobiy yangiliklar

<b>🎯 Bull bozorda strategiya:</b>
✅ Trenddagi tangalarga kiring
✅ Pullback (qisqa muddatli tushish) da sotib oling
✅ TP darajalarini ketma-ket oling
✅ Trailing stop loss ishlating

<b>💡 Kripto bull bozor sikllari:</b>
• Bitcoin Halving (4 yilda bir) — kuchli katalizator
• Institutsional qabul
• Regulyatorlik sohaligi
""",
        "keywords": ["bull market", "bull", "buqa", "uptrend", "rally", "growth"]
    },

    "bearmarket": {
        "title": "🐻 Bear Bozor (Ayiqli Bozor)",
        "content": """
<b>🐻 Bear Bozor — Pastga Yo'nalgan Bozor</b>

Bear bozor — uzoq muddatli narx tushishi davri.

<b>📊 Belgilari:</b>
• Narxlar 20%+ tushgan (yuksakdan
• Investorlar kayfiyati salbiy
• Hajm past (ko'pincha)
• Media salbiy yangiliklar

<b>🛡️ Bear bozorda strategiya:</b>
✅ Foyda olish (FOYDA OLISH signali)
✅ Kichik pozitsiyalar ushlab turish
✅ Stablecoin da saqlanish
✅ DCA (Dollar Cost Averaging) — asta-sekin kirish

<b>🕌 Halol yondashuv:</b>
Bear bozorda bot SHORT signal bermaydi.
Faqat FOYDA OLISH va XAVF OSHDI signallari.
Kapitalingizni himoya qiling va yuqori sifatli tangalarda qoling.

<b>💡 Eslatma:</b>
Bear bozor ham o'tadi. Sabr — muvaffaqiyatning kaliti.
""",
        "keywords": ["bear market", "bear", "ayiq", "downtrend", "crash", "winter"]
    },
}


# ============================================================
# BILIM BAZASINI IZLASH
# ============================================================

def search_knowledge(query: str) -> Optional[Dict]:
    """Bilim bazasidan mavzuni izlash."""
    query_lower = query.lower().strip()

    # To'g'ridan-to'g'ri kalit so'z tekshiruvi
    for key, data in KNOWLEDGE_BASE.items():
        if query_lower == key:
            return data

    # Kalit so'zlar bo'yicha izlash
    best_match = None
    best_score = 0

    for key, data in KNOWLEDGE_BASE.items():
        score = 0
        keywords = data.get("keywords", [])

        # Kalit so'z bilan to'liq moslik
        for kw in keywords:
            if query_lower == kw:
                score += 10
            elif query_lower in kw or kw in query_lower:
                score += 5

        # Sarlavha bilan moslik
        title_lower = data.get("title", "").lower()
        if query_lower in title_lower:
            score += 3

        if score > best_score:
            best_score = score
            best_match = data

    return best_match if best_score > 0 else None


def get_all_topics() -> List[str]:
    """Barcha mavzular ro'yxatini olish."""
    return list(KNOWLEDGE_BASE.keys())


# ============================================================
# AI MENYU KONTENTI
# ============================================================

AI_MENU_SECTIONS = {
    "basics": {
        "title": "📚 Kripto Asoslari",
        "topics": ["bullmarket", "bearmarket", "trend", "candlestick"],
        "emoji": "📚"
    },
    "technical": {
        "title": "📈 Texnik Tahlil",
        "topics": ["rsi", "ema", "macd", "adx", "atr", "bollinger", "volume"],
        "emoji": "📈"
    },
    "spot_trading": {
        "title": "💰 Spot Savdo",
        "topics": ["spot", "support", "resistance", "breakout", "liquidity"],
        "emoji": "💰"
    },
    "halal_crypto": {
        "title": "🕌 Halol Kripto",
        "topics": ["halol"],
        "emoji": "🕌"
    },
    "risk_management": {
        "title": "⚠️ Risk Boshqaruvi",
        "topics": ["risk", "position", "portfolio"],
        "emoji": "⚠️"
    },
    "smart_money": {
        "title": "🏦 Smart Money",
        "topics": ["orderblock", "fvg", "bos", "choch"],
        "emoji": "🏦"
    },
}


def get_section_topics(section_key: str) -> List[Dict]:
    """Bo'lim mavzularini olish."""
    section = AI_MENU_SECTIONS.get(section_key, {})
    topics = section.get("topics", [])
    result = []
    for topic_key in topics:
        if topic_key in KNOWLEDGE_BASE:
            result.append({
                "key": topic_key,
                "title": KNOWLEDGE_BASE[topic_key]["title"],
            })
    return result


def get_topic_content(topic_key: str) -> Optional[str]:
    """Mavzu mazmunini olish."""
    data = KNOWLEDGE_BASE.get(topic_key)
    if data:
        return data["content"]
    return None
