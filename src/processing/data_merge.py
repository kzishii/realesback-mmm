import pandas as pd
import numpy as np

print("=== データ統合開始 ===")

# ──────────────────────────────
# 1. Google広告 日別データ
# ──────────────────────────────
ads = pd.read_csv('data/raw/google_ads_daily.csv', 
                  encoding='utf-8-sig', skiprows=2)
ads.columns = ads.columns.str.strip()
print(f"広告データ列：{ads.columns.tolist()}")

# 日付列を特定
date_col = '日' if '日' in ads.columns else 'Date'
ads = ads.rename(columns={date_col: 'date'})
ads['date'] = pd.to_datetime(ads['date'], errors='coerce')
ads = ads.dropna(subset=['date'])

# 数値クリーニング
numeric_cols = ['クリック数', '表示回数', '費用', 'コンバージョン', 
                'コンバージョン単価', 'すべてのコンバージョン']
for col in numeric_cols:
    if col in ads.columns:
        ads[col] = pd.to_numeric(
            ads[col].astype(str).str.replace(',', '').str.replace('%', ''),
            errors='coerce'
        ).fillna(0)

# 日別集計
agg_dict = {}
for col in numeric_cols:
    if col in ads.columns:
        agg_dict[col] = 'sum'

ads_daily = ads.groupby('date').agg(agg_dict).reset_index()

# CPA再計算
if 'コンバージョン' in ads_daily.columns and '費用' in ads_daily.columns:
    ads_daily['CPA'] = ads_daily.apply(
        lambda r: r['費用'] / r['コンバージョン'] if r['コンバージョン'] > 0 else 0,
        axis=1
    )

print(f"広告データ：{len(ads_daily)}日分 ({ads_daily['date'].min()} 〜 {ads_daily['date'].max()})")

# ──────────────────────────────
# 2. 時間帯別データ（曜日・時間帯効果の参考用）
# ──────────────────────────────
hourly = pd.read_csv('data/raw/google_ads_hourly.csv',
                     encoding='utf-8-sig', skiprows=2)
hourly.columns = hourly.columns.str.strip()

# 時間帯別CV率を集計
if '時間帯' in hourly.columns and 'コンバージョン' in hourly.columns:
    for col in ['クリック数', '費用', 'コンバージョン']:
        if col in hourly.columns:
            hourly[col] = pd.to_numeric(
                hourly[col].astype(str).str.replace(',', ''),
                errors='coerce'
            ).fillna(0)
    
    hourly_summary = hourly.groupby('時間帯').agg({
        'クリック数': 'sum',
        '費用': 'sum',
        'コンバージョン': 'sum'
    }).reset_index()
    hourly_summary['CV率'] = hourly_summary.apply(
        lambda r: r['コンバージョン'] / r['クリック数'] if r['クリック数'] > 0 else 0,
        axis=1
    )
    hourly_summary.to_csv('data/processed/hourly_summary.csv', index=False)
    print(f"時間帯別集計：保存完了")

# ──────────────────────────────
# 3. Google Trendsデータ
# ──────────────────────────────
trends = pd.read_csv('data/raw/trends.csv')
trends['date'] = pd.to_datetime(trends['date'])
trends = trends.set_index('date').resample('D').ffill().reset_index()
print(f"Trendsデータ：{len(trends)}行")

# ──────────────────────────────
# 4. 政策金利データ
# ──────────────────────────────
try:
    rate = pd.read_csv('data/raw/interest_rate.csv', 
                       encoding='shift-jis', skiprows=1)
    rate.columns = ['date', 'interest_rate']
    rate['date'] = pd.to_datetime(rate['date'], errors='coerce')
    rate = rate.dropna(subset=['date'])
    rate['interest_rate'] = pd.to_numeric(rate['interest_rate'], errors='coerce')
    rate = rate.set_index('date').resample('D').ffill().reset_index()
    print(f"金利データ：{len(rate)}行")
    has_rate = True
except Exception as e:
    print(f"金利データ読み込みスキップ：{e}")
    has_rate = False

# ──────────────────────────────
# 5. 日経平均（自動取得）
# ──────────────────────────────
try:
    import yfinance as yf
    nikkei_raw = yf.download('^N225', 
                         start='2021-12-01',
                         end='2026-06-15',
                         interval='1wk',
                         progress=False)
    # MultiIndexを解消
    nikkei_raw.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col 
                          for col in nikkei_raw.columns]
    close_col = [c for c in nikkei_raw.columns if 'Close' in c][0]
    nikkei = nikkei_raw[[close_col]].rename(columns={close_col: 'nikkei'})
    nikkei.index.name = 'date'
    nikkei = nikkei.reset_index()
    nikkei['date'] = pd.to_datetime(nikkei['date']).dt.tz_localize(None)
    nikkei = nikkei.set_index('date').resample('D').ffill().reset_index()
    print(f"日経データ：{len(nikkei)}行")
    has_nikkei = True
except Exception as e:
    print(f"日経データ取得スキップ：{e}")
    has_nikkei = False

# ──────────────────────────────
# 6. データ統合
# ──────────────────────────────
merged = ads_daily.copy()
merged = merged.merge(trends, on='date', how='left')

if has_rate:
    merged = merged.merge(rate, on='date', how='left')

if has_nikkei:
    merged = merged.merge(nikkei, on='date', how='left')

# 曜日・月・年を追加
merged['weekday'] = merged['date'].dt.dayofweek
merged['weekday_name'] = merged['date'].dt.day_name()
merged['month'] = merged['date'].dt.month
merged['year'] = merged['date'].dt.year
merged['week'] = merged['date'].dt.isocalendar().week.astype(int)

merged = merged.sort_values('date').reset_index(drop=True)
merged.to_csv('data/processed/master_data.csv', index=False)
print(f"Trends列：{[c for c in merged.columns if 'Trend' in c or c in ['リースバック','リバースモーゲージ','リバース60','任意売却','住宅ローン 払えない','不動産担保ローン','競売 不動産']]}")

print(f"\n=== 統合完了 ===")
print(f"期間：{merged['date'].min()} 〜 {merged['date'].max()}")
print(f"行数：{len(merged)}行")
print(f"列数：{len(merged.columns)}列")
print(f"CV合計：{merged['コンバージョン'].sum():.0f}件")
print(f"\n先頭5行：")
print(merged.head())