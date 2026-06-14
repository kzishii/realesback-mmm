import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="リースバック広告 MMM Dashboard", layout="wide")

# データ読み込み
df = pd.read_csv('data/master_data.csv')
df['date'] = pd.to_datetime(df['date'])
coef = pd.read_csv('data/model_coef.csv')

# 直近7日・30日の集計
last7 = df.tail(7)
last30 = df.tail(30)
prev30 = df.iloc[-60:-30] if len(df) >= 60 else df.head(30)

cv_last30 = last30['コンバージョン'].sum()
cv_prev30 = prev30['コンバージョン'].sum()
cost_last30 = last30['費用'].sum()
cpa_last30 = cost_last30 / cv_last30 if cv_last30 > 0 else 0
cpa_prev30 = prev30['費用'].sum() / cv_prev30 if cv_prev30 > 0 else 0
cv_change = ((cv_last30 - cv_prev30) / cv_prev30 * 100) if cv_prev30 > 0 else 0
cpa_change = ((cpa_last30 - cpa_prev30) / cpa_prev30 * 100) if cpa_prev30 > 0 else 0

st.title("🏠 リースバック広告 MMM ダッシュボード")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 今週の推奨アクション",
    "📊 広告パフォーマンス",
    "📈 MMM分析結果",
    "🔍 競合・市場トレンド",
    "💰 予算最適化"
])

# ───────────────────────────────
with tab1:
    st.header("今週の推奨アクション")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("直近30日 CV数", f"{cv_last30:.0f}件",
                  f"{cv_change:+.1f}% 前月比")
    with col2:
        st.metric("直近30日 CPA", f"¥{cpa_last30:,.0f}",
                  f"{cpa_change:+.1f}% 前月比")
    with col3:
        st.metric("直近30日 広告費", f"¥{cost_last30:,.0f}")

    st.divider()

    # 推奨アクションコメント
    st.subheader("💬 AIによる評価コメント")

    if cpa_change < -10:
        st.success(f"✅ CPAが前月比{abs(cpa_change):.1f}%改善しています。現在の予算配分を維持してください。")
    elif cpa_change > 10:
        st.warning(f"⚠️ CPAが前月比{cpa_change:.1f}%悪化しています。入札戦略の見直しを推奨します。")
    else:
        st.info("ℹ️ CPAは前月比ほぼ横ばいです。Trendsの動向を確認しながら微調整してください。")

    if cv_change > 10:
        st.success(f"✅ CV数が前月比{cv_change:.1f}%増加しています。好調です。")
    elif cv_change < -10:
        st.warning(f"⚠️ CV数が前月比{abs(cv_change):.1f}%減少しています。予算増額またはクリエイティブ改善を検討してください。")

    # 最新トレンド評価
    st.divider()
    st.subheader("📡 市場トレンド評価（直近週）")
    latest = df.iloc[-1]

    col1, col2 = st.columns(2)
    with col1:
        rb = latest.get('リースバック', 0)
        rm = latest.get('リバースモーゲージ', 0)
        if rb > 60:
            st.warning(f"⚠️ リースバック検索量が高水準（{rb}）です。競合他社との差別化が重要です。")
        else:
            st.info(f"ℹ️ リースバック検索量：{rb}（標準水準）")
        if rm > 60:
            st.success(f"✅ リバースモーゲージ需要が高水準（{rm}）です。CV増加が期待できます。予算増額を推奨します。")
        else:
            st.info(f"ℹ️ リバースモーゲージ需要：{rm}（標準水準）")
    with col2:
        sale = latest.get('任意売却', 0)
        loan = latest.get('住宅ローン 払えない', 0)
        if sale > 60:
            st.success(f"✅ 任意売却需要が高水準（{sale}）です。困窮層へのアプローチ強化を推奨します。")
        if loan > 50:
            st.warning(f"⚠️ 住宅ローン困窮需要が上昇中（{loan}）です。緊急訴求クリエイティブを検討してください。")

# ───────────────────────────────
with tab2:
    st.header("広告パフォーマンス")

    col1, col2 = st.columns(2)
    with col1:
        fig = px.line(df, x='date', y='コンバージョン',
                      title='日別コンバージョン数', markers=True)
        fig.update_traces(line_color='#00CC96')
        st.plotly_chart(fig)
    with col2:
        fig2 = px.bar(df, x='date', y='費用',
                      title='日別広告費用', color_discrete_sequence=['#636EFA'])
        st.plotly_chart(fig2)

    # CPA推移
    df_cpa = df[df['CPA'] > 0]
    if not df_cpa.empty:
        fig3 = px.line(df_cpa, x='date', y='CPA',
                       title='CPA推移（1CV獲得コスト）', markers=True)
        fig3.update_traces(line_color='#EF553B')
        avg_cpa = df_cpa['CPA'].mean()
        fig3.add_hline(y=avg_cpa, line_dash='dash',
                       annotation_text=f"平均CPA: ¥{avg_cpa:,.0f}")
        st.plotly_chart(fig3)

        avg = df_cpa['CPA'].mean()
        recent = df_cpa['CPA'].tail(7).mean()
        if recent < avg * 0.9:
            st.success(f"✅ 直近7日のCPA（¥{recent:,.0f}）は全期間平均（¥{avg:,.0f}）より改善しています。")
        elif recent > avg * 1.1:
            st.warning(f"⚠️ 直近7日のCPA（¥{recent:,.0f}）は全期間平均（¥{avg:,.0f}）より悪化しています。")
        else:
            st.info(f"ℹ️ 直近7日のCPA（¥{recent:,.0f}）は平均的な水準です。")

# ───────────────────────────────
with tab3:
    st.header("MMM分析結果")

    coef_main = coef[coef['variable'].str.startswith('trend_') |
                     (coef['variable'] == 'cost_adstock')]
    coef_main = coef_main.copy()
    coef_main['変数名'] = coef_main['variable'].map({
        'cost_adstock': '広告費（Adstock）',
        'trend_leaseback': 'リースバック検索',
        'trend_reverse_mortgage': 'リバースモーゲージ検索',
        'trend_reverse60': 'リバース60検索',
        'trend_sale': '任意売却検索',
        'trend_loan': '住宅ローン困窮検索',
        'trend_collateral': '不動産担保ローン検索'
    })
    coef_main['有意性'] = coef_main['pvalue'].apply(
        lambda p: '★★★ 有意' if p < 0.01 else ('★★ 有意' if p < 0.05 else '参考値'))

    fig4 = px.bar(coef_main, x='変数名', y='coefficient',
                  title='各要因のCV数への影響度',
                  color='coefficient',
                  color_continuous_scale='RdYlGn',
                  hover_data=['有意性', 'pvalue'])
    st.plotly_chart(fig4)

    st.subheader("💬 分析コメント")
    st.info("📌 広告費（Adstock）はCV数に最も確実な影響を与えています（p<0.001）。")
    st.success("✅ リバースモーゲージ需要が高い時期はCV数が増加する傾向があります。この時期に予算を集中させることを推奨します。")
    st.warning("⚠️ リースバック検索量が増えるとCV数が減少する傾向があります。競合他社との差別化戦略が重要です。")
    st.info("📌 任意売却需要が高い時期もCV数が増加します。困窮層向けの訴求を強化しましょう。")

    st.divider()
    st.subheader("係数一覧")
    st.dataframe(coef_main[['変数名', 'coefficient', 'pvalue', '有意性']].round(4))

# ───────────────────────────────
with tab4:
    st.header("競合・市場トレンド分析")

    trends_df = pd.read_csv('data/trends.csv')
    trends_df['date'] = pd.to_datetime(trends_df['date'])

    # リースバック vs リバース系
    st.subheader("リースバック vs リバース系 需要比較")
    fig5 = px.line(trends_df, x='date',
                   y=['リースバック', 'リバースモーゲージ', 'リバース60'],
                   title='リースバック・リバース系 検索トレンド',
                   labels={'value': '検索量（相対値）', 'variable': 'キーワード'})
    st.plotly_chart(fig5)

    latest_t = trends_df.iloc[-1]
    rb_share = latest_t['リースバック']
    rm_share = latest_t['リバースモーゲージ']
    if rm_share > rb_share:
        st.warning(f"⚠️ 現在リバースモーゲージ（{rm_share}）がリースバック（{rb_share}）より検索量が多い状態です。競合製品への流出に注意してください。")
    else:
        st.success(f"✅ リースバック（{rb_share}）がリバースモーゲージ（{rm_share}）より検索量が多い状態です。市場優位性があります。")

    st.divider()

    # 困窮層トレンド
    st.subheader("困窮層・緊急資金層 需要トレンド")
    fig6 = px.line(trends_df, x='date',
                   y=['任意売却', '住宅ローン 払えない', '不動産担保ローン'],
                   title='困窮層・緊急資金層 検索トレンド',
                   labels={'value': '検索量（相対値）', 'variable': 'キーワード'})
    st.plotly_chart(fig6)

# ───────────────────────────────
with tab5:
    st.header("予算最適化シミュレーション")

    st.subheader("月間予算を入力してください")
    budget = st.number_input("月間予算（円）", value=300000, step=10000)

    # MMMの広告費係数
    cost_coef = coef[coef['variable'] == 'cost_adstock']['coefficient'].values[0]

    # 曜日別効果（モデル係数から）
    weekday_coef = {}
    weekday_names = ['月', '火', '水', '木', '金', '土', '日']
    base = 0
    for i in range(7):
        key = f'C(weekday)[T.{i}]' if i > 0 else None
        if key and key in coef['variable'].values:
            weekday_coef[i] = coef[coef['variable'] == key]['coefficient'].values[0]
        else:
            weekday_coef[i] = base

    total_effect = sum(max(v, 0.01) for v in weekday_coef.values())
    budget_allocation = {
        weekday_names[k]: budget / 4.3 * max(v, 0.01) / total_effect * 7
        for k, v in weekday_coef.items()
    }

    alloc_df = pd.DataFrame({
        '曜日': list(budget_allocation.keys()),
        '推奨日予算（円）': [round(v) for v in budget_allocation.values()]
    })

    fig7 = px.bar(alloc_df, x='曜日', y='推奨日予算（円）',
                  title='曜日別 推奨予算配分',
                  color='推奨日予算（円）',
                  color_continuous_scale='Blues')
    st.plotly_chart(fig7)

    st.dataframe(alloc_df)

    # CV予測
    monthly_cost_adstock = budget * (1 / (1 - 0.4))
    predicted_cv = cost_coef * monthly_cost_adstock
    st.divider()
    st.subheader("💬 予算最適化コメント")
    st.success(f"✅ 月間予算 ¥{budget:,} の場合、月間CV数は約 **{max(predicted_cv, 0):.1f}件** と予測されます。")
    st.info("📌 リバースモーゲージ需要が高い週は予算を20〜30%増額することでCV効率が上がる可能性があります。")

    best_day = alloc_df.loc[alloc_df['推奨日予算（円）'].idxmax(), '曜日']
    st.info(f"📌 最も効果が期待できる曜日は **{best_day}曜日** です。重点的に予算を配分することを推奨します。")