# pages/3_long_term.py
# Long-term analytics: CAGR, percentile rank within sub-type, consistency score,
# rolling outperformance vs category median — grouped by cat_level_3 (Sub-Type)
import streamlit as st
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.filters import style_returns_df, bar_top_bottom, heatmap_category_returns, category_comparison_bar, plot_layout, get_group_col, C
import plotly.graph_objects as go

LONG_MAP = {"return_365d":"1Y","return_730d":"2Y","return_1095d":"3Y","cagr_3y":"3Y CAGR"}

def consistency_score(row, ret_cols):
    """% of available periods with positive return — simple consistency metric."""
    vals = [row.get(c) for c in ret_cols if c in row and pd.notna(row.get(c))]
    if not vals: return np.nan
    return sum(v>0 for v in vals)/len(vals)*100

def show():
    st.markdown("""<div class="mf-header">
        <h1>📊 Long-Term Returns <span class="mf-badge">COMPOUNDING</span></h1>
        <p>1Y · 2Y · 3Y CAGR · Percentile rank · Consistency · Sub-type comparison</p>
    </div>""", unsafe_allow_html=True)

    if not st.session_state.get("data_loaded"):
        st.warning("⚠️ Load data from the sidebar first."); return

    df   = st.session_state.get("filtered_df", st.session_state["df"]).copy()
    full = st.session_state["df"]
    if len(df) < len(full):
        st.markdown(f'<div class="active-filter-bar">🎛️ Filters active — <b>{len(df):,}</b> of <b>{len(full):,}</b> schemes</div>', unsafe_allow_html=True)

    present_map = {k:v for k,v in LONG_MAP.items() if k in df.columns}
    if not present_map:
        st.error("No long-term return columns found."); return

    # Add consistency score (% periods positive)
    all_ret_cols = list({"return_7d","return_14d","return_30d","return_90d",
                          "return_180d","return_365d","return_730d","return_1095d"} & set(df.columns))
    df["consistency_score"] = df.apply(lambda r: consistency_score(r, all_ret_cols), axis=1)

    # Add percentile rank within sub-type for each return period
    grp = get_group_col(df)
    if grp in df.columns and "return_365d" in df.columns:
        df["pct_rank_1y"] = df.groupby(grp)["return_365d"].rank(pct=True) * 100

    # ── KPI tiles ──────────────────────────────────────────────────────────────
    cols = st.columns(len(present_map) + 1)
    for i,(col_key,label) in enumerate(present_map.items()):
        valid = df[col_key].dropna()
        if valid.empty: continue
        avg = valid.mean(); med = valid.median(); top10 = valid.quantile(0.90)
        color = C["green"] if avg>=0 else C["red"]
        sign  = "+" if avg>=0 else ""
        cols[i].markdown(f"""<div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value" style="color:{color}">{sign}{avg:.1f}%</div>
            <div class="kpi-sub">Median: {med:+.1f}% · Top 10%: {top10:+.1f}%</div>
        </div>""", unsafe_allow_html=True)

    cons_avg = df["consistency_score"].mean()
    cols[len(present_map)].markdown(f"""<div class="kpi-card">
        <div class="kpi-label">AVG CONSISTENCY</div>
        <div class="kpi-value" style="color:{C['blue']}">{cons_avg:.0f}%</div>
        <div class="kpi-sub">% periods with +ve return</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Scheme Table","🏆 Top & Bottom","🔥 Sub-Type Heatmap","📐 Distribution","🎯 Sub-Type Comparison"
    ])

    with tab1:
        disp_cols = ["scheme_name","amc_name","cat_level_2","cat_level_3","plan_type","option_type","latest_nav"]
        disp_cols = [c for c in disp_cols if c in df.columns] + list(present_map.keys()) + ["consistency_score"]
        if "pct_rank_1y" in df.columns: disp_cols.append("pct_rank_1y")
        sort_col = st.selectbox("Sort by", list(present_map.keys()), format_func=lambda x:present_map[x], key="lt_sort")
        asc      = st.checkbox("Ascending", value=False, key="lt_asc")
        disp     = df[disp_cols].sort_values(sort_col, ascending=asc).reset_index(drop=True)
        disp.index += 1
        rename = {**present_map, "scheme_name":"Scheme","amc_name":"AMC",
                  "cat_level_2":"Asset Class","cat_level_3":"Sub-Type",
                  "plan_type":"Plan","option_type":"Option","latest_nav":"NAV",
                  "consistency_score":"Consistency%","pct_rank_1y":"Pctile Rank 1Y"}
        disp = disp.rename(columns=rename)
        ret_labels = list(present_map.values()) + ["Consistency%","Pctile Rank 1Y"]
        st.dataframe(style_returns_df(disp,[c for c in ret_labels if c in disp.columns]),
                     use_container_width=True, height=500)
        st.download_button("⬇️ Download CSV", df[disp_cols].to_csv(index=False), "long_term.csv","text/csv")

    with tab2:
        col_a,col_b = st.columns(2)
        with col_a: sel = st.selectbox("Period",list(present_map.keys()),format_func=lambda x:present_map[x],key="lt_sel")
        with col_b: n_show = st.slider("N per side",5,25,10,key="lt_n")
        st.plotly_chart(bar_top_bottom(df, sel, present_map[sel], n_show), use_container_width=True)

    with tab3:
        fig_hm = heatmap_category_returns(df, present_map, group_col=grp)
        if fig_hm.data:
            st.plotly_chart(fig_hm, use_container_width=True)
        else:
            st.info("Not enough data for heatmap.")

    with tab4:
        sel_d = st.selectbox("Period",list(present_map.keys()),format_func=lambda x:present_map[x],key="lt_dist")
        data  = df[sel_d].dropna()
        if not data.empty:
            fig = go.Figure()
            fig.add_trace(go.Histogram(x=data, nbinsx=50, marker_color=C["blue"],
                                        opacity=0.75, name="Schemes",
                                        marker_line_color="#FFFFFF", marker_line_width=0.5))
            fig.add_vline(x=data.mean(),   line_color=C["amber"], line_dash="dash",
                          annotation_text=f"Avg {data.mean():+.1f}%",   annotation_font_color=C["amber"])
            fig.add_vline(x=data.median(), line_color=C["green"], line_dash="dot",
                          annotation_text=f"Median {data.median():+.1f}%", annotation_font_color=C["green"])
            fig.add_vline(x=0, line_color=C["red"], line_width=1.5)
            fig.update_layout(**plot_layout(title=f"Return Distribution — {present_map[sel_d]}", height=360))
            st.plotly_chart(fig, use_container_width=True)

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                pct_df = pd.DataFrame({
                    "Percentile": ["5th","10th","25th","50th","75th","90th","95th"],
                    "Return":     [f"{np.percentile(data,p):+.2f}%" for p in [5,10,25,50,75,90,95]],
                })
                st.table(pct_df)
            with col_p2:
                st.metric("% Schemes Positive", f"{(data>0).mean()*100:.1f}%")
                st.metric("Std Deviation",      f"{data.std():.2f}%")
                st.metric("Skewness",           f"{data.skew():.2f}")

    with tab5:
        # The core analytics view — how each sub-type performed with avg, median, std dev
        sel_c = st.selectbox("Period",list(present_map.keys()),format_func=lambda x:present_map[x],key="lt_cat")
        st.plotly_chart(category_comparison_bar(df, sel_c, present_map[sel_c]), use_container_width=True)
        st.caption("Error bars show standard deviation within each sub-type — wider bars = more dispersed performance within that category.")

show()
