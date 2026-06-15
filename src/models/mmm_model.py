import pandas as pd
import numpy as np
from statsmodels.formula.api import ols
import warnings
warnings.filterwarnings('ignore')

print("=== MMM モデル構築開始 ===")

df = pd.read_csv('data/processed/master_data.csv')
df['date'] = pd.to_datetime(df['date'])

print(f"データ期間：{df['date'].min()} 〜 {df['date'].max()}")
print(f"行数：{len(df)}")
print(f"CV合計：{df['コンバージョン'].sum():.0f}件")

# ──────────────────────────────
# Adstock変換
# ──────────────────────────────
def adstock(x, decay=0.4):
    x = np.array(x, dtype=float)
    result = np.zeros(len(x))
    result[0] = x[0]
    for i in range(1, len(x)):
        result[i] = x[i] + decay * result[i-1]
    return result

df['cost_adstock'] = adstock(df['費用'])

# ──────────────────────────────
# Trends列名を整理
# ──────────────────────────────
rename_map = {
    'リースバック': 'trend_leaseback',
    'リバースモーゲージ': 'trend_reverse_mortgage',
    'リバース60': 'trend_reverse60',
    '任意売却': 'trend_sale',
    '住宅ローン 払えない': 'trend_loan',
    '不動産担保ローン': 'trend_collateral',
    '競売 不動産': 'trend_auction'
}
df = df.rename(columns=rename_map)

trend_cols = list(rename_map.values())
for col in trend_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# ──────────────────────────────
# 経済指標
# ──────────────────────────────
if 'interest_rate' in df.columns:
    df['interest_rate'] = pd.to_numeric(df['interest_rate'], errors='coerce').ffill()

if 'nikkei' in df.columns:
    df['nikkei'] = pd.to_numeric(df['nikkei'], errors='coerce').ffill()
    df['nikkei_scaled'] = df['nikkei'] / 10000

# ──────────────────────────────
# 直近2年に絞る（2024年1月〜）
# ──────────────────────────────
df = df[df['date'] >= '2024-01-01'].copy()
print(f"\n直近2年データ：{len(df)}行（{df['date'].min()} 〜 {df['date'].max()}）")

# ──────────────────────────────
# 週次に集計
# ──────────────────────────────
df['week_start'] = df['date'] - pd.to_timedelta(df['date'].dt.dayofweek, unit='d')
df_weekly = df.groupby('week_start').agg({
    'コンバージョン': 'sum',
    '費用': 'sum',
    'クリック数': 'sum',
    '表示回数': 'sum',
    'cost_adstock': 'last',
    'trend_leaseback': 'mean',
    'trend_reverse_mortgage': 'mean',
    'trend_reverse60': 'mean',
    'trend_sale': 'mean',
    'trend_loan': 'mean',
    'trend_collateral': 'mean',
    'trend_auction': 'mean',
    'month': 'first',
    'year': 'first',
    'weekday': 'first'
}).reset_index()
df_weekly.rename(columns={'week_start': 'date'}, inplace=True)
df_weekly['cost_adstock'] = adstock(df_weekly['費用'])
print(f"\n週次データ：{len(df_weekly)}週分")
df_model = df_weekly[df_weekly['費用'] > 0].copy()

# ──────────────────────────────
# Phase1：線形回帰MMM
# ──────────────────────────────
formula_parts = ['cost_adstock']
for col in trend_cols:
    if col in df_model.columns:
        formula_parts.append(col)

formula = 'コンバージョン ~ ' + ' + '.join(formula_parts) + ' + C(weekday) + C(month) + C(year)'

model = ols(formula, data=df_model).fit()

print(f"\n=== モデル結果 ===")
print(f"R²：{model.rsquared:.3f}")
print(f"Adj R²：{model.rsquared_adj:.3f}")
print(f"F統計量のp値：{model.f_pvalue:.4f}")

# 係数を保存
coef = pd.DataFrame({
    'variable': model.params.index,
    'coefficient': model.params.values,
    'pvalue': model.pvalues.values,
    'significant': model.pvalues.values < 0.05
})
coef.to_csv('data/processed/model_coef.csv', index=False)

print(f"\n=== 有意な変数（p<0.05）===")
sig = coef[coef['significant'] & ~coef['variable'].str.contains('Intercept|weekday|month')]
print(sig[['variable', 'coefficient', 'pvalue']].to_string())

print("\n係数を保存しました")