import pandas as pd

df = pd.read_csv('data/processed/master_data.csv')
df['date'] = pd.to_datetime(df['date'])
df = df[df['date'] >= '2024-01-01'].copy()

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

print("trend_auction が存在するか：", 'trend_auction' in df.columns)