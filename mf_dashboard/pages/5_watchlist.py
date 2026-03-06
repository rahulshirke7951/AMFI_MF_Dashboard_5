# pages/5_watchlist.py
import streamlit as st
import pandas as pd
import numpy as np
import json
import requests
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.filters import style_returns_df, waterfall_returns, C, PLOTLY_THEME
import plotly.graph_objects as go

ALL_RETS = {
    "return_7d":    "1W",
    "return_14d":   "2W",
    "return_30d":   "1M",
    "return_90d":   "3M",
    "return_180d":  "6M",
    "return_365d":  "1Y",
    "return_730d":  "2Y",
    "return_1095d": "3Y",
    "cagr_3y":      "3Y CAGR",
}

SAMPLE_WL = {
    "Core Portfolio": {
        "description": "Long-term wealth creation schemes",
        "scheme_codes": ["100001", "100003", "100007"]
    },
    "Momentum Picks": {
        "description": "High recent momentum schemes",
        "scheme_codes": ["100005", "100010", "100011"]
    }
}


def load_watchlist_json(data: dict) -> dict:
    """Validate and normalize watchlist JSON."""
    result = {}
    for name, content in data.items():
        if isinstance(content, list):
            result[name] = {"description": "", "scheme_codes": [str(c) for c in content]}
        elif isinstance(content, dict) and "scheme_codes" in content:
            result[name] = {
                "description": content.get("description", ""),
                "scheme_codes": [str(c) for c in content["scheme_codes"]]
            }
    return result


def show():
    st.markdown("""
    <div class="mf-header">
        <h1>⭐ Watchlists <span class="mf-badge">PERSONAL</span></h1>
        <p>Track your selected schemes · Multiple named watchlists · JSON powered</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.get("data_loaded"):
        st.warning("⚠️ Load data from the sidebar first.")
        return

    df   = st.session_state.get("filtered_df", st.session_state["df"])
    full = st.session_state["df"]
    if "cagr_3y" not in df.columns and "return_1095d" in df.columns:
        df = df.copy()
        df["cagr_3y"] = ((1 + df["return_1095d"] / 100) ** (1/3) - 1) * 100

    # ── Load Watchlists ──
    st.markdown('<div class="section-title">LOAD WATCHLIST</div>', unsafe_allow_html=True)

    load_method = st.radio(
        "", ["📁 Upload JSON File", "🌐 GitHub Raw URL", "✏️ Sample / Manual"],
        horizontal=True, label_visibility="collapsed"
    )

    watchlists = st.session_state.get("watchlists", {})

    if load_method == "📁 Upload JSON File":
        wl_file = st.file_uploader("Upload watchlist JSON", type=["json"], label_visibility="collapsed")
        if wl_file:
            try:
                raw = json.load(wl_file)
                watchlists = load_watchlist_json(raw)
                st.session_state["watchlists"] = watchlists
                st.success(f"✅ Loaded {len(watchlists)} watchlist(s): {', '.join(watchlists.keys())}")
            except Exception as e:
                st.error(f"❌ Invalid JSON: {e}")

    elif load_method == "🌐 GitHub Raw URL":
        wl_url = st.text_input("Raw GitHub URL to watchlist JSON",
                                placeholder="https://raw.githubusercontent.com/...",
                                label_visibility="collapsed")
        if st.button("🔄 Load from GitHub", key="wl_gh"):
            try:
                resp = requests.get(wl_url, timeout=15)
                resp.raise_for_status()
                raw = resp.json()
                watchlists = load_watchlist_json(raw)
                st.session_state["watchlists"] = watchlists
                st.success(f"✅ Loaded {len(watchlists)} watchlist(s)")
            except Exception as e:
                st.error(f"❌ Failed: {e}")

    elif load_method == "✏️ Sample / Manual":
        if st.button("Load Sample Watchlist"):
            st.session_state["watchlists"] = SAMPLE_WL
            watchlists = SAMPLE_WL
            st.success("Sample watchlist loaded!")

        st.markdown("**JSON Format Reference:**")
        st.code(json.dumps({
            "My Portfolio": {
                "description": "Core long-term schemes",
                "scheme_codes": ["100001", "100003", "100007"]
            },
            "Sector Bets": {
                "description": "Tactical allocation",
                "scheme_codes": ["100016", "100017", "100023"]
            }
        }, indent=2), language="json")

    watchlists = st.session_state.get("watchlists", {})

    if not watchlists:
        st.info("👆 Load a watchlist JSON to get started.")
        return

    st.markdown("---")

    # ── Watchlist Selector ──
    st.markdown('<div class="section-title">SELECT WATCHLIST</div>', unsafe_allow_html=True)
    wl_names = list(watchlists.keys())
    selected_wl = st.selectbox("Choose Watchlist", wl_names, label_visibility="collapsed")

    wl_data   = watchlists[selected_wl]
    wl_desc   = wl_data.get("description", "")
    wl_codes  = [str(c) for c in wl_data.get("scheme_codes", [])]

    # ── Watchlist overview badges ──
    badge_html = " ".join([
        f'<span class="wl-tag" style="background:rgba(59,130,246,0.12);border-color:rgba(59,130,246,0.3);color:#2563EB">{name} ({len(wl["scheme_codes"])})</span>'
        for name, wl in watchlists.items()
    ])
    st.markdown(f"""
    <div style='margin:8px 0 16px'>
        <div style='color:#475569;font-size:0.75rem;margin-bottom:6px'>ALL WATCHLISTS</div>
        {badge_html}
    </div>
    <div style='background:#FFFFFF;border:1px solid #E2E8F0;border-radius:10px;
    padding:14px 18px;margin-bottom:16px'>
        <span style='font-weight:600;color:#0F172A'>{selected_wl}</span>
        {"<span style='color:#64748B;font-size:0.85rem;margin-left:12px'>" + wl_desc + "</span>" if wl_desc else ""}
        <span style='float:right;color:#64748B;font-size:0.8rem'>{len(wl_codes)} schemes</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Match codes to data ──
    df_wl = df[df["scheme_code"].astype(str).isin(wl_codes)].copy()
    not_found = [c for c in wl_codes if c not in df["scheme_code"].astype(str).values]

    if not_found:
        st.warning(f"⚠️ {len(not_found)} scheme code(s) not found in loaded data: `{', '.join(not_found)}`")

    if df_wl.empty:
        st.error("No matching schemes found. Check your scheme codes.")
        return

    present_rets = {k: v for k, v in ALL_RETS.items() if k in df_wl.columns}

    # ── KPI row for this watchlist ──
    st.markdown('<div class="section-title">WATCHLIST SUMMARY</div>', unsafe_allow_html=True)
    kpi_cols = st.columns(5)

    def wl_kpi(col, label, value, sub=""):
        col.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value" style="font-size:1.4rem">{value}</div>
            <div class="kpi-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

    avg_1y = df_wl["return_365d"].mean() if "return_365d" in df_wl.columns else None
    avg_1m = df_wl["return_30d"].mean()  if "return_30d"  in df_wl.columns else None
    best   = df_wl.loc[df_wl["return_365d"].idxmax(), "scheme_name"][:25] if "return_365d" in df_wl.columns and not df_wl["return_365d"].isna().all() else "—"
    worst  = df_wl.loc[df_wl["return_365d"].idxmin(), "scheme_name"][:25] if "return_365d" in df_wl.columns and not df_wl["return_365d"].isna().all() else "—"

    wl_kpi(kpi_cols[0], "SCHEMES",       len(df_wl),                "Matched in data")
    wl_kpi(kpi_cols[1], "AVG 1Y RETURN", f"{avg_1y:+.2f}%" if avg_1y else "—", "Watchlist average")
    wl_kpi(kpi_cols[2], "AVG 1M RETURN", f"{avg_1m:+.2f}%" if avg_1m else "—", "Recent momentum")
    wl_kpi(kpi_cols[3], "BEST 1Y",       best,                      f"{df_wl['return_365d'].max():+.1f}%" if "return_365d" in df_wl.columns else "")
    wl_kpi(kpi_cols[4], "WORST 1Y",      worst,                     f"{df_wl['return_365d'].min():+.1f}%" if "return_365d" in df_wl.columns else "")

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📋 Returns Table", "📊 Compare Chart", "🔬 Scheme Detail"])

    with tab1:
        show_cols = ["scheme_name","amc_name","cat_level_1","cat_level_2","plan_type","option_type","latest_nav"]
        show_cols = [c for c in show_cols if c in df_wl.columns] + list(present_rets.keys())
        disp = df_wl[show_cols].reset_index(drop=True)
        disp.index += 1
        rename = {**present_rets,
                  "scheme_name":"Scheme","amc_name":"AMC","cat_level_1":"Category",
                  "cat_level_2":"Sub-Cat","plan_type":"Plan","option_type":"Option","latest_nav":"NAV"}
        disp = disp.rename(columns=rename)

        st.dataframe(style_returns_df(disp, list(present_rets.values())),
                     use_container_width=True, height=420)
        st.download_button("⬇️ Export Watchlist CSV",
                            df_wl[show_cols].to_csv(index=False),
                            f"watchlist_{selected_wl.replace(' ','_')}.csv", "text/csv")

    with tab2:
        sel_period = st.selectbox("Compare by", list(present_rets.keys()),
                                   format_func=lambda x: present_rets[x], key="wl_cmp")
        sub = df_wl.dropna(subset=[sel_period]).sort_values(sel_period, ascending=True)
        if not sub.empty:
            colors = [C["green"] if v >= 0 else C["red"] for v in sub[sel_period]]
            fig = go.Figure(go.Bar(
                x=sub[sel_period],
                y=sub["scheme_name"].str[:40],
                orientation="h",
                marker_color=colors,
                text=[f"{v:+.1f}%" for v in sub[sel_period]],
                textposition="outside",
                textfont=dict(family="DM Mono", size=10, color="#94A3B8"),
            ))
            fig.update_layout(
                title=f"Watchlist Comparison — {present_rets[sel_period]}",
                height=max(300, 35 * len(sub)),
                **plot_layout(yaxis=dict(autorange="reversed")),
            )
            st.plotly_chart(fig, use_container_width=True)

        # Multi-period grouped bar
        if len(present_rets) >= 3 and len(df_wl) <= 20:
            st.markdown("#### Multi-Period Comparison")
            key_periods = {k: v for k, v in present_rets.items()
                           if k in ["return_30d","return_180d","return_365d","cagr_3y"]}
            if key_periods:
                fig2 = go.Figure()
                colors_list = [C["cyan"], C["blue"], C["green"], C["amber"]]
                for i, (col_k, lbl) in enumerate(key_periods.items()):
                    fig2.add_trace(go.Bar(
                        name=lbl,
                        x=df_wl["scheme_name"].str[:30],
                        y=df_wl[col_k],
                        marker_color=colors_list[i % len(colors_list)],
                        opacity=0.85,
                    ))
                fig2.add_hline(y=0, line_color=C["border"], line_width=1)
                fig2.update_layout(
                    barmode="group",
                    title="Multi-Period Returns per Scheme",
                    height=450,
                    xaxis_tickangle=-35,
                    **plot_layout(),
                    legend=dict(font=dict(color="#94A3B8"), bgcolor="rgba(0,0,0,0)")
                )
                st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        sel_scheme = st.selectbox("Select Scheme", df_wl["scheme_name"].tolist(), key="wl_dd")
        row = df_wl[df_wl["scheme_name"] == sel_scheme].iloc[0]

        cat  = row.get("cat_level_2","") or row.get("cat_level_1","")
        plan = row.get("plan_type","")
        amc  = row.get("amc_name","")

        st.markdown(f"""
        <div style='background:#FFFFFF;border:1px solid #1e3a5f;border-radius:12px;
        padding:18px 22px;margin:8px 0 16px'>
            <div style='font-size:1rem;font-weight:700;color:#0F172A'>{sel_scheme}</div>
            <div style='margin-top:6px;display:flex;gap:8px;flex-wrap:wrap'>
                <span class='wl-tag'>{amc}</span>
                <span class='wl-tag'>{cat}</span>
                <span class='wl-tag'>{plan}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.plotly_chart(waterfall_returns(row, present_rets), use_container_width=True)

show()
