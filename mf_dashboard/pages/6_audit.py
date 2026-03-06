# pages/6_audit.py
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.filters import C, PLOTLY_THEME
import plotly.graph_objects as go

def show():
    st.markdown("""
    <div class="mf-header">
        <h1>📋 Audit Trail <span class="mf-badge">SYSTEM</span></h1>
        <p>Data freshness · Stale schemes · Pipeline health</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.get("data_loaded"):
        st.warning("⚠️ Load data from the sidebar first.")
        return

    df       = st.session_state["df"]
    stale_df = st.session_state.get("stale_df", pd.DataFrame())

    # ── KPIs ──
    k1, k2, k3, k4 = st.columns(4)
    anchor = df["latest_nav_date"].max().strftime("%d %b %Y") if "latest_nav_date" in df.columns else "—"
    oldest = df["latest_nav_date"].min().strftime("%d %b %Y") if "latest_nav_date" in df.columns else "—"

    for col, label, val, sub in [
        (k1, "ACTIVE SCHEMES",  f"{len(df):,}",        "Passed freshness check"),
        (k2, "STALE / EXCLUDED",f"{len(stale_df):,}",  "Below threshold"),
        (k3, "LATEST NAV DATE", anchor,                 "Most recent"),
        (k4, "OLDEST ACTIVE",   oldest,                 "Min latest_nav_date"),
    ]:
        col.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value" style="font-size:1.4rem">{val}</div>
            <div class="kpi-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── NAV date distribution ──
    st.markdown('<div class="section-title">NAV DATE DISTRIBUTION</div>', unsafe_allow_html=True)
    if "latest_nav_date" in df.columns:
        date_counts = df["latest_nav_date"].value_counts().sort_index()
        fig = go.Figure(go.Bar(
            x=date_counts.index, y=date_counts.values,
            marker_color=C["blue"], opacity=0.8,
        ))
        layout = dict(PLOTLY_THEME)
        layout.update({"title":"Schemes per Latest NAV Date","height":320})
        layout["xaxis"] = dict(**layout.get("xaxis",{}), title="Date")
        layout["yaxis"] = dict(**layout.get("yaxis",{}), title="Scheme Count")
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True)

    # ── Stale table ──
    if not stale_df.empty:
        st.markdown('<div class="section-title">STALE / EXCLUDED SCHEMES</div>', unsafe_allow_html=True)
        st.dataframe(stale_df.reset_index(drop=True), use_container_width=True, height=360)
        st.download_button("⬇️ Download Stale Schemes CSV",
                            stale_df.to_csv(index=False),
                            "stale_schemes.csv", "text/csv")
    else:
        st.info("No stale scheme data found (Full_Audit_Trail sheet missing or all schemes active).")

    # ── Active data preview ──
    st.markdown('<div class="section-title">ACTIVE SCHEMES — DATA PREVIEW</div>', unsafe_allow_html=True)
    preview_cols = ["scheme_code","scheme_name","amc_name","cat_level_1","cat_level_2",
                    "plan_type","option_type","latest_nav","latest_nav_date"]
    preview_cols = [c for c in preview_cols if c in df.columns]
    st.dataframe(df[preview_cols].head(100), use_container_width=True, height=400)

show()
