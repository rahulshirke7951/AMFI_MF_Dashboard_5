# pages/4_screener.py
# Screener: filter by return thresholds + deep dive with percentile rank within sub-type
import streamlit as st
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.filters import style_returns_df, waterfall_returns, plot_layout, get_group_col, C
import plotly.graph_objects as go

ALL_RETS = {"return_7d":"1W","return_14d":"2W","return_30d":"1M","return_90d":"3M",
            "return_180d":"6M","return_365d":"1Y","return_730d":"2Y","return_1095d":"3Y","cagr_3y":"3Y CAGR"}

def show():
    st.markdown("""<div class="mf-header">
        <h1>🔍 Scheme Screener <span class="mf-badge">ADVANCED</span></h1>
        <p>Return thresholds · Percentile rank within sub-type · Scheme deep dive</p>
    </div>""", unsafe_allow_html=True)

    if not st.session_state.get("data_loaded"):
        st.warning("⚠️ Load data from the sidebar first."); return

    df   = st.session_state.get("filtered_df", st.session_state["df"]).copy()
    full = st.session_state["df"]
    if len(df) < len(full):
        st.markdown(f'<div class="active-filter-bar">🎛️ Filters active — <b>{len(df):,}</b> of <b>{len(full):,}</b> schemes</div>', unsafe_allow_html=True)

    present_rets = {k:v for k,v in ALL_RETS.items() if k in df.columns}
    grp          = get_group_col(df)

    # Add percentile rank within sub-type for 1Y — key MF metric
    if grp in df.columns and "return_365d" in df.columns:
        df["peer_rank_1y"] = df.groupby(grp)["return_365d"].rank(pct=True) * 100
    if grp in df.columns and "return_90d" in df.columns:
        df["peer_rank_3m"] = df.groupby(grp)["return_90d"].rank(pct=True) * 100

    # ── Optional threshold filters ──
    with st.expander("🎯 Return Threshold Filters"):
        tc = st.columns(4)
        thresholds = {}
        for i,(col_key,label) in enumerate(list(present_rets.items())[:8]):
            with tc[i%4]:
                mn = float(df[col_key].min()) if col_key in df.columns else -100.0
                mx = float(df[col_key].max()) if col_key in df.columns else 100.0
                if not np.isnan(mn) and not np.isnan(mx) and mn < mx:
                    rng = st.slider(f"{label} (%)", mn, mx, (mn, mx), step=0.5, key=f"sc_{col_key}")
                    thresholds[col_key] = rng
    for col_key,(lo,hi) in thresholds.items():
        df = df[(df[col_key].isna()) | ((df[col_key]>=lo) & (df[col_key]<=hi))]

    st.markdown(f"<div style='color:#64748B;font-size:0.8rem;margin:6px 0 16px'>Showing <b style='color:#2563EB'>{len(df):,}</b> schemes after all filters</div>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📋 Screener Table","🔬 Scheme Deep Dive"])

    with tab1:
        sort_by  = st.selectbox("Sort by", list(present_rets.keys()), format_func=lambda x:present_rets[x],
                                 key="sc_sort", index=min(5, len(present_rets)-1))
        asc      = st.checkbox("Ascending", value=False, key="sc_asc")
        show_cols = ["scheme_name","amc_name","cat_level_2","cat_level_3","plan_type","option_type","latest_nav"]
        show_cols = [c for c in show_cols if c in df.columns] + list(present_rets.keys())
        if "peer_rank_1y" in df.columns: show_cols.append("peer_rank_1y")
        if "peer_rank_3m" in df.columns: show_cols.append("peer_rank_3m")

        disp = df[show_cols].sort_values(sort_by, ascending=asc).reset_index(drop=True)
        disp.index += 1
        rename = {**present_rets,"scheme_name":"Scheme","amc_name":"AMC",
                  "cat_level_2":"Asset Class","cat_level_3":"Sub-Type",
                  "plan_type":"Plan","option_type":"Option","latest_nav":"NAV",
                  "peer_rank_1y":"Peer%ile 1Y","peer_rank_3m":"Peer%ile 3M"}
        disp = disp.rename(columns=rename)
        ret_labels = list(present_rets.values()) + ["Peer%ile 1Y","Peer%ile 3M"]
        st.dataframe(style_returns_df(disp,[c for c in ret_labels if c in disp.columns]),
                     use_container_width=True, height=540)
        st.download_button("⬇️ Download CSV", df[show_cols].to_csv(index=False), "screener.csv","text/csv")

    with tab2:
        all_names = df["scheme_name"].sort_values().tolist()
        if not all_names:
            st.info("No schemes match current filters."); return

        selected = st.selectbox("🔍 Select a Scheme", all_names, key="sc_dd")
        row      = df[df["scheme_name"]==selected].iloc[0]

        sub_type  = row.get("cat_level_3","") or row.get("cat_level_2","")
        asset_cls = row.get("cat_level_2","")
        amc       = row.get("amc_name","")
        plan      = row.get("plan_type","")
        opt       = row.get("option_type","")

        st.markdown(f"""<div style='background:#FFFFFF;border:1px solid #E2E8F0;border-radius:10px;
        padding:16px 20px;margin:8px 0 16px;box-shadow:0 1px 4px rgba(0,0,0,0.04)'>
            <div style='font-size:0.95rem;font-weight:700;color:#0F172A'>{selected}</div>
            <div style='margin-top:6px;display:flex;gap:6px;flex-wrap:wrap'>
                <span class='wl-tag'>{amc}</span>
                <span class='wl-tag'>{asset_cls}</span>
                <span class='wl-tag'>{sub_type}</span>
                <span class='wl-tag'>{plan}</span>
                <span class='wl-tag'>{opt}</span>
            </div></div>""", unsafe_allow_html=True)

        nav  = row.get("latest_nav")
        r1m  = row.get("return_30d")
        r1y  = row.get("return_365d")
        cagr = row.get("cagr_3y")
        rank = row.get("peer_rank_1y")

        k1,k2,k3,k4,k5 = st.columns(5)
        k1.metric("Latest NAV",   f"₹{float(nav):.2f}" if pd.notna(nav) else "—")
        k2.metric("1M Return",    f"{float(r1m):+.2f}%" if pd.notna(r1m) else "—")
        k3.metric("1Y Return",    f"{float(r1y):+.2f}%" if pd.notna(r1y) else "—")
        k4.metric("3Y CAGR",      f"{float(cagr):+.2f}%" if pd.notna(cagr) else "—")
        k5.metric("Peer %ile 1Y", f"{float(rank):.0f}th" if pd.notna(rank) else "—",
                  help="Percentile rank within sub-type — higher is better")

        # Returns waterfall
        st.plotly_chart(waterfall_returns(row, present_rets), use_container_width=True)

        # Distribution of peers + this scheme's position
        if sub_type and sub_type not in ("NA","") and "return_365d" in df.columns:
            peers       = full[full[grp] == sub_type].copy() if grp in full.columns else pd.DataFrame()
            scheme_val  = row.get("return_365d")

            if not peers.empty and pd.notna(scheme_val):
                peer_1y = peers["return_365d"].dropna()
                rank_n  = (peer_1y >= float(scheme_val)).sum()
                total   = len(peer_1y)
                pctile  = int((1 - rank_n/total)*100) if total > 0 else None

                st.markdown(f"""<div style='background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;
                padding:14px 18px;margin:10px 0'>
                    <div class='kpi-label'>PEER RANK IN {sub_type}</div>
                    <div style='display:flex;align-items:baseline;gap:10px;margin-top:6px'>
                        <div style='font-size:2rem;font-weight:700;color:#2563EB;font-family:DM Mono,monospace'>#{rank_n}</div>
                        <div>
                            <div style='color:#0F172A;font-size:0.85rem'>of {total} peers (1Y Return)</div>
                            <div style='color:#64748B;font-size:0.75rem'>{"Top "+str(100-pctile)+"th percentile" if pctile else ""}</div>
                        </div>
                    </div></div>""", unsafe_allow_html=True)

                fig = go.Figure()
                fig.add_trace(go.Histogram(x=peer_1y, nbinsx=40, marker_color=C["blue"],
                                            opacity=0.6, name="All peers",
                                            marker_line_color="#FFFFFF", marker_line_width=0.5))
                fig.add_vline(x=float(scheme_val), line_color=C["amber"], line_width=2.5,
                              annotation_text=f"{selected[:30]}: {scheme_val:+.1f}%",
                              annotation_font_color=C["amber"])
                fig.add_vline(x=peer_1y.median(), line_color=C["slate"], line_dash="dot",
                              annotation_text=f"Category median: {peer_1y.median():+.1f}%",
                              annotation_font_color=C["slate"])
                fig.update_layout(**plot_layout(
                    title=f"1Y Return — {sub_type} universe ({total} schemes)",
                    height=300,
                ))
                st.plotly_chart(fig, use_container_width=True)

show()
