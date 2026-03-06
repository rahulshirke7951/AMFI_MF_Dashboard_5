# pages/1_overview.py
import streamlit as st
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.filters import heatmap_category_returns, category_comparison_bar, C, plot_layout, get_group_col
import plotly.graph_objects as go

ALL_RETS = {"return_30d":"1M","return_90d":"3M","return_180d":"6M",
            "return_365d":"1Y","return_730d":"2Y","return_1095d":"3Y"}

def show():
    st.markdown("""<div class="mf-header">
        <h1>📊 Market Overview <span class="mf-badge">LIVE</span></h1>
        <p>Sub-type heatmap · AMC leaderboard · Market breadth</p>
    </div>""", unsafe_allow_html=True)

    if not st.session_state.get("data_loaded"):
        st.info("📂 Load data using the sidebar — paste GitHub URL → click Load / Refresh")
        return

    df   = st.session_state.get("filtered_df", st.session_state["df"])
    full = st.session_state["df"]

    if len(df) < len(full):
        st.markdown(f'<div class="active-filter-bar">🎛️ Filters active — showing <b>{len(df):,}</b> of <b>{len(full):,}</b> schemes</div>', unsafe_allow_html=True)

    anchor = df["latest_nav_date"].max().strftime("%d %b %Y") if "latest_nav_date" in df.columns else "—"
    avg_1y = df["return_365d"].mean()  if "return_365d" in df.columns else None
    avg_6m = df["return_180d"].mean()  if "return_180d" in df.columns else None
    # Sub-types = cat_level_3 (Small Cap, Mid Cap, ELSS…) — the key analytics level
    n_sub  = df["cat_level_3"].replace({"NA":pd.NA,"":pd.NA}).dropna().nunique() if "cat_level_3" in df.columns else 0
    breadth_1y = (df["return_365d"] > 0).mean() * 100 if "return_365d" in df.columns else None

    k1,k2,k3,k4,k5 = st.columns(5)
    def kpi(col, label, value, sub=""):
        col.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub">{sub}</div></div>""", unsafe_allow_html=True)

    kpi(k1, "ANCHOR DATE",    anchor,                                               "Latest NAV date")
    kpi(k2, "SCHEMES",        f"{len(df):,}",                                       "After filters")
    kpi(k3, "AVG 1Y RETURN",  f"{avg_1y:+.1f}%" if avg_1y is not None else "—",    "Filtered universe")
    kpi(k4, "AVG 6M RETURN",  f"{avg_6m:+.1f}%" if avg_6m is not None else "—",    "Filtered universe")
    kpi(k5, "MARKET BREADTH", f"{breadth_1y:.0f}%" if breadth_1y is not None else "—", "% schemes +ve 1Y")

    st.markdown("---")

    # ── Heatmap: Sub-Type × Return Period (cat_level_3 is the row grouping) ──
    st.markdown('<div class="section-title">PERFORMANCE HEATMAP — BY SUB-TYPE × PERIOD</div>', unsafe_allow_html=True)
    present_rets = {k:v for k,v in ALL_RETS.items() if k in df.columns}
    if present_rets:
        grp = get_group_col(df)
        fig_heat = heatmap_category_returns(df, present_rets, group_col=grp)
        if fig_heat.data:
            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.info("Not enough data for heatmap with current filters.")
    st.markdown("---")

    # ── AMC Leaderboard — sorted by avg 1Y, coloured by breadth ──
    st.markdown('<div class="section-title">AMC LEADERBOARD — AVG 1Y RETURN</div>', unsafe_allow_html=True)
    if "amc_name" in df.columns and "return_365d" in df.columns:
        amc_perf = (df.groupby("amc_name")["return_365d"]
                    .agg(["mean","count","median"])
                    .rename(columns={"mean":"Avg","count":"N","median":"Median"})
                    .sort_values("Avg", ascending=False).head(20).reset_index())
        colors = [C["green"] if v >= 0 else C["red"] for v in amc_perf["Avg"]]
        fig_amc = go.Figure(go.Bar(
            x=amc_perf["Avg"], y=amc_perf["amc_name"],
            orientation="h", marker_color=colors, marker_line_width=0,
            text=[f"{v:+.1f}%" for v in amc_perf["Avg"]],
            textposition="outside",
            textfont=dict(family="DM Mono, monospace", size=10, color="#475569"),
            customdata=list(zip(amc_perf["N"], amc_perf["Median"])),
            hovertemplate="<b>%{y}</b><br>Avg 1Y: %{x:+.1f}%<br>Median: %{customdata[1]:+.1f}%<br>Schemes: %{customdata[0]}<extra></extra>",
        ))
        fig_amc.update_layout(**plot_layout(
            title="Top 20 AMCs by Avg 1Y Return (bars = avg, hover = median)",
            height=520, yaxis=dict(autorange="reversed"),
        ))
        st.plotly_chart(fig_amc, use_container_width=True)

show()
