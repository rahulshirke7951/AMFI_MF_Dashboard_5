import streamlit as st
import os, sys, importlib.util, pandas as pd

st.set_page_config(
    page_title="MF Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Light professional theme — DM Sans / Bloomberg daylight ──────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=DM+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background: #F8FAFC !important;
    color: #0F172A !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid #E2E8F0 !important;
}
[data-testid="stSidebar"] * { color: #334155 !important; }
[data-testid="stSidebar"] .stTextInput > div > div {
    background: #F8FAFC !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 6px !important;
    color: #0F172A !important;
}
[data-testid="stSidebar"] .stMultiSelect > div > div {
    background: #F8FAFC !important;
    border: 1px solid #CBD5E1 !important;
    color: #0F172A !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: #F1F5F9 !important;
    border: 1px solid #CBD5E1 !important;
    color: #334155 !important;
    border-radius: 6px !important;
    font-size: 0.8rem !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #E2E8F0 !important;
}

/* Sidebar collapse arrow — always visible */
[data-testid="collapsedControl"] {
    display: flex !important;
    background: #FFFFFF !important;
    border-right: 1px solid #E2E8F0 !important;
    color: #64748B !important;
}
section[data-testid="stSidebar"][aria-expanded="false"] {
    width: 0px !important;
    min-width: 0px !important;
}

/* ── Main content ── */
[data-testid="stMain"] { background: #F8FAFC !important; }
.block-container { padding: 1.5rem 2rem !important; }

/* ── Page header ── */
.mf-header {
    background: linear-gradient(135deg, #1E40AF 0%, #2563EB 60%, #0EA5E9 100%);
    border-radius: 12px;
    padding: 24px 32px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 4px 24px rgba(37,99,235,0.15);
}
.mf-header::after {
    content: '';
    position: absolute; top: 0; right: 0; width: 300px; height: 100%;
    background: radial-gradient(ellipse at right center, rgba(255,255,255,0.08) 0%, transparent 70%);
}
.mf-header h1 { margin: 0; font-size: 1.6rem; font-weight: 700; color: #FFFFFF; letter-spacing: -0.3px; }
.mf-header p  { margin: 5px 0 0; color: rgba(255,255,255,0.7); font-size: 0.85rem; }
.mf-badge {
    display: inline-block;
    background: rgba(255,255,255,0.2);
    border: 1px solid rgba(255,255,255,0.3);
    color: #FFFFFF;
    padding: 2px 10px; border-radius: 20px;
    font-size: 0.68rem; font-weight: 700; letter-spacing: 0.8px; margin-left: 10px; vertical-align: middle;
}

/* ── KPI cards ── */
.kpi-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 16px 18px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    transition: box-shadow 0.2s, border-color 0.2s;
    height: 100%;
}
.kpi-card:hover { box-shadow: 0 4px 12px rgba(37,99,235,0.10); border-color: #BFDBFE; }
.kpi-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #2563EB, #0EA5E9);
}
.kpi-label { font-size: 0.67rem; color: #94A3B8; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 6px; }
.kpi-value { font-size: 1.5rem; font-weight: 700; color: #0F172A; font-family: 'DM Mono', monospace; line-height: 1.1; }
.kpi-sub   { font-size: 0.7rem; color: #94A3B8; margin-top: 5px; }

/* ── Return colors ── */
.ret-pos { color: #16A34A; font-weight: 600; font-family: 'DM Mono', monospace; }
.ret-neg { color: #DC2626; font-weight: 600; font-family: 'DM Mono', monospace; }
.ret-neu { color: #64748B; font-family: 'DM Mono', monospace; }

/* ── Section title ── */
.section-title {
    font-size: 0.72rem; font-weight: 700; color: #64748B;
    letter-spacing: 1.2px; text-transform: uppercase;
    border-left: 3px solid #2563EB;
    padding-left: 10px; margin: 20px 0 12px;
}

/* ── Filter active bar ── */
.active-filter-bar {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-radius: 6px;
    padding: 8px 14px;
    margin-bottom: 14px;
    font-size: 0.78rem;
    color: #1E40AF;
}

/* ── Watchlist tag ── */
.wl-tag {
    display: inline-block;
    background: #F0FDF4; border: 1px solid #BBF7D0; color: #15803D;
    padding: 2px 10px; border-radius: 20px;
    font-size: 0.7rem; font-weight: 600; margin: 2px;
}

/* ── Streamlit overrides ── */
div[data-testid="metric-container"] {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 10px !important;
    padding: 14px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
}
div[data-testid="metric-container"] label { color: #94A3B8 !important; font-size: 0.7rem !important; }
div[data-testid="metric-container"] [data-testid="metric-value"] {
    color: #0F172A !important; font-family: 'DM Mono', monospace !important;
}

.stSelectbox > div > div,
.stMultiSelect > div > div {
    background: #FFFFFF !important;
    border-color: #CBD5E1 !important;
    color: #0F172A !important;
}
.stTextInput > div > div {
    background: #FFFFFF !important;
    border-color: #CBD5E1 !important;
}

.stDataFrame { background: #FFFFFF !important; }
.stDataFrame th { background: #F1F5F9 !important; color: #475569 !important; }

button[kind="primary"] {
    background: linear-gradient(135deg, #2563EB, #0EA5E9) !important;
    border: none !important; border-radius: 7px !important;
    font-weight: 600 !important; color: #FFFFFF !important;
}

.stTabs [data-baseweb="tab"] { color: #64748B !important; font-weight: 500 !important; }
.stTabs [aria-selected="true"] { color: #2563EB !important; border-bottom-color: #2563EB !important; }
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 2px solid #E2E8F0 !important;
}

hr { border-color: #E2E8F0 !important; }
.stAlert { background: #F8FAFC !important; border-color: #E2E8F0 !important; }

/* Multiselect tags */
[data-baseweb="tag"] {
    background: #EFF6FF !important;
    border: 1px solid #BFDBFE !important;
    color: #1E40AF !important;
}

/* Download button */
.stDownloadButton > button {
    background: #F1F5F9 !important;
    border: 1px solid #CBD5E1 !important;
    color: #475569 !important;
    border-radius: 6px !important;
    font-size: 0.8rem !important;
}
</style>
""", unsafe_allow_html=True)

base = os.path.dirname(__file__)
sys.path.insert(0, base)


def load_page(path):
    spec = importlib.util.spec_from_file_location("page", path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)


# ════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════
st.sidebar.markdown("""
<div style='padding:16px 12px 8px'>
    <div style='font-size:1.05rem;font-weight:700;color:#0F172A;letter-spacing:-0.3px'>📊 MF Intelligence</div>
    <div style='font-size:0.7rem;color:#94A3B8;margin-top:2px'>Mutual Fund Analytics · v3.3</div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("<hr style='border-color:#E2E8F0;margin:4px 0 10px'>", unsafe_allow_html=True)

st.sidebar.markdown("<div style='font-size:0.62rem;color:#94A3B8;letter-spacing:1.2px;font-weight:700;padding:0 4px 6px;text-transform:uppercase'>Navigation</div>", unsafe_allow_html=True)

pages = {
    "🏠  Overview":           "pages/1_overview.py",
    "📈  Short-Term Returns": "pages/2_short_term.py",
    "📊  Long-Term Returns":  "pages/3_long_term.py",
    "🔍  Scheme Screener":    "pages/4_screener.py",
    "⭐  Watchlists":         "pages/5_watchlist.py",
    "📋  Audit Trail":        "pages/6_audit.py",
}
page = st.sidebar.radio("", list(pages.keys()), label_visibility="collapsed")

st.sidebar.markdown("<hr style='border-color:#E2E8F0;margin:10px 0'>", unsafe_allow_html=True)

# ── Data Source ──
st.sidebar.markdown("<div style='font-size:0.62rem;color:#94A3B8;letter-spacing:1.2px;font-weight:700;padding:0 4px 6px;text-transform:uppercase'>📡 Data Source</div>", unsafe_allow_html=True)

gh_url = st.sidebar.text_input(
    "GitHub Raw URL",
    value=st.session_state.get("gh_url_saved", ""),
    placeholder="https://raw.githubusercontent.com/…/dashboard_data.xlsx",
    label_visibility="collapsed",
)

col_load, col_clear = st.sidebar.columns([3, 1])
with col_load:
    load_clicked  = st.button("🔄 Load / Refresh", use_container_width=True, key="load_btn")
with col_clear:
    clear_clicked = st.button("🗑️", use_container_width=True, key="clear_btn")

FILTER_KEYS = ["filtered_df","gf_cat1","gf_cat2","gf_cat3","gf_amc","gf_plan","gf_option","gf_search"]

if clear_clicked:
    for k in ["df","stale_df","data_loaded","gh_url_saved"] + FILTER_KEYS:
        st.session_state.pop(k, None)
    st.rerun()

if load_clicked:
    if gh_url.strip():
        from utils.loader import load_from_github
        with st.spinner("Fetching from GitHub..."):
            df_loaded, stale_loaded = load_from_github(gh_url.strip())
        if df_loaded is not None and not df_loaded.empty:
            st.session_state["df"]           = df_loaded
            st.session_state["stale_df"]     = stale_loaded
            st.session_state["data_loaded"]  = True
            st.session_state["gh_url_saved"] = gh_url.strip()
            for k in FILTER_KEYS: st.session_state.pop(k, None)
            st.rerun()
        else:
            st.sidebar.error("❌ Failed — check URL")
    else:
        st.sidebar.warning("Paste your GitHub raw URL above")

# Connection status
if st.session_state.get("data_loaded"):
    _df  = st.session_state["df"]
    anch = _df["latest_nav_date"].max().strftime("%d %b %Y") if "latest_nav_date" in _df.columns else "—"
    amcs = _df["amc_name"].nunique() if "amc_name" in _df.columns else "—"
    st.sidebar.markdown(f"""
    <div style='background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;padding:10px 12px;margin:6px 0'>
        <div style='font-size:0.6rem;color:#15803D;font-weight:700;letter-spacing:0.8px'>● CONNECTED</div>
        <div style='color:#15803D;font-size:0.95rem;font-weight:700;margin-top:2px;font-family:DM Mono,monospace'>{_df.shape[0]:,} schemes</div>
        <div style='color:#64748B;font-size:0.67rem;margin-top:2px'>📅 {anch} &nbsp;·&nbsp; 🏦 {amcs} AMCs</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.sidebar.markdown("""
    <div style='background:#FFF1F2;border:1px solid #FECDD3;border-radius:8px;padding:10px 12px;margin:6px 0;text-align:center'>
        <div style='font-size:0.6rem;color:#DC2626;font-weight:700;letter-spacing:0.8px'>● NOT CONNECTED</div>
        <div style='color:#94A3B8;font-size:0.7rem;margin-top:2px'>Paste URL &amp; click Load</div>
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════
# GLOBAL FILTERS
# Hierarchy: Scheme Type → Asset Class → Sub-Type → AMC → Plan → Payout → Search
# Analysis grouping always uses Sub-Type (cat_level_3)
# ════════════════════════════════════════════════════
if st.session_state.get("data_loaded"):
    df_master = st.session_state["df"]

    st.sidebar.markdown("<hr style='border-color:#E2E8F0;margin:10px 0'>", unsafe_allow_html=True)
    st.sidebar.markdown("""
    <div style='font-size:0.62rem;color:#2563EB;letter-spacing:1.2px;font-weight:700;padding:0 4px 3px;text-transform:uppercase'>🎛️ Filters</div>
    <div style='font-size:0.67rem;color:#94A3B8;padding:0 4px 8px'>Applied to all pages</div>
    """, unsafe_allow_html=True)

    df_f = df_master.copy()

    # 1 — Scheme Type (Open Ended / Close Ended)
    c1_opts = sorted([c for c in df_f["cat_level_1"].dropna().unique() if c not in ("NA","","Unknown")])
    sel_c1  = st.sidebar.multiselect("🗂️ Scheme Type", c1_opts, key="gf_cat1", placeholder="Open Ended, Close Ended…")
    if sel_c1: df_f = df_f[df_f["cat_level_1"].isin(sel_c1)]

    # 2 — Asset Class (Equity / Debt / Hybrid)
    c2_opts = sorted([c for c in df_f["cat_level_2"].dropna().unique() if c not in ("NA","","Unknown")])
    sel_c2  = st.sidebar.multiselect("📂 Asset Class", c2_opts, key="gf_cat2", placeholder="Equity, Debt, Hybrid…")
    if sel_c2: df_f = df_f[df_f["cat_level_2"].isin(sel_c2)]

    # 3 — Sub-Type (Small Cap / Mid Cap / ELSS) — the primary analytics grouping
    c3_opts = sorted([c for c in df_f["cat_level_3"].dropna().unique() if c not in ("NA","","Unknown")])
    sel_c3  = st.sidebar.multiselect("📁 Sub-Type", c3_opts, key="gf_cat3", placeholder="Small Cap, Mid Cap, ELSS…")
    if sel_c3: df_f = df_f[df_f["cat_level_3"].isin(sel_c3)]

    # 4 — AMC
    amc_opts = sorted([c for c in df_f["amc_name"].dropna().unique() if c not in ("NA","","Unknown")])
    sel_amc  = st.sidebar.multiselect("🏦 AMC / Fund House", amc_opts, key="gf_amc", placeholder="HDFC, SBI, Nippon…")
    if sel_amc: df_f = df_f[df_f["amc_name"].isin(sel_amc)]

    # 5 — Plan Type
    plan_opts = sorted([c for c in df_f["plan_type"].dropna().unique() if c not in ("NA","")])
    sel_plan  = st.sidebar.multiselect("💳 Plan Type", plan_opts, key="gf_plan", placeholder="Direct / Regular")
    if sel_plan: df_f = df_f[df_f["plan_type"].isin(sel_plan)]

    # 6 — Payout Option
    opt_opts  = sorted([c for c in df_f["option_type"].dropna().unique() if c not in ("NA","")])
    sel_opt   = st.sidebar.multiselect("💰 Payout Option", opt_opts, key="gf_option", placeholder="Growth / IDCW / Bonus")
    if sel_opt: df_f = df_f[df_f["option_type"].isin(sel_opt)]

    # 7 — Scheme search
    search = st.sidebar.text_input("🔎 Scheme Search", key="gf_search", placeholder="Type scheme name…")
    if search: df_f = df_f[df_f["scheme_name"].str.contains(search, case=False, na=False)]

    if st.sidebar.button("↺ Reset Filters", use_container_width=True, key="reset_filters"):
        for k in FILTER_KEYS: st.session_state.pop(k, None)
        st.rerun()

    # Summary
    total_m = len(df_master); total_f = len(df_f)
    pct     = total_f / total_m * 100 if total_m > 0 else 0
    chips   = []
    if sel_c1:  chips.append(f"Type: {','.join(sel_c1[:1])}{'…' if len(sel_c1)>1 else ''}")
    if sel_c2:  chips.append(f"{','.join(sel_c2[:1])}{'…' if len(sel_c2)>1 else ''}")
    if sel_c3:  chips.append(f"{','.join(sel_c3[:2])}{'…' if len(sel_c3)>2 else ''}")
    if sel_amc: chips.append(f"{','.join(sel_amc[:1])}{'…' if len(sel_amc)>1 else ''}")
    if sel_plan: chips.append(','.join(sel_plan))
    if sel_opt:  chips.append(','.join(sel_opt))
    if search:   chips.append(f'"{search}"')

    chip_html = " · ".join([f"<b style='color:#1E40AF'>{c}</b>" for c in chips]) if chips else "<span style='color:#94A3B8'>No filters</span>"

    st.sidebar.markdown(f"""
    <div style='background:#EFF6FF;border:1px solid #BFDBFE;border-radius:8px;padding:10px 12px;margin-top:6px'>
        <div style='font-size:0.6rem;color:#2563EB;font-weight:700;letter-spacing:0.8px;margin-bottom:3px'>SHOWING</div>
        <div style='color:#0F172A;font-size:0.95rem;font-weight:700;font-family:DM Mono,monospace'>
            {total_f:,} <span style='color:#94A3B8;font-size:0.72rem;font-family:DM Sans,sans-serif'>/ {total_m:,} ({pct:.0f}%)</span>
        </div>
        <div style='margin-top:4px;font-size:0.67rem;line-height:1.5'>{chip_html}</div>
    </div>
    """, unsafe_allow_html=True)

    st.session_state["filtered_df"] = df_f

st.sidebar.markdown("<hr style='border-color:#E2E8F0;margin:10px 0'>", unsafe_allow_html=True)
st.sidebar.markdown("<div style='font-size:0.62rem;color:#CBD5E1;text-align:center;padding:4px'>v3.3 · Built for Rahul 🚀</div>", unsafe_allow_html=True)

page_file = os.path.join(base, pages[page])
load_page(page_file)
