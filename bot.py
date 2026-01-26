import yfinance as yf
import requests
import os
import pandas as pd

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
SYMBOL = "BTC-USD"

def send_discord(message):
    if WEBHOOK_URL:
        requests.post(WEBHOOK_URL, json={"content": message})

# データの取得（余裕を持って1ヶ月分）
df = yf.download(SYMBOL, period="1mo", interval="1h")

# 移動平均の計算
df['SMA_S'] = df['Close'].rolling(window=12).mean()
df['SMA_L'] = df['Close'].rolling(window=24).mean()

# 計算できない初期の空データ(NaN)を削除
df = df.dropna()

if len(df) < 2:
    send_discord("データ不足で判定できませんでした。次回の実行をお待ちください。")
else:
    last_1 = df.iloc[-1]
    last_2 = df.iloc[-2]
    
    # 価格の取得（エラー回避のため values[0] を使用）
    current_price = round(float(last_1['Close'].values[0] if isinstance(last_1['Close'], pd.Series) else last_1['Close']), 2)

    status_msg = f"🔎 {SYMBOL} 現在価格: {current_price}\n"

    # シグナル判定（.item()や.values[0]を使わず、安全に比較）
    s1, l1 = float(last_1['SMA_S']), float(last_1['SMA_L'])
    s2, l2 = float(last_2['SMA_S']), float(last_2['SMA_L'])

    if s2 <= l2 and s1 > l1:
        status_msg += "🚀 **【買い】** ゴールデンクロス発生！"
    elif s2 >= l2 and s1 < l1:
        status_msg += "⚠️ **【売り】** デッドクロス発生！"
    else:
        status_msg += "😴 現在シグナルなし。ホールド中。"

    send_discord(status_msg)
