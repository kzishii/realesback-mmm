from pytrends.request import TrendReq
import pandas as pd
import time

pytrends = TrendReq(hl='ja-JP', tz=540)

keywords = [
    "リースバック",
    "リバースモーゲージ",
    "リバース60",
    "任意売却",
    "住宅ローン 払えない",
    "家 売却 現金化",
    "不動産担保ローン"
]

all_data = []
for kw in keywords:
    print(f"取得中：{kw}")
    pytrends.build_payload([kw], timeframe='today 12-m', geo='JP')
    df = pytrends.interest_over_time()
    if not df.empty:
        all_data.append(df[[kw]])
    time.sleep(5)

trends_df = pd.concat(all_data, axis=1)
trends_df.to_csv('data/trends.csv')
print("取得完了")
print(trends_df.tail())