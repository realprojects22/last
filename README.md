# 🕌 HALOL CRYPTO AI BOT V3.5

**Halol Spot Savdo uchun Professional Telegram Kripto Tahlil Boti**

> ✅ Faqat Spot Savdo | ✅ Faqat Long Pozitsiyalar | ❌ Futures/Leveraj/Short YO'Q

---

## 📋 Xususiyatlar

### 📊 Texnik Indikatorlar
- **RSI** (14 davr) — momentum tahlili
- **EMA 20/50/200** — trend yo'nalishi
- **MACD** (12/26/9) — trend momentumi
- **ADX** (+DI/-DI) — trend kuchi
- **ATR** — volatillik o'lchovi
- **Bollinger Bands** — narx oraliq tahlili
- **Volume & RVOL** — nisbiy hajm tahlili

### 🏦 Smart Money Kontseptsiyalari
- **Order Blocks** — institutsional buyurtmalar zonasi
- **Fair Value Gaps (FVG)** — narx bo'shliqlari
- **Break of Structure (BOS)** — tuzilma sinishi
- **Change of Character (CHoCH)** — trend o'zgarishi
- **Liquidity Sweeps** — likvidlik oqimi
- **Breakout + Retest** — sinish va qayta test

### ⏱️ Ko'p Vaqt Oralig'i Tahlili
- 15 daqiqa | 1 soat | 4 soat | 1 kun
- Og'irlikli kombinatsiya (uzoq vaqt oraliq = ko'proq og'irlik)

### 🎯 Signal Tizimi
| Signal | Ball | Vaziyat |
|--------|------|---------|
| 🔥 KUCHLI SOTIB OLISH | 80-100 | Eng kuchli imkoniyat |
| 🟢 SOTIB OLISH | 60-79 | Yaxshi kirish |
| 🟡 KUTISH | 40-59 | Noaniq sharoit |
| 🔵 FOYDA OLISH | Bearish | Foyda olish vaqti |
| 🟠 XAVF OSHDI | < 40 | Yuqori xavf |

### 📐 Risk Boshqaruvi
- Har signal uchun: **Kirish + Stop Loss + TP1 + TP2 + TP3**
- ATR asosida stop loss
- Resistance asosida take profit
- Risk/Reward nisbati avtomatik

### 📈 Qo'shimcha Xususiyatlar
- **RVOL** (Nisbiy Hajm) tahlili
- **Entry Quality Score** (0-100)
- **Trend Kuchi Reytingi**
- **Top 10 Imkoniyatlar**
- **Bozor Holati Skaneri**
- **Coin Reytingi** (ishonch/RVOL/R:R/sifat)

---

## 🚀 O'rnatish

### 1. Talablar
```
Python 3.9+
pip
```

### 2. Faylni yuklab olish
```bash
git clone <repo_url> halol_crypto_bot
cd halol_crypto_bot
```

### 3. Virtual muhit yaratish (tavsiya etiladi)
```bash
python -m venv venv

# Linux/Mac:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### 4. Kutubxonalarni o'rnatish
```bash
pip install -r requirements.txt
```

### 5. .env faylini yaratish
```bash
cp .env.example .env
```

`.env` faylini oching va to'ldiring:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### 6. Telegram Bot Token olish
1. Telegram da `@BotFather` ga yozing
2. `/newbot` buyrug'ini yuboring
3. Bot nomini kiriting
4. Token nusxasini oling
5. `.env` fayliga joylashtiring

### 7. Botni ishga tushirish
```bash
python bot.py
```

---

## ☁️ Bulutli Deployment

### Railway
```bash
# railway.json yarating:
{
  "build": {"builder": "NIXPACKS"},
  "deploy": {"startCommand": "python bot.py"}
}
```

### Render
```yaml
# render.yaml:
services:
  - type: worker
    name: halol-crypto-bot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python bot.py
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
```

```bash
docker build -t halol-bot .
docker run -e TELEGRAM_BOT_TOKEN=your_token halol-bot
```

### Ubuntu VPS
```bash
# Systemd service:
sudo nano /etc/systemd/system/halol-bot.service

[Unit]
Description=Halol Crypto Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/halol_crypto_bot
ExecStart=/home/ubuntu/halol_crypto_bot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

sudo systemctl enable halol-bot
sudo systemctl start halol-bot
```

### Termux (Android)
```bash
pkg install python
pip install -r requirements.txt
python bot.py
```

---

## ⚙️ Konfiguratsiya

### .env Parametrlari

| Parametr | Standart | Tavsif |
|----------|----------|--------|
| `TELEGRAM_BOT_TOKEN` | — | **Majburiy** |
| `SCAN_INTERVAL` | 600 | Skanerlash intervalı (soniya) |
| `ALERT_THRESHOLD` | 70 | Ogohlantirish chegarasi (0-100) |
| `LOG_LEVEL` | INFO | Log darajasi |
| `DB_NAME` | halol_bot.db | Ma'lumotlar bazasi fayli |
| `CACHE_TTL` | 300 | Kesh muddati (soniya) |
| `MAX_WATCHLIST_SIZE` | 20 | Watchlist chegarasi |
| `ALERT_COOLDOWN` | 3600 | Ogohlantirish oralig'i (soniya) |

---

## 📱 Bot Komandalar

| Komanda | Tavsif |
|---------|--------|
| `/start` | Botni ishga tushirish |
| `/menu` | Asosiy menyuni ko'rsatish |
| `/signal [tanga]` | Tezkor signal olish |
| `/watchlist` | Kuzatuv ro'yxatim |
| `/market` | Bozor holati |

---

## 🕌 Islomiy Tamoyillar

Bu bot quyidagi islomiy moliya tamoyillariga asoslangan:

### ✅ RUXSAT ETILGAN:
- **Spot savdo**: Real aktivni sotib olish
- **Mulkchilik**: Aktiv haqiqatan sizga tegishli
- **Uzoq muddatli ushlab turish**
- **Foyda olish**: Mulkdan daromad topish

### ❌ TAQIQLANGAN:
- **Futures**: Kelajakdagi shartnomalar (gharar)
- **Leverage/Margin**: Qarz mablag'lar (riba)
- **Short Selling**: Mavjud bo'lmagan aktivni sotish
- **Options**: Muddatli shartnomalar

---

## 📁 Fayl Tuzilmasi

```
halol_crypto_bot/
├── bot.py          # Asosiy bot va Telegram handlerlar
├── config.py       # Barcha konfiguratsiya sozlamalari
├── database.py     # SQLite ma'lumotlar bazasi
├── scanner.py      # Bozor skanerlash mexanizmi
├── signals.py      # Texnik tahlil va signal yaratish
├── charts.py       # Professional grafik generatsiya
├── ai_helper.py    # O'rnatilgan bilim bazasi (oflayn)
├── utils.py        # Yordamchi funksiyalar
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🔧 Muammo va Yechimlar

### "Module not found" xatosi
```bash
pip install -r requirements.txt --upgrade
```

### "Token not found" xatosi
- `.env` faylida `TELEGRAM_BOT_TOKEN` to'g'ri kiritilganligini tekshiring

### Grafik ko'rinmasa
```bash
pip install matplotlib mplfinance --upgrade
```

### Binance API xatosi
- Internet ulanishini tekshiring
- VPN ishlatayotgan bo'lsangiz, o'chiring

---

## 📊 Ishlash ko'rsatkichlari

- **RAM**: ~80-150 MB
- **CPU**: Past (asinxron arxitektura)
- **Tarmoq**: O'rtacha (API cache mavjud)
- **Disk**: ~5-50 MB (ma'lumotlar bazasi)

---

## ⚠️ Ogohlantirish

> Bu bot **ta'lim maqsadida** yaratilgan. Signal va tahlillar moliyaviy maslahat hisoblanmaydi.
> Har doim o'z tadqiqotingizni o'tkazing va faqat yo'qotishga tayyor bo'lgan pulni
> investitsiya qiling. Kripto bozori juda o'zgaruvchan.

---

## 📄 Litsenziya

MIT License — erkin foydalaning, o'zgartiring va tarqating.
