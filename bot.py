import yfinance as yf
import requests
import os

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
SYMBOL = "BTC-USD"

def send_discord(message):
    if WEBHOOK_URL:
        requests.post(WEBHOOK_URL, json={"content": message})

# データの取得
df = yf.download(SYMBOL, period="1mo", interval="1h")

# pandas_taを使わず、標準機能で移動平均を計算 (12時間と24時間)
df['SMA_S'] = df['Close'].rolling(window=12).mean()
df['SMA_L'] = df['Close'].rolling(window=24).mean()

last_1 = df.iloc[-1]
last_2 = df.iloc[-2]
current_price = round(float(last_1['Close']), 2)

status_msg = f"🔎 {SYMBOL} 現在価格: {current_price}\n"

# 判定ロジック
if last_2['SMA_S'] <= last_2['SMA_L'] and last_1['SMA_S'] > last_1['SMA_L']:
    status_msg += "🚀 **【買い】** ゴールデンクロス発生！"
elif last_2['SMA_S'] >= last_2['SMA_L'] and last_1['SMA_S'] < last_1['SMA_L']:
    status_msg += "⚠️ **【売り】** デッドクロス発生！"
else:
    status_msg += "😴 現在シグナルなし。ホールド中。"

send_discord(status_msg)
