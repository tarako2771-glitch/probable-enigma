import yfinance as yf
import requests
import os
import pandas as pd
import json

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
HISTORY_FILE = "trade_history.json"
INITIAL_CASH = 100000  # 1銘柄あたりのシミュレーション予算（10万円）
JPY_USD = 150 # 簡易固定レート

def send_discord(message):
    if not WEBHOOK_URL: return
    # Discordの2000文字制限対策
    if len(message) > 2000:
        for i in range(0, len(message), 2000):
            requests.post(WEBHOOK_URL, json={"content": message[i:i+2000]})
    else:
        requests.post(WEBHOOK_URL, json={"content": message})

def get_nasdaq100_list():
    try:
        # WikipediaのNasdaq100リストからティッカーを取得
        url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
        df_list = pd.read_html(url)[4]
        return df_list['Ticker'].tolist()
    except Exception as e:
        print(f"Error fetching list: {e}")
        return ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "TSLA"]

def load_data():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f)

# 実行開始
symbols = get_nasdaq100_list()
data_store = load_data()
actions_taken = []
total_all_assets = 0

print(f"Starting scan for {len(symbols)} symbols...")

for symbol in symbols:
    try:
        # ティッカーの微修正 (例: BRK.B -> BRK-B)
        s_fix = symbol.replace('.', '-')
        df = yf.download(s_fix, period="5d", interval="1h", progress=False)
        
        # 十分なデータがない場合はスキップ
        if len(df) < 25: continue
        
        # 移動平均線計算
        df['SMA_S'] = df['Close'].rolling(window=12).mean()
        df['SMA_L'] = df['Close'].rolling(window=24).mean()
        
        current_price_usd = float(df['Close'].iloc[-1])
        current_price_jpy = current_price_usd * JPY_USD
        
        s1, l1 = float(df['SMA_S'].iloc[-1]), float(df['SMA_L'].iloc[-1])
        s2, l2 = float(df['SMA_S'].iloc[-2]), float(df['SMA_L'].iloc[-2])
        
        # 銘柄ごとの財布を準備
        if s_fix not in data_store:
            data_store[s_fix] = {"holdings": 0.0, "cash": float(INITIAL_CASH)}
        
        h = data_store[s_fix]["holdings"]
        c = data_store[s_fix]["cash"]
        
        # 売買判定
        if s2 <= l2 and s1 > l1 and c > 0: # ゴールデンクロスで買い
            h = c / current_price_jpy
            c = 0
            actions_taken.append(f"🚀買:{s_fix}")
        elif s2 >= l2 and s1 < l1 and h > 0: # デッドクロスで売り
            c = h * current_price_jpy
            h = 0
            actions_taken.append(f"⚠️売:{s_fix}")
        
        # 記録更新
        data_store[s_fix] = {"holdings": h, "cash": c}
        total_all_assets += round(c + (h * current_price_jpy))
        
    except Exception as e:
        print(f"Error processing {symbol}: {e}")
        continue

# 全体の集計
initial_total = len(symbols) * INITIAL_CASH
profit_loss = total_all_assets - initial_total
profit_rate = (profit_loss / initial_total) * 100

summary = f"📑 **【Nasdaq100自動シミュレーション報告】**\n"
summary += f"💰 総資産: **{total_all_assets:,}円**\n"
summary += f"📈 累計損益: {profit_loss:+,}円 ({profit_rate:+.2f}%)\n"

if actions_taken:
    summary += "\n🔔 **今回の売買:** " + ", ".join(actions_taken)
else:
    summary += "\n😴 本日の売買シグナルはありませんでした。"

save_data(data_store)
send_discord(summary)
print("Process completed.")
