import yfinance as yf
import pandas_ta as ta
import requests
import os

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK") # GitHubの設定から読み込む
SYMBOL = "BTC-USD"

def send_discord(message):
    if WEBHOOK_URL:
        requests.post(WEBHOOK_URL, json={"content": message})

# データ取得と判定
df = yf.download(SYMBOL, period="1mo", interval="1h")
df['SMA_S'] = ta.sma(df['Close'], length=12)
df['SMA_L'] = ta.sma(df['Close'], length=24)

last_1 = df.iloc[-1]
last_2 = df.iloc[-2]
current_price = round(float(last_1['Close']), 2)

if last_2['SMA_S'] <= last_2['SMA_L'] and last_1['SMA_S'] > last_1['SMA_L']:
    send_discord(f"🚀 **【買い】** {SYMBOL} 発生！ 価格: {current_price}")
elif last_2['SMA_S'] >= last_2['SMA_L'] and last_1['SMA_S'] < last_1['SMA_L']:
    send_discord(f"⚠️ **【売り】** {SYMBOL} 発生！ 価格: {current_price}")
# 変化がない時は、動いている確認のために通知しない設定（お好みで）