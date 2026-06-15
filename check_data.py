import pandas as pd

df = pd.read_csv('data/processed/master_data.csv')
df = df[df['date'] >= '2024-01-01']

print('CV分布：')
print(df['コンバージョン'].value_counts().head(10).sort_index())

print('\n費用の統計：')
print(df[df['費用']>0]['費用'].describe().round(0))

print('\nTrends確認（リースバック最初の14行）：')
print(df['リースバック'].head(14).tolist())