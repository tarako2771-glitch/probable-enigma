import yfinance as yf
import requests
import os
import pandas as pd

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
SYMBOL = "BTC-USD"
HISTORY_FILE = "trade_history.txt"

def send_discord(message):
    if WEBHOOK_URL:
        requests.post(WEBHOOK_URL, json={"content": message})

def get_last_buy_price():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                content = f.read().strip()
                return float(content) if content else None
        except:
            return None
    return None

def save_buy_price(price):
    with open(HISTORY_FILE, "w") as f:
        f.write(str(price))

df = yf.download(SYMBOL, period="5d", interval="1h")
df['SMA_S'] = df['Close'].rolling(window=12).mean()
df['SMA_L'] = df['Close'].rolling(window=24).mean()
df = df.dropna()

if len(df) < 2:
    send_discord("データ準備中...")
else:
    current_price = round(float(df['Close'].iloc[-1]), 2)
    s1, l1 = float(df['SMA_S'].iloc[-1]), float(df['SMA_L'].iloc[-1])
    s2, l2 = float(df['SMA_S'].iloc[-2]), float(df['SMA_L'].iloc[-2])
    
    last_buy_price = get_last_buy_price()
    profit_msg = ""

    if last_buy_price:
        diff = current_price - last_buy_price
        rate = (diff / last_buy_price) * 100
        emoji = "📈" if diff >= 0 else "📉"
        profit_msg = f"\n{emoji} 現在の含み損益: {round(diff, 2)} USD ({round(rate, 2)}%)"

    status_msg = f"🔎 {SYMBOL} 現在価格: {current_price}"

    if s2 <= l2 and s1 > l1:
        status_msg += "\n🚀 **【買い】** ゴールデンクロス発生！"
        save_buy_price(current_price)
        status_msg += f"\n💰 {current_price} で仮想購入しました。"
    elif s2 >= l2 and s1 < l1:
        status_msg += "\n⚠️ **【売り】** デッドクロス発生！"
        if last_buy_price:
            status_msg += f"\n🏁 今回のトレード結果: {round(current_price - last_buy_price, 2)} USD"
            with open(HISTORY_FILE, "w") as f: f.write("") # 履歴を空にする
    else:
        status_msg += f"\n😴 シグナルなし。ホールド中。{profit_msg}"

    send_discord(status_msg)
