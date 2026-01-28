import yfinance as yf
import requests
import os
import pandas as pd
import json

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
HISTORY_FILE = "trade_history.json"
INITIAL_CASH = 1000 
JPY_USD = 150 

def send_discord(message):
    if not WEBHOOK_URL: return
    if len(message) > 2000:
        for i in range(0, len(message), 2000):
            requests.post(WEBHOOK_URL, json={"content": message[i:i+2000]})
    else:
        requests.post(WEBHOOK_URL, json={"content": message})

def get_nasdaq100_list():
    try:
        # Wikipediaのブロック対策: User-Agentを追加
        url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        tables = pd.read_html(response.text)
        # テーブルのインデックスを自動判定
        for df in tables:
            if 'Ticker' in df.columns:
                return df['Ticker'].tolist()
        return ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "TSLA"] # 予備
    except Exception as e:
        print(f"List fetch error: {e}")
        return ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "TSLA"]

def load_data():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                content = f.read().strip()
                return json.loads(content) if content else {}
        except:
            return {}
    return {}

def save_data(data):
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=4)

# 実行
symbols = get_nasdaq100_list()
data_store = load_data()
actions_taken = []
total_all_assets = 0

print(f"Scanning {len(symbols)} symbols...")

for symbol in symbols:
    try:
        s_fix = str(symbol).replace('.', '-')
        df = yf.download(s_fix, period="5d", interval="1h", progress=False)
        if len(df) < 20: continue
        
        df['SMA_S'] = df['Close'].rolling(window=12).mean()
        df['SMA_L'] = df['Close'].rolling(window=24).mean()
        
        curr_p = float(df['Close'].iloc[-1])
        curr_jpy = curr_p * JPY_USD
        
        s1, l1 = float(df['SMA_S'].iloc[-1]), float(df['SMA_L'].iloc[-1])
        s2, l2 = float(df['SMA_S'].iloc[-2]), float(df['SMA_L'].iloc[-2])
        
        if s_fix not in data_store:
            data_store[s_fix] = {"holdings": 0.0, "cash": float(INITIAL_CASH)}
        
        h, c = data_store[s_fix]["holdings"], data_store[s_fix]["cash"]
        
        if s2 <= l2 and s1 > l1 and c > 0:
            h, c = c / curr_jpy, 0
            actions_taken.append(f"🚀買:{s_fix}")
        elif s2 >= l2 and s1 < l1 and h > 0:
            c, h = h * curr_jpy, 0
            actions_taken.append(f"⚠️売:{s_fix}")
        
        data_store[s_fix] = {"holdings": h, "cash": c}
        total_all_assets += round(c + (h * curr_jpy))
    except:
        continue

# 集計と報告
initial_total = len(symbols) * INITIAL_CASH
profit_loss = total_all_assets - initial_total

summary = f"📑 **【Nasdaq100シミュレーション】**\n"
summary += f"💰 総資産: **{total_all_assets:,}円**\n"
summary += f"📈 累計損益: {profit_loss:+,}円\n"

if actions_taken:
    summary += "\n🔔 **売買:** " + ", ".join(actions_taken[:15]) # 通知が長すぎないよう制限
else:
    summary += "\n😴 待機中..."

save_data(data_store)
send_discord(summary)

