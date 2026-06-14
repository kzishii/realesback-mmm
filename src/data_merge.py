import pandas as pd

# Google広告データ読み込み
ads = pd.read_csv('data/google_ads.csv', encoding='utf-8-sig', skiprows=2)
ads.columns = ads.columns.str.strip()

# 日付列を整理
ads = ads.rename(columns={'日': 'date'})
ads['date'] = pd.to_datetime(ads['date'])

# 数値クリーニング
for col in ['クリック数', '表示回数', '費用', 'コンバージョン', 'コンバージョン単価']:
    ads[col] = pd.to_numeric(
        ads[col].astype(str).str.replace(',', '').str.replace('%', ''),
        errors='coerce'
    ).fillna(0)

# 日別に集計
ads_daily = ads.groupby('date').agg({
    'クリック数': 'sum',
    '表示回数': 'sum',
    '費用': 'sum',
    'コンバージョン': 'sum',
    'コンバージョン単価': 'mean'
}).reset_index()

# CPA計算
ads_daily['CPA'] = ads_daily.apply(
    lambda r: r['費用'] / r['コンバージョン'] if r['コンバージョン'] > 0 else 0,
    axis=1
)

# Trendsデータ読み込み
trends = pd.read_csv('data/trends.csv')
trends['date'] = pd.to_datetime(trends['date'])
trends = trends.set_index('date').resample('D').ffill().reset_index()

# 結合
merged = ads_daily.merge(trends, on='date', how='left')
merged = merged.sort_values('date').reset_index(drop=True)

merged.to_csv('data/master_data.csv', index=False)
print(f"統合完了：{len(merged)}行")
print(merged.head())
print(f"\nコンバージョン合計：{merged['コンバージョン'].sum()}")