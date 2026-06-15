import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="リースバック広告 MMM Dashboard", layout="wide")

# ──────────────────────────────
# データ読み込み
# ──────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv('data/processed/master_data.csv')
    df['date'] = pd.to_datetime(df['date'])
    coef = pd.read_csv('data/processed/model_coef.csv')
    heatmap_cv = pd.read_csv('data/processed/heatmap_cv.csv', index_col=0)
    heatmap_cvrate = pd.read_csv('data/processed/heatmap_cvrate.csv', index_col=0)
    heatmap_cost = pd.read_csv('data/processed/heatmap_cost.csv', index_col=0)
    trends_df = pd.read_csv('data/raw/trends.csv')
    trends_df['date'] = pd.to_datetime(trends_df['date'])
    return df, coef, heatmap_cv, heatmap_cvrate, heatmap_cost, trends_df

df, coef, heatmap_cv, heatmap_cvrate, heatmap_cost, trends_df = load_data()

# ──────────────────────────────
# KPI計算
# ──────────────────────────────
df_recent = df[df['date'] >= '2024-01-01']
last30 = df_recent.tail(30)
prev30 = df_recent.iloc[-60:-30] if len(df_recent) >= 60 else df_recent.head(30)

cv_last30 = last30['コンバージョン'].sum()
cv_prev30 = prev30['コンバージョン'].sum()
cost_last30 = last30['費用'].sum()
cost_prev30 = prev30['費用'].sum()
cpa_last30 = cost_last30 / cv_last30 if cv_last30 > 0 else 0
cpa_prev30 = cost_prev30 / cv_prev30 if cv_prev30 > 0 else 0
cv_change = (cv_last30 - cv_prev30) / cv_prev30 * 100 if cv_prev30 > 0 else 0
cpa_change = (cpa_last30 - cpa_prev30) / cpa_prev30 * 100 if cpa_prev30 > 0 else 0

# ──────────────────────────────
# タブ構成
# ──────────────────────────────
st.title("🏠 リースバック広告 MMM ダッシュボード")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 推奨アクション",
    "📊 広告パフォーマンス",
    "⏰ 曜日×時間帯分析",
    "📈 MMM分析結果",
    "💰 予算最適化"
])

# ──────────────────────────────
# TAB1：推奨アクション
# ──────────────────────────────
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
    st.subheader("💬 AIによる評価コメント")

    if cpa_change < -10:
        st.success(f"✅ CPAが前月比{abs(cpa_change):.1f}%改善しています。現在の予算配分を維持してください。")
    elif cpa_change > 10:
        st.warning(f"⚠️ CPAが前月比{cpa_change:.1f}%悪化しています。入札戦略の見直しを推奨します。")
    else:
        st.info("ℹ️ CPAは前月比ほぼ横ばいです。Trendsの動向を確認しながら微調整してください。")

    if cv_change < -10:
        st.warning(f"⚠️ CV数が前月比{abs(cv_change):.1f}%減少しています。競合の動向を確認してください。")
    elif cv_change > 10:
        st.success(f"✅ CV数が前月比{cv_change:.1f}%増加しています。好調です。")

    st.divider()
    st.subheader("⏰ 推奨入札強化タイミング")
    col1, col2 = st.columns(2)
    with col1:
        st.info("📌 **最もCVが多い時間帯：10〜17時**\n\nこの時間帯の入札単価を10〜20%引き上げることを推奨します。")
    with col2:
        st.info("📌 **最もCVが多い曜日：火曜・木曜**\n\n週末（土・日）は入札単価を10〜15%引き下げてコストを最適化してください。")

    st.divider()
    st.subheader("📡 市場トレンド評価（直近週）")
    latest = trends_df.iloc[-1]
    col1, col2 = st.columns(2)
    with col1:
        rb = latest.get('リースバック', 0)
        rm = latest.get('リバースモーゲージ', 0)
        if rb > 60:
            st.warning(f"⚠️ リースバック検索量が高水準（{rb}）です。競合との差別化が重要です。")
        else:
            st.info(f"ℹ️ リースバック検索量：{rb}（標準水準）")
        if rm > 60:
            st.success(f"✅ リバースモーゲージ需要が高水準（{rm}）です。予算増額を推奨します。")
        else:
            st.info(f"ℹ️ リバースモーゲージ需要：{rm}（標準水準）")
    with col2:
        sale = latest.get('任意売却', 0)
        loan = latest.get('住宅ローン 払えない', 0)
        if sale > 60:
            st.success(f"✅ 任意売却需要が高水準（{sale}）です。困窮層へのアプローチ強化を推奨します。")
        if loan > 50:
            st.warning(f"⚠️ 住宅ローン困窮需要が上昇中（{loan}）です。緊急訴求クリエイティブを検討してください。")

# ──────────────────────────────
# TAB2：広告パフォーマンス
# ──────────────────────────────
with tab2:
    st.header("広告パフォーマンス")

    # 期間選択
    period = st.selectbox("表示期間", ["直近90日", "直近180日", "直近1年", "全期間"])
    period_map = {"直近90日": 90, "直近180日": 180, "直近1年": 365, "全期間": 9999}
    days = period_map[period]
    df_show = df.tail(days) if days < 9999 else df

    col1, col2 = st.columns(2)
    with col1:
        fig = px.line(df_show, x='date', y='コンバージョン',
                      title='日別コンバージョン数', markers=False)
        fig.update_traces(line_color='#00CC96')
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig2 = px.bar(df_show, x='date', y='費用',
                      title='日別広告費用', color_discrete_sequence=['#636EFA'])
        st.plotly_chart(fig2, use_container_width=True)

    # CPA推移
    df_cpa = df_show[df_show['CPA'] > 0].copy()
    if not df_cpa.empty:
        fig3 = px.line(df_cpa, x='date', y='CPA',
                       title='CPA推移（1CV獲得コスト）', markers=False)
        fig3.update_traces(line_color='#EF553B')
        avg_cpa = df_cpa['CPA'].mean()
        fig3.add_hline(y=avg_cpa, line_dash='dash',
                       annotation_text=f"平均CPA: ¥{avg_cpa:,.0f}")
        st.plotly_chart(fig3, use_container_width=True)

    # 年別サマリー
    st.subheader("📅 年別パフォーマンス比較")
    yearly = df[df['費用'] > 0].groupby('year').agg({
        'コンバージョン': 'sum',
        '費用': 'sum',
        'クリック数': 'sum'
    }).reset_index()
    yearly['CPA'] = (yearly['費用'] / yearly['コンバージョン']).round(0)
    yearly['費用'] = yearly['費用'].round(0)
    yearly['コンバージョン'] = yearly['コンバージョン'].round(1)
    st.dataframe(yearly, use_container_width=True)

    # 年別CPA推移グラフ
    fig_yearly = px.bar(yearly, x='year', y='CPA',
                        title='年別CPA推移（競合参入の影響）',
                        color='CPA', color_continuous_scale='Reds')
    st.plotly_chart(fig_yearly, use_container_width=True)
    st.warning("⚠️ 2024年以降のCPA悪化は競合参入の影響と考えられます。差別化戦略の強化が必要です。")

# ──────────────────────────────
# TAB3：曜日×時間帯分析
# ──────────────────────────────
with tab3:
    st.header("曜日×時間帯 パフォーマンス分析")

    metric = st.radio("表示指標", ["CV数", "CV率", "広告費用"], horizontal=True)

    if metric == "CV数":
        data = heatmap_cv
        title = "曜日×時間帯別 CV数ヒートマップ"
        fmt = ".1f"
    elif metric == "CV率":
        data = heatmap_cvrate * 100
        title = "曜日×時間帯別 CV率ヒートマップ（%）"
        fmt = ".2f"
    else:
        data = heatmap_cost / 10000
        title = "曜日×時間帯別 広告費ヒートマップ（万円）"
        fmt = ".1f"

    fig_heat = go.Figure(data=go.Heatmap(
        z=data.values,
        x=data.columns.tolist(),
        y=[f"{h}時" for h in data.index.tolist()],
        colorscale='RdYlGn',
        text=data.values.round(2),
        texttemplate=f"%{{text:{fmt}}}",
        showscale=True
    ))
    fig_heat.update_layout(
        title=title,
        height=700,
        xaxis_title="曜日",
        yaxis_title="時間帯",
        yaxis=dict(autorange='reversed')
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    st.subheader("💬 時間帯分析コメント")
    st.success("✅ **10〜17時がゴールデンタイム**：CV数が最も多い時間帯です。この時間帯の入札単価を重点的に引き上げてください。")
    st.info("📌 **火曜・木曜が最効率**：週間でCV数が最も多い曜日です。この曜日に予算を集中させることを推奨します。")
    st.warning("⚠️ **深夜0〜6時はCV効率が低い**：この時間帯の入札を抑制してコストを削減できます。")

    # 曜日別・時間帯別棒グラフ
    col1, col2 = st.columns(2)
    with col1:
        weekday_cv = heatmap_cv.sum(axis=0).reset_index()
        weekday_cv.columns = ['曜日', 'CV数']
        fig_w = px.bar(weekday_cv, x='曜日', y='CV数',
                       title='曜日別CV数合計',
                       color='CV数', color_continuous_scale='Blues')
        st.plotly_chart(fig_w, use_container_width=True)
    with col2:
        hour_cv = heatmap_cv.sum(axis=1).reset_index()
        hour_cv.columns = ['時間帯', 'CV数']
        fig_h = px.bar(hour_cv, x='時間帯', y='CV数',
                       title='時間帯別CV数合計',
                       color='CV数', color_continuous_scale='Greens')
        st.plotly_chart(fig_h, use_container_width=True)

# ──────────────────────────────
# TAB4：MMM分析結果
# ──────────────────────────────
with tab4:
    st.header("MMM分析結果")

    coef_main = coef[coef['variable'].str.startswith('trend_') |
                     (coef['variable'] == 'cost_adstock')].copy()
    coef_main['変数名'] = coef_main['variable'].map({
        'cost_adstock': '広告費（Adstock）',
        'trend_leaseback': 'リースバック検索',
        'trend_reverse_mortgage': 'リバースモーゲージ検索',
        'trend_reverse60': 'リバース60検索',
        'trend_sale': '任意売却検索',
        'trend_loan': '競売不動産検索',
        'trend_collateral': '不動産担保ローン検索',
        'trend_auction': '競売不動産検索',
    })
    coef_main['有意性'] = coef_main['pvalue'].apply(
        lambda p: '★★★ 有意' if p < 0.01 else ('★★ 有意' if p < 0.05 else '参考値'))

    fig4 = px.bar(coef_main, x='変数名', y='coefficient',
                  title='各要因のCV数への影響度（週次）',
                  color='coefficient',
                  color_continuous_scale='RdYlGn',
                  hover_data=['有意性', 'pvalue'])
    st.plotly_chart(fig4, use_container_width=True)

    st.subheader("💬 分析コメント")
    st.info("📌 広告費（Adstock）はCV数に最も確実な影響を与えています（p<0.001）。")
    st.warning("⚠️ 2025・2026年は同じ広告費でも週6〜7件CVが減少しています。競合参入による市場シェア低下が主因です。")
    st.success("✅ 競合が取りにくい緊急現金化層（最短5日訴求）への予算シフトが差別化の鍵です。")
    st.divider()
    st.subheader("📅 月別の季節性")
    col1, col2 = st.columns(2)
    with col1:
        st.warning("⚠️ **8月はCVが最も落ち込みます**（週約5.6件減・p<0.01）。お盆・夏季休暇の影響です。この時期は予算を抑えるか、緊急資金層への訴求に絞ることを推奨します。")
    with col2:
        st.warning("⚠️ **4月もCVが減少します**（週約3.8件減・p<0.05）。年度替わりで意思決定が後ろ倒しになる傾向です。")
    st.info("📌 **1月・5月は比較的好調**です。年始の資金計画・連休明けの行動開始が背景と考えられます。この時期に予算を集中させると効率的です。")

    st.divider()
    st.subheader("係数一覧")
    st.dataframe(coef_main[['変数名', 'coefficient', 'pvalue', '有意性']].round(4),
                 use_container_width=True)

# ──────────────────────────────
# TAB5：予算最適化
# ──────────────────────────────
with tab5:
    st.header("予算最適化シミュレーション")

    budget = st.number_input("月間予算（円）", value=1500000, step=50000)

    cost_coef = coef[coef['variable'] == 'cost_adstock']['coefficient'].values[0]

    # 曜日別推奨配分（時間帯分析結果ベース）
    weekday_cv_total = heatmap_cv.sum(axis=0)
    total_cv = weekday_cv_total.sum()
    weekday_names_jp = ['月曜日', '火曜日', '水曜日', '木曜日', '金曜日', '土曜日', '日曜日']

    alloc_df = pd.DataFrame({
        '曜日': weekday_cv_total.index.tolist(),
        'CV実績割合': (weekday_cv_total / total_cv * 100).round(1),
        '推奨日予算（円）': [
            round(budget / 30 * (weekday_cv_total[d] / total_cv) * 7)
            for d in weekday_cv_total.index
        ]
    })

    fig5 = px.bar(alloc_df, x='曜日', y='推奨日予算（円）',
                  title='曜日別 推奨予算配分（CV実績ベース）',
                  color='推奨日予算（円）',
                  color_continuous_scale='Blues')
    st.plotly_chart(fig5, use_container_width=True)

    st.dataframe(alloc_df, use_container_width=True)

    # CV予測
    monthly_adstock = budget * (1 / (1 - 0.4))
    predicted_cv = cost_coef * monthly_adstock / 4.3
    predicted_cv_month = predicted_cv * 4.3

    st.divider()
    st.subheader("💬 予算最適化コメント")
    st.success(f"✅ 月間予算 ¥{budget:,} の場合、月間CV数は約 **{max(predicted_cv_month, 0):.0f}件** と予測されます。")
    st.info("📌 火曜・木曜の10〜17時に予算を集中させることでCV効率が最大化できます。")
    st.warning("⚠️ 競合参入の影響でCPAが上昇傾向にあります。緊急現金化層への訴求強化で差別化を図ることを推奨します。")

    # 時間帯別推奨
    st.subheader("⏰ 時間帯別入札調整推奨")
    hour_cv_total = heatmap_cv.sum(axis=1)
    avg_cv = hour_cv_total.mean()
    bid_adj = pd.DataFrame({
        '時間帯': [f"{h}時" for h in hour_cv_total.index],
        'CV数': hour_cv_total.values.round(1),
        '推奨入札調整': [
            f"+{min(int((v/avg_cv-1)*100), 30)}%" if v > avg_cv * 1.2
            else (f"{max(int((v/avg_cv-1)*100), -30)}%" if v < avg_cv * 0.8 else "±0%")
            for v in hour_cv_total.values
        ]
    })
    st.dataframe(bid_adj, use_container_width=True)