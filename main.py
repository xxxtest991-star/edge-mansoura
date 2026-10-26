import os, time, threading, requests
from flask import Flask
import yfinance as yf

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = "8603649187"
CHECK_INTERVAL = 300

app = Flask(__name__)
@app.route('/')
def home(): return "Edge Mansoura V3 - bebo - LIVE"

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def get_data():
    try:
        df_4h = yf.Ticker("GC=F").history(period="20d", interval="60m")
        df_5m = yf.Ticker("GC=F").history(period="5d", interval="5m")
        high_50 = df_4h['High'].tail(50).max()
        low_50 = df_4h['Low'].tail(50).min()
        current = df_5m['Close'].iloc[-1]
        return current, df_5m, high_50, low_50
    except: return None,None,None,None

def rsi(series, p=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(p).mean()
    loss = -delta.where(delta < 0, 0).rolling(p).mean()
    rs = gain/loss
    return 100 - (100/(1+rs))

def check():
    price, df5, high50, low50 = get_data()
    if price is None: return
    sell_bottom = high50 * 0.985
    sell_top = high50 * 1.002
    buy_bottom = low50 * 0.998
    buy_top = low50 * 1.015
    rsi_val = rsi(df5['Close']).iloc[-1]
    if sell_bottom <= price <= sell_top and rsi_val > 62:
        last = df5.iloc[-1]
        wick = last['High'] - max(last['Open'], last['Close'])
        body = abs(last['Close']-last['Open']) + 0.01
        if wick > body * 0.5:
            send_telegram(f"🔴 بيع V3 {price:.2f} قمة {high50:.0f} RSI {rsi_val:.1f}")
    if buy_bottom <= price <= buy_top and rsi_val < 38:
        last = df5.iloc[-1]
        wick = min(last['Open'], last['Close']) - last['Low']
        body = abs(last['Close']-last['Open']) + 0.01
        if wick > body * 0.5:
            send_telegram(f"🟢 شراء V3 {price:.2f} قاع {low50:.0f} RSI {rsi_val:.1f}")

def loop():
    send_telegram("🚀 V3 اشتغل يا بيبو ID: 8603649187")
    while True:
        try: check()
        except: pass
        time.sleep(CHECK_INTERVAL)

threading.Thread(target=loop, daemon=True).start()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
