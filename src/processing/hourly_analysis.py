import pandas as pd
import numpy as np

print("=== 時間帯×曜日 分析開始 ===")

df = pd.read_csv('data/raw/google_ads_hourly.csv',
                 encoding='utf-8-sig', skiprows=2)
df.columns = df.columns.str.strip()

# 数値クリーニング
for col in ['クリック数', '表示回数', '費用', 'コンバージョン']:
    df[col] = pd.to_numeric(
        df[col].astype(str).str.replace(',', '').str.replace('%', ''),
        errors='coerce'
    ).fillna(0)

# 曜日の順序を設定
weekday_order = ['月曜日', '火曜日', '水曜日', '木曜日', '金曜日', '土曜日', '日曜日']

# 時間帯×曜日で集計
pivot_data = df.groupby(['時間帯', '曜日']).agg({
    'クリック数': 'sum',
    '費用': 'sum',
    'コンバージョン': 'sum',
    '表示回数': 'sum'
}).reset_index()

# CV率・CPA計算
pivot_data['CV率'] = pivot_data.apply(
    lambda r: r['コンバージョン'] / r['クリック数'] if r['クリック数'] > 0 else 0,
    axis=1
)
pivot_data['CPA'] = pivot_data.apply(
    lambda r: r['費用'] / r['コンバージョン'] if r['コンバージョン'] > 0 else 0,
    axis=1
)

# ヒートマップ用ピボット作成
heatmap_cv = pivot_data.pivot_table(
    index='時間帯', columns='曜日', values='コンバージョン', aggfunc='sum'
)[weekday_order]

heatmap_cvrate = pivot_data.pivot_table(
    index='時間帯', columns='曜日', values='CV率', aggfunc='mean'
)[weekday_order]

heatmap_cost = pivot_data.pivot_table(
    index='時間帯', columns='曜日', values='費用', aggfunc='sum'
)[weekday_order]

# 保存
heatmap_cv.to_csv('data/processed/heatmap_cv.csv')
heatmap_cvrate.to_csv('data/processed/heatmap_cvrate.csv')
heatmap_cost.to_csv('data/processed/heatmap_cost.csv')
pivot_data.to_csv('data/processed/hourly_detail.csv', index=False)

print("CV数ヒートマップ（上位時間帯）：")
print(heatmap_cv.sum(axis=1).sort_values(ascending=False).head(10))
print("\n曜日別CV合計：")
print(heatmap_cv.sum(axis=0).sort_values(ascending=False))
print("\n保存完了")