import requests, hmac, hashlib, time, os, io, json
from PIL import Image
import pytesseract
import cv2
import numpy as np
from datetime import datetime

# KONFIGURASI
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT = "YOUR_CHAT_ID"
GROQ_KEY = "YOUR_GROQ_API_KEY"
INDODAX_KEY = "YOUR_INDODAX_KEY"
INDODAX_SECRET = "YOUR_INDODAX_SECRET"

# ==================== STRATEGI SCALPING AGRESIF ====================
MODAL = 50000  # Modal per trade
PAIRS = ["btc_idr", "eth_idr", "trx_idr", "bnb_idr"]  # Pair utama
TP = 0.008  # Take Profit 0.8% (aggressive scalping)
SL = 0.003  # Stop Loss 0.3% (tight)
TRAILING = 0.005  # Trailing stop 0.5%
MIN_VOLUME = 100000000  # Minimum volume IDR untuk trade
MAX_POSITIONS = 4  # Max posisi terbuka
SCALP_CHECK_INTERVAL = 5  # Check setiap 5 detik untuk scalping

# ==================== AGGRESSIVE GREED PARAMETERS ====================
GREED_MODE = True  # Enable aggressive scalping
QUICK_EXIT = True  # Exit cepat saat profit minimal
MIN_PROFIT_IDR = 5000  # Minimal profit Rp 5000 untuk exit
PYRAMID_TRADING = True  # Add position saat trend kuat
MARTINGALE_ENABLED = False  # Double lot saat loss (RISKY!)
MAX_LOSS_DAILY = 500000  # Max loss per hari (Rp 500k)

# ==================== TELEGRAM ====================
def tg(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={"chat_id": TELEGRAM_CHAT, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except:
        pass

def send_photo(photo_path, caption=""):
    try:
        with open(photo_path, 'rb') as f:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto",
            data={"chat_id": TELEGRAM_CHAT, "caption": caption, "parse_mode": "HTML"},
            files={"photo": f}, timeout=10)
    except:
        pass

# ==================== IMAGE PROCESSING ====================
def download_image_from_telegram(file_id):
    """Download gambar dari Telegram"""
    try:
        file_info = requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile",
            params={"file_id": file_id},
            timeout=10
        ).json()
        
        if not file_info.get("ok"):
            return None
            
        file_path = file_info["result"]["file_path"]
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
        
        img_data = requests.get(file_url, timeout=10).content
        return Image.open(io.BytesIO(img_data))
    except Exception as e:
        print(f"Download error: {e}")
        return None

def read_text_from_image(image):
    """Baca text dari gambar menggunakan Tesseract OCR"""
    try:
        text = pytesseract.image_to_string(image, lang='ind+eng')
        return text.strip() if text else "Tidak ada text"
    except Exception as e:
        return f"OCR Error: {e}"

def detect_support_resistance(image):
    """Detect support & resistance dari chart image"""
    try:
        img_array = np.array(image)
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Detect edges
        edges = cv2.Canny(gray, 50, 150)
        
        # Detect lines (support/resistance)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 50, minLineLength=100, maxLineGap=10)
        
        support_resistance = []
        if lines is not None:
            for line in lines[:10]:
                x1, y1, x2, y2 = line[0]
                if abs(y2 - y1) < 10:  # Horizontal line
                    y_pos = (y1 + y2) // 2
                    support_resistance.append({
                        "type": "Support/Resistance",
                        "level": y_pos,
                        "strength": "Medium"
                    })
        
        if not support_resistance:
            return [{"type": "Analysis", "info": "Tidak terdeteksi support/resistance yang jelas"}]
        
        return support_resistance[:5]
    except Exception as e:
        return [{"error": f"Detection error: {e}"}]

def analyze_chart_image(image):
    """Analisis keseluruhan gambar chart"""
    try:
        img_array = np.array(image)
        mean_brightness = np.mean(img_array)
        
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        
        analysis = {
            "brightness": round(float(mean_brightness), 2),
            "width": image.width,
            "height": image.height,
            "format": "Chart detected"
        }
        
        return analysis
    except Exception as e:
        return {"error": str(e)}

# ==================== AI GROQ ====================
def groq(tanya, ctx=""):
    try:
        h = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
        system = f"""Kamu adalah MASTER TRADER SCALPER AGRESIF dengan keahlian ganda:

1. MASTER SCALPER PROFESIONAL:
- AGGRESSIVE SCALPING (Quick in/out, micro profit)
- Greed Strategy (Maksimalkan setiap profit kecil)
- Pyramid Trading (Add position saat strength)
- Micro Trend Recognition
- 1-5 minute chart analysis
- High frequency trading mindset
- Risk/Reward ratio optimization
- Market Maker Psychology
- Support/Resistance pada micro level

2. MASTER IT & CODING:
- Python, JavaScript, Java
- API Integration & Automation
- Database & Real-time processing
- Machine Learning basics
- Trading Bot Development
- Risk Management Systems

STRATEGI SCALPING GREED ANDA:
- TP: 0.8% (Quick profit)
- SL: 0.3% (Tight stop)
- Max Position: 4 terbuka
- Target: 20-50 trades/hari
- Pair: BTC, ETH, TRX, BNB IDR

Jawab dalam bahasa Indonesia profesional.
Berikan strategi agresif tapi tetap managed risk.
Konteks pasar: {ctx}"""
        
        p = {"model": "llama-3.1-8b-instant", "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": tanya}],
        "max_tokens": 600}
        
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
        headers=h, json=p, timeout=30)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"AI error: {e}"

# ==================== INDODAX API ====================
def sign(p):
    b = "&".join(f"{k}={v}" for k, v in sorted(p.items()))
    return hmac.new(INDODAX_SECRET.encode(), b.encode(), hashlib.sha512).hexdigest()

def priv(m, p={}):
    d = {"method": m, "nonce": str(int(time.time()*1000)), **p}
    try:
        r = requests.post("https://indodax.com/tapi", data=d,
        headers={"Key": INDODAX_KEY, "Sign": sign(d)}, timeout=10)
        j = r.json()
        return j.get("return", {}) if j.get("success") == 1 else {}
    except:
        return {}

def tick(pair):
    try:
        r = requests.get(f"https://indodax.com/api/{pair}/ticker", timeout=10)
        return r.json().get("ticker", {})
    except:
        return {}

def get_trades(pair):
    try:
        r = requests.get(f"https://indodax.com/api/{pair}/trades", timeout=10)
        return r.json() if isinstance(r.json(), list) else []
    except:
        return []

def get_order_book(pair):
    """Get order book untuk analisis depth"""
    try:
        r = requests.get(f"https://indodax.com/api/{pair}/depth", timeout=10)
        return r.json()
    except:
        return {}

# ==================== TECHNICAL ANALYSIS - SCALPING FOCUSED ====================
def calc_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50
    g, l = [], []
    for i in range(1, len(prices)):
        d = prices[i] - prices[i-1]
        g.append(max(d, 0))
        l.append(max(-d, 0))
    ag = sum(g[-period:]) / period
    al = sum(l[-period:]) / period
    return round(100 - (100 / (1 + (ag / al if al else 1))), 1)

def calc_ema(prices, period):
    if not prices:
        return 0
    k = 2 / (period + 1)
    ema = prices[0]
    for p in prices[1:]:
        ema = p * k + ema * (1 - k)
    return round(ema, 2)

def calc_macd(prices):
    if len(prices) < 26:
        return 0, 0
    ema12 = calc_ema(prices, 12)
    ema26 = calc_ema(prices, 26)
    macd = ema12 - ema26
    signal = calc_ema([macd], 9)
    return round(macd, 4), round(signal, 4)

def calc_bb(prices, period=20):
    if len(prices) < period:
        return 0, 0, 0
    r = prices[-period:]
    mid = sum(r) / period
    std = (sum((p - mid)**2 for p in r) / period)**0.5
    return round(mid - 2*std, 2), round(mid, 2), round(mid + 2*std, 2)

def calc_stoch(prices, period=14):
    if len(prices) < period:
        return 50, 50
    high = max(prices[-period:])
    low = min(prices[-period:])
    if high == low:
        return 50, 50
    k = round((prices[-1] - low) / (high - low) * 100, 1)
    return k, k

def calc_momentum(prices, period=5):
    """Calculate momentum untuk scalping"""
    if len(prices) < period:
        return 0
    return round((prices[-1] - prices[-period]) / prices[-period] * 100, 2)

def calc_cci(prices, period=20):
    """Commodity Channel Index untuk scalping"""
    if len(prices) < period:
        return 0
    tp = prices[-period:]
    sma = sum(tp) / period
    mad = sum(abs(p - sma) for p in tp) / period
    cci = (tp[-1] - sma) / (0.015 * mad) if mad else 0
    return round(cci, 2)

def detect_scalp_entry(prices, volume_trend):
    """Detect aggressive scalp entry signal"""
    if len(prices) < 5:
        return "HOLD"
    
    rsi = calc_rsi(prices)
    mom = calc_momentum(prices, 5)
    cci = calc_cci(prices, 20)
    
    # AGGRESSIVE BUY SIGNAL
    if rsi < 35 and mom > 0.5 and volume_trend > 0:
        return "AGGRESSIVE_BUY"
    elif rsi < 45 and mom > 0 and cci > 0:
        return "BUY"
    
    # AGGRESSIVE SELL SIGNAL
    if rsi > 65 and mom < -0.5 and volume_trend < 0:
        return "AGGRESSIVE_SELL"
    elif rsi > 55 and mom < 0 and cci < 0:
        return "SELL"
    
    return "HOLD"

def quick_scalp_analysis(pair):
    """Quick analysis untuk micro scalping (5-15 menit)"""
    trades = get_trades(pair)
    t = tick(pair)
    if not trades or not t:
        return None
    
    prices = [float(x["price"]) for x in trades[:30]][::-1]
    price = float(t["last"])
    vol = float(t.get("vol_idr", 0))
    
    rsi = calc_rsi(prices, 9)  # 9 period untuk scalp
    mom = calc_momentum(prices, 3)
    cci = calc_cci(prices, 10)
    ema5 = calc_ema(prices, 5)
    ema10 = calc_ema(prices, 10)
    
    scalp_signal = detect_scalp_entry(prices, 1 if mom > 0 else -1)
    
    # Scalp score
    scalp_score = 0
    if rsi < 30:
        scalp_score += 40
    elif rsi > 70:
        scalp_score -= 40
    
    if ema5 > ema10:
        scalp_score += 30
    elif ema5 < ema10:
        scalp_score -= 30
    
    if mom > 0.5:
        scalp_score += 30
    
    confidence = abs(scalp_score)
    
    return {
        "pair": pair,
        "price": price,
        "vol": vol,
        "rsi": rsi,
        "momentum": mom,
        "cci": cci,
        "ema5": ema5,
        "ema10": ema10,
        "signal": scalp_signal,
        "confidence": confidence,
        "scalp_score": scalp_score
    }

# ==================== STATE & VARIABLES ====================
STATE = {
    "pos": {},  # {pair: {e, c, peak, entry_time, type}}
    "pnl": 0,
    "tr": 0,  # Total trades
    "wins": 0,
    "losses": 0,
    "active": True,
    "start": time.time(),
    "last_report": time.time(),
    "daily_pnl": 0,
    "daily_trades": 0,
    "day_start": datetime.now().date(),
    "last_scalp_check": {}
}
offset = 0

def get_updates():
    global offset
    try:
        r = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates",
        params={"offset": offset, "timeout": 5}, timeout=10)
        return r.json().get("result", [])
    except:
        return []

def market_ctx():
    ctx = ""
    for pair in PAIRS:
        a = quick_scalp_analysis(pair)
        if a:
            ctx += f"{pair.upper()}: {a['price']:,.0f} RSI={a['rsi']} Signal={a['signal']} Score={a['scalp_score']}\n"
    return ctx

def send_report():
    wr = round(STATE["wins"] / STATE["tr"] * 100, 1) if STATE["tr"] > 0 else 0
    uptime = int(time.time() - STATE["start"])
    h, m = divmod(uptime // 60, 60)
    
    msg = f"""📊 <b>MASTER SCALPER REPORT</b>
⏱ Uptime: {h}j {m}m
💰 Total PnL: Rp {STATE["pnl"]:+,.0f}
📈 Daily PnL: Rp {STATE["daily_pnl"]:+,.0f}
🎯 Trades: {STATE["tr"]} (Daily: {STATE["daily_trades"]})
✅ Wins: {STATE["wins"]} | ❌ Loss: {STATE["losses"]}
📊 Win Rate: {wr}%
🔄 Active Pos: {len(STATE["pos"])}
🟢 Status: {"AKTIF" if STATE["active"] else "PAUSE"}"""
    tg(msg)

# ==================== MAIN LOOP ====================
print("MASTER SCALPER GREED v6 STARTING...")
tg("""🚀 <b>MASTER SCALPER GREED v6 AKTIF!</b>
━━━━━━━━━━━━━━━━━━━━
⚡ AGGRESSIVE SCALPING MODE
💰 BTC | ETH | TRX | BNB
📊 Micro Analysis (5-15min)
🎯 TP: 0.8% | SL: 0.3%
🔥 MAX 4 POSISI
━━━━━━━━━━━━━━━━━━━━
Pair: {', '.join(PAIRS).upper()}
Modal: Rp {MODAL:,}
/help untuk commands""")

scalp_cycle = 0
while True:
    try:
        for upd in get_updates():
            offset = upd["update_id"] + 1
            msg = upd.get("message", {})
            txt = msg.get("text", "").strip()
            photo = msg.get("photo")
            
            # ==================== HANDLE GAMBAR ====================
            if photo:
                tg("📸 Menganalisis gambar...")
                file_id = photo[-1]["file_id"]
                image = download_image_from_telegram(file_id)
                
                if image:
                    text_result = read_text_from_image(image)
                    sr_result = detect_support_resistance(image)
                    chart_analysis = analyze_chart_image(image)
                    
                    sr_text = "\n".join([f"  • {item.get('type', 'Unknown')}: Level {item.get('level', '?')}" 
                                        for item in sr_result[:5]])
                    
                    result_msg = f"""📊 <b>CHART ANALYSIS</b>

📝 <b>TEXT:</b>
{text_result[:200]}

📈 <b>SUPPORT/RESISTANCE:</b>
{sr_text if sr_text else "Tidak terdeteksi"}

💡 <b>INFO:</b>
Ukuran: {chart_analysis.get('width', '?')}x{chart_analysis.get('height', '?')}

🤖 Tanya AI untuk analisis lebih dalam..."""
                    
                    tg(result_msg)
                else:
                    tg("❌ Gagal download gambar")
                continue
            
            # ==================== HANDLE COMMAND ====================
            if not txt:
                continue
            
            cmd = txt.lower()
            
            if cmd in ["/help", "/start"]:
                tg("""🤖 <b>MASTER SCALPER GREED v6</b>
                
⚡ <b>AGGRESSIVE SCALPING COMMANDS:</b>
/status - Status trading real-time
/scalp - Quick scalp analysis ALL
/balance - Saldo Indodax
/start_bot - MULAI auto-scalping
/stop_bot - PAUSE trading
/report - Laporan profit harian
/positions - Lihat semua posisi open

📊 <b>PAIR TRADING:</b>
BTC_IDR | ETH_IDR | TRX_IDR | BNB_IDR

💰 <b>PARAMETER:</b>
TP: 0.8% | SL: 0.3% | Trailing: 0.5%
Max Pos: 4 | Check: 5 detik

📸 <b>FITUR GAMBAR:</b>
✓ OCR - Baca text
✓ Support/Resistance detect
✓ Chart Analysis

🎯 Atau tanya AI apapun!""")
            
            elif cmd == "/status":
                active_pos = len(STATE["pos"])
                wr = round(STATE["wins"] / STATE["tr"] * 100, 1) if STATE["tr"] > 0 else 0
                tg(f"""⚡ <b>SCALPER STATUS</b>
PnL: Rp {STATE["pnl"]:+,.0f}
Daily PnL: Rp {STATE["daily_pnl"]:+,.0f}
Trades: {STATE["tr"]} (WR: {wr}%)
Open Pos: {active_pos}/{MAX_POSITIONS}
Status: {"🟢 AKTIF" if STATE["active"] else "🔴 PAUSE"}""")
            
            elif cmd == "/scalp":
                tg("⚡ Quick scalp analysis...")
                for pair in PAIRS:
                    a = quick_scalp_analysis(pair)
                    if a:
                        tg(f"""⚡ <b>{pair.upper()}</b>
💰 Harga: Rp {a["price"]:,.0f}
📊 RSI: {a["rsi"]} | Momentum: {a["momentum"]}%
🎯 CCI: {a["cci"]}
📈 EMA5: {a["ema5"]:,.0f} | EMA10: {a["ema10"]:,.0f}
⚡ Signal: {a["signal"]} ({a["confidence"]}%)
Score: {a["scalp_score"]}""")
            
            elif cmd == "/balance":
                idr = float(priv("getInfo").get("balance", {}).get("idr", 0))
                tg(f"💰 Saldo IDR: Rp {idr:,.0f}")
            
            elif cmd == "/positions":
                if not STATE["pos"]:
                    tg("Tidak ada posisi terbuka")
                else:
                    for pair, data in STATE["pos"].items():
                        entry = data["e"]
                        t = tick(pair)
                        current = float(t["last"]) if t else entry
                        pnl = (current - entry) * data["c"]
                        pnl_pct = ((current - entry) / entry) * 100
                        tg(f"""📊 <b>{pair.upper()}</b>
Entry: Rp {entry:,.0f}
Current: Rp {current:,.0f}
PnL: Rp {pnl:+,.0f} ({pnl_pct:+.2f}%)
Type: {data.get('type', 'LONG')}""")
            
            elif cmd == "/start_bot":
                STATE["active"] = True
                tg("✅ SCALPER AKTIF! Mode GREED ON 🔥")
            
            elif cmd == "/stop_bot":
                STATE["active"] = False
                tg("⏸ Bot PAUSE")
            
            elif cmd == "/report":
                send_report()
            
            else:
                tg("🧠 AI analyzing...")
                ctx = market_ctx()
                ans = groq(txt, ctx)
                tg(f"🧠 <b>AI SCALPER:</b>\n\n{ans}")

        # ==================== AUTO SCALPING ====================
        if STATE["active"]:
            scalp_cycle += 1
            
            # Check daily reset
            if datetime.now().date() > STATE["day_start"]:
                STATE["daily_pnl"] = 0
                STATE["daily_trades"] = 0
                STATE["day_start"] = datetime.now().date()
            
            # MANAGE POSISI YANG TERBUKA
            for pair in list(STATE["pos"].keys()):
                t = tick(pair)
                if not t:
                    continue
                
                now = float(t["last"])
                data = STATE["pos"][pair]
                ep = data["e"]  # entry price
                coin = data["c"]
                peak = data.get("peak", ep)
                
                if now > peak:
                    data["peak"] = now
                    peak = now
                
                trail_sl = peak * (1 - TRAILING)
                pnl = (now - ep) * coin
                pnl_pct = ((now - ep) / ep) * 100
                
                # AGGRESSIVE EXIT - QUICK PROFIT
                if QUICK_EXIT and pnl >= MIN_PROFIT_IDR:
                    priv("trade", {"pair": pair, "type": "sell", "price": str(int(now)), "order_return_funds": str(coin)})
                    STATE["pnl"] += pnl
                    STATE["daily_pnl"] += pnl
                    STATE["tr"] += 1
                    STATE["daily_trades"] += 1
                    STATE["wins"] += 1
                    del STATE["pos"][pair]
                    tg(f"✅ QUICK PROFIT {pair.upper()}\nRp {pnl:+,.0f} ({pnl_pct:+.3f}%)\nTotal: Rp {STATE['pnl']:+,.0f}")
                
                # TAKE PROFIT
                elif now >= ep * (1 + TP):
                    priv("trade", {"pair": pair, "type": "sell", "price": str(int(now)), "order_return_funds": str(coin)})
                    STATE["pnl"] += pnl
                    STATE["daily_pnl"] += pnl
                    STATE["tr"] += 1
                    STATE["daily_trades"] += 1
                    STATE["wins"] += 1
                    del STATE["pos"][pair]
                    tg(f"✅ TP HIT {pair.upper()} +Rp {pnl:,.0f}")
                
                # STOP LOSS
                elif now <= ep * (1 - SL):
                    priv("trade", {"pair": pair, "type": "sell", "price": str(int(now)), "order_return_funds": str(coin)})
                    STATE["pnl"] += pnl
                    STATE["daily_pnl"] += pnl
                    STATE["tr"] += 1
                    STATE["daily_trades"] += 1
                    STATE["losses"] += 1
                    del STATE["pos"][pair]
                    tg(f"🛑 SL HIT {pair.upper()} Rp {pnl:,.0f}")
                
                # TRAILING STOP (Secure profit)
                elif now <= trail_sl and pnl > 0:
                    priv("trade", {"pair": pair, "type": "sell", "price": str(int(now)), "order_return_funds": str(coin)})
                    STATE["pnl"] += pnl
                    STATE["daily_pnl"] += pnl
                    STATE["tr"] += 1
                    STATE["daily_trades"] += 1
                    STATE["wins"] += 1
                    del STATE["pos"][pair]
                    tg(f"📉 TRAILING STOP {pair.upper()} +Rp {pnl:,.0f}")
            
            # NEW ENTRY - AGGRESSIVE SCALPING
            if len(STATE["pos"]) < MAX_POSITIONS and STATE["daily_pnl"] > -MAX_LOSS_DAILY:
                idr = float(priv("getInfo").get("balance", {}).get("idr", 0))
                
                if idr >= MODAL * 1.5:
                    best = None
                    bc = 0
                    best_data = None
                    
                    for pair in PAIRS:
                        if pair in STATE["pos"]:
                            continue
                        
                        a = quick_scalp_analysis(pair)
                        if not a:
                            continue
                        
                        t = tick(pair)
                        vol = float(t.get("vol_idr", 0)) if t else 0
                        
                        # Filter by volume & signal strength
                        if vol >= MIN_VOLUME and a["confidence"] >= bc:
                            if a["signal"] in ["AGGRESSIVE_BUY", "BUY"]:
                                bc = a["confidence"]
                                best = pair
                                best_data = a
                    
                    if best and bc >= 40:
                        alloc = min(MODAL, idr * 0.85)
                        r = priv("trade", {"pair": best, "type": "buy", "price": 0, "idr": str(int(alloc))})
                        
                        if r:
                            t = tick(best)
                            price = float(t["last"]) if t else 0
                            coin = (alloc / price) * 0.997
                            
                            STATE["pos"][best] = {
                                "e": price,
                                "c": coin,
                                "peak": price,
                                "entry_time": time.time(),
                                "type": best_data["signal"]
                            }
                            
                            tg(f"""🔥 <b>SCALP ENTRY {best.upper()}</b>
Price: Rp {price:,.0f}
Modal: Rp {alloc:,.0f}
Signal: {best_data["signal"]}
Confidence: {bc}%
TP: Rp {price*(1+TP):,.0f}
SL: Rp {price*(1-SL):,.0f}
CCI: {best_data["cci"]} | RSI: {best_data["rsi"]}""")
        
        # PERIODIC REPORT
        if time.time() - STATE["last_report"] >= 1800:  # Every 30 min
            send_report()
            STATE["last_report"] = time.time()

    except KeyboardInterrupt:
        tg("⛔ Scalper stopped")
        break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(2)
    
    time.sleep(SCALP_CHECK_INTERVAL)
