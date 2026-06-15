import pandas as pd

df = pd.read_csv('data/raw/google_ads_hourly.csv',
                 encoding='utf-8-sig', skiprows=2)
df.columns = df.columns.str.strip()
print("列名：")
print(df.columns.tolist())
print("\n先頭5行：")
print(df.head())
print("\n時間帯の値サンプル：")
print(df['時間帯'].unique()[:5] if '時間帯' in df.columns else "時間帯列なし")
print("\n曜日の値サンプル：")
print(df['曜日'].unique() if '曜日' in df.columns else "曜日列なし")