import pandas as pd
import numpy as np
from statsmodels.formula.api import ols

df = pd.read_csv('data/master_data.csv')
df['date'] = pd.to_datetime(df['date'])

# Adstock変換
def adstock(x, decay=0.4):
    x = np.array(x, dtype=float)
    result = np.zeros(len(x))
    result[0] = x[0]
    for i in range(1, len(x)):
        result[i] = x[i] + decay * result[i-1]
    return result

df['cost_adstock'] = adstock(df['費用'])
df['weekday'] = df['date'].dt.dayofweek
df['month'] = df['date'].dt.month

# 列名を整理
df = df.rename(columns={
    'リースバック': 'trend_leaseback',
    'リバースモーゲージ': 'trend_reverse_mortgage',
    'リバース60': 'trend_reverse60',
    '任意売却': 'trend_sale',
    '住宅ローン 払えない': 'trend_loan',
    '不動産担保ローン': 'trend_collateral'
})

trend_cols = ['trend_leaseback', 'trend_reverse_mortgage', 'trend_reverse60',
              'trend_sale', 'trend_loan', 'trend_collateral']
df[trend_cols] = df[trend_cols].fillna(0)

# モデル構築（目的変数：コンバージョン数）
model = ols('''
    コンバージョン ~
    cost_adstock +
    trend_leaseback +
    trend_reverse_mortgage +
    trend_reverse60 +
    trend_sale +
    trend_loan +
    trend_collateral +
    C(weekday) +
    C(month)
''', data=df).fit()

print(model.summary())

# 係数を保存
coef = pd.DataFrame({
    'variable': model.params.index,
    'coefficient': model.params.values,
    'pvalue': model.pvalues.values
})
coef.to_csv('data/model_coef.csv', index=False)
print("\n係数を保存しました")
print(f"R²（モデル精度）: {model.rsquared:.3f}")