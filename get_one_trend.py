from pytrends.request import TrendReq
import pandas as pd
import time

print("30秒待機してからリクエストします...")
time.sleep(30)

pytrends = TrendReq(hl='ja-JP', tz=540)

try:
    pytrends.build_payload(["競売 不動産"], timeframe='today 5-y', geo='JP')
    df = pytrends.interest_over_time()
    if not df.empty:
        # 既存のtrendsに追加
        trends = pd.read_csv('data/raw/trends.csv', index_col=0)
        trends['競売 不動産'] = df['競売 不動産']
        trends.to_csv('data/raw/trends.csv')
        print("取得・保存完了")
        print(df.tail())
    else:
        print("データなし（検索ボリューム不足）")
except Exception as e:
    print(f"エラー：{e}")