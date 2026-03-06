# pages/2_short_term.py
# Short-term analysis groups by cat_level_3 (Sub-Type: Small Cap, Mid Cap, ELSS…)
# Meaningful metrics: momentum ranking, breadth per sub-type, consistency flag
import streamlit as st
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.filters import style_returns_df, bar_top_bottom, heatmap_category_returns, category_comparison_bar, plot_layout, get_group_col, C
import plotly.graph_objects as go

SHORT_MAP = {"return_7d":"1W","return_14d":"2W","return_30d":"1M","return_90d":"3M","return_180d":"6M"}

def show():
    st.markdown("""<div class="mf-header">
        <h1>📈 Short-Term Returns <span class="mf-badge">MOMENTUM</span></h1>
        <p>1W · 2W · 1M · 3M · 6M · Sub-type breadth · Momentum ranking</p>
    </div>""", unsafe_allow_html=True)

    if not st.session_state.get("data_loaded"):
        st.warning("⚠️ Load data from the sidebar first."); return

    df   = st.session_state.get("filtered_df", st.session_state["df"])
    full = st.session_state["df"]
    if len(df) < len(full):
        st.markdown(f'<div class="active-filter-bar">🎛️ Filters active — <b>{len(df):,}</b> of <b>{len(full):,}</b> schemes</div>', unsafe_allow_html=True)

    present_map = {k:v for k,v in SHORT_MAP.items() if k in df.columns}
    if not present_map:
        st.error("No short-term return columns found."); return

    # ── KPI: avg return + breadth per period ──────────────────────────────
    cols = st.columns(len(present_map))
    for i,(col_key,label) in enumerate(present_map.items()):
        s = df[col_key].dropna()
        if s.empty: continue
        avg = s.mean(); pos = (s>0).sum(); total = len(s)
        pct_pos = pos/max(total,1)*100
        color = C["green"] if avg>=0 else C["red"]
        sign  = "+" if avg>=0 else ""
        cols[i].markdown(f"""<div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value" style="color:{color}">{sign}{avg:.1f}%</div>
            <div class="kpi-sub">Breadth: {pct_pos:.0f}% positive</div>
            <div style="margin-top:8px;background:#E2E8F0;border-radius:4px;height:4px">
                <div style="background:{color};width:{pct_pos:.0f}%;height:100%;border-radius:4px"></div>
            </div></div>""", unsafe_allow_html=True)

    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(["📋 Scheme Table","🏆 Top & Bottom","🔥 Sub-Type Heatmap","📊 Breadth by Sub-Type"])

    with tab1:
        st.caption("All analysis uses Sub-Type (Small Cap, Mid Cap, ELSS…) as the peer group.")
        grp = get_group_col(df)
        disp_cols = ["scheme_name","amc_name","cat_level_2","cat_level_3","plan_type","option_type","latest_nav"]
        disp_cols = [c for c in disp_cols if c in df.columns] + list(present_map.keys())
        sort_col  = st.selectbox("Sort by", list(present_map.keys()), format_func=lambda x:present_map[x], key="st_sort")
        asc       = st.checkbox("Ascending", value=False, key="st_asc")
        disp      = df[disp_cols].sort_values(sort_col, ascending=asc).reset_index(drop=True)
        disp.index += 1
        rename = {**present_map, "scheme_name":"Scheme","amc_name":"AMC",
                  "cat_level_2":"Asset Class","cat_level_3":"Sub-Type",
                  "plan_type":"Plan","option_type":"Option","latest_nav":"NAV"}
        disp = disp.rename(columns=rename)
        st.dataframe(style_returns_df(disp, list(present_map.values())), use_container_width=True, height=500)
        st.download_button("⬇️ Download CSV", df[disp_cols].to_csv(index=False), "short_term.csv","text/csv")

    with tab2:
        col_a, col_b = st.columns(2)
        with col_a: sel = st.selectbox("Period", list(present_map.keys()), format_func=lambda x:present_map[x], key="st_tb")
        with col_b: n_show = st.slider("N per side", 5, 25, 10, key="st_n")
        st.plotly_chart(bar_top_bottom(df, sel, present_map[sel], n_show), use_container_width=True)

    with tab3:
        # Heatmap rows = Sub-Type (cat_level_3), cols = return periods
        # This is the correct analytics view — peer group performance at a glance
        grp = get_group_col(df)
        st.caption(f"Grouping by: **{grp.replace('cat_level_3','Sub-Type (e.g. Small Cap, ELSS)').replace('cat_level_2','Asset Class')}**")
        fig_hm = heatmap_category_returns(df, present_map, group_col=grp)
        if fig_hm.data:
            st.plotly_chart(fig_hm, use_container_width=True)
        else:
            st.info("Add more data or remove filters to see heatmap.")

    with tab4:
        # Market breadth by sub-type — tells you WHICH categories are running hot
        grp = get_group_col(df)
        if grp in df.columns and present_map:
            sel_b = st.selectbox("Period", list(present_map.keys()), format_func=lambda x:present_map[x], key="st_br")
            breadth_df = (
                df[~df[grp].isin(("NA","","Unknown"))]
                .groupby(grp)[sel_b]
                .apply(lambda x: (x>0).mean()*100).reset_index()
                .rename(columns={sel_b:"Breadth%",grp:"Sub-Type"})
                .sort_values("Breadth%", ascending=False)
            )
            colors = [C["green"] if v>=50 else C["red"] for v in breadth_df["Breadth%"]]
            fig_br = go.Figure(go.Bar(
                x=breadth_df["Sub-Type"], y=breadth_df["Breadth%"],
                marker_color=colors, marker_line_width=0,
                text=[f"{v:.0f}%" for v in breadth_df["Breadth%"]],
                textposition="outside",
                textfont=dict(family="DM Mono, monospace", size=11, color="#475569"),
            ))
            fig_br.add_hline(y=50, line_dash="dash", line_color="#CBD5E1",
                             annotation_text="50% — neutral line",
                             annotation_font_color="#94A3B8")
            fig_br.update_layout(**plot_layout(
                title=f"Market Breadth by Sub-Type — {present_map[sel_b]} (% schemes positive)",
                height=380, xaxis=dict(tickangle=-30),
            ))
            st.plotly_chart(fig_br, use_container_width=True)
            st.caption("Above 50% = majority of schemes in that sub-type are positive. Below 50% = majority are negative.")

show()
