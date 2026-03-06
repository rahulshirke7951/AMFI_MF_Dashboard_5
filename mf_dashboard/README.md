# 📊 MF Intelligence Dashboard

Institutional-grade Mutual Fund analytics · Streamlit · Dark theme

---

## 🏗️ Project Structure

```
mf_dashboard/
├── app.py                        # Main entry point + sidebar navigation
├── requirements.txt
├── utils/
│   ├── loader.py                 # Excel + GitHub data loading
│   └── filters.py                # Shared filters, charts, styling
├── pages/
│   ├── 1_overview.py             # Market overview + heatmap + AMC leaderboard
│   ├── 2_short_term.py           # 1W / 2W / 1M / 3M / 6M returns
│   ├── 3_long_term.py            # 1Y / 2Y / 3Y / CAGR returns
│   ├── 4_screener.py             # Advanced screener + scheme deep dive
│   ├── 5_watchlist.py            # Multiple watchlists via JSON
│   └── 6_audit.py                # Data freshness + stale schemes
└── watchlists/
    └── sample_watchlist.json     # Reference JSON format
```

---

## 🚀 Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## ☁️ Deploy on Streamlit Cloud

1. Push this folder to a GitHub repo
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. New app → select repo → Main file: `app.py`
4. Deploy 🚀

---

## 📂 Data Sources

### Option A — Upload Excel
- Upload `output/dashboard_data.xlsx` directly in the sidebar
- Auto-reads `Active_Analytics` and `Full_Audit_Trail` sheets

### Option B — GitHub URL
- Paste raw URL to your `dashboard_data.xlsx` in the sidebar
- Example: `https://raw.githubusercontent.com/rahulshirke7951/mf-data-pipeline/main/output/dashboard_data.xlsx`
- Cached for 30 minutes per session

---

## ⭐ Watchlist JSON Format

Create a JSON file and upload it (or host on GitHub):

```json
{
  "Core Portfolio": {
    "description": "Long-term wealth creation",
    "scheme_codes": ["119551", "120503", "118834"]
  },
  "Momentum Picks": {
    "description": "High recent momentum",
    "scheme_codes": ["125354", "130503"]
  }
}
```

- `scheme_codes` must match the `scheme_code` column in your NAV database
- You can have **unlimited named watchlists** in one JSON file
- Host on GitHub and load via URL for auto-refresh

---

## ➕ Add 1W / 2W Returns to Pipeline

Add `7` and `14` to your `config.json`:

```json
{
  "return_periods_days": [7, 14, 30, 90, 180, 365, 730, 1095],
  ...
}
```

The dashboard auto-detects which return columns are present.

---

## 📊 Pages Summary

| Page | What it shows |
|------|--------------|
| 🏠 Overview | KPIs, category heatmap, AMC leaderboard |
| 📈 Short-Term | 1W/2W/1M/3M/6M · top/bottom · breadth · heatmap |
| 📊 Long-Term | 1Y/2Y/3Y/CAGR · distribution · category comparison |
| 🔍 Screener | Filter + threshold + per-scheme deep dive + peer rank |
| ⭐ Watchlists | JSON watchlists · multi-period compare · scheme detail |
| 📋 Audit | NAV date distribution · stale schemes · data health |
