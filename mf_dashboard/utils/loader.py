# utils/loader.py
import pandas as pd
import requests
import io
import re
import streamlit as st

RETURN_COLS = {
    "return_7d":    "1W",  "return_14d":   "2W",  "return_30d":   "1M",
    "return_90d":   "3M",  "return_180d":  "6M",  "return_365d":  "1Y",
    "return_730d":  "2Y",  "return_1095d": "3Y",  "cagr_3y":      "3Y CAGR",
}

_CAT_PATTERN = re.compile(r'^(.*?)\s*\(\s*(.*?)\s*\)$')
_PLAN_RE     = re.compile(r'\b(Direct|Regular)\b', re.IGNORECASE)
_OPTION_RE   = re.compile(r'\b(IDCW|Dividend|Bonus|Growth)\b', re.IGNORECASE)


def _split_category(cat_str) -> tuple:
    """
    Parse real AMFI scheme_category strings.

    AMFI format examples:
      'Open Ended Schemes (Equity Scheme - Small Cap Fund)'
      'Open Ended Schemes (Equity Scheme - ELSS)'
      'Open Ended Schemes (Debt Scheme - Liquid Fund)'
      'Open Ended Schemes (Hybrid Scheme - Balanced Hybrid Fund)'
      'Close Ended Schemes (Equity Scheme - ELSS)'
      'Interval Fund Schemes (Equity Scheme)'

    Returns:
      cat_level_1 = Open Ended Schemes / Close Ended Schemes / Interval Fund Schemes
      cat_level_2 = Equity Scheme / Debt Scheme / Hybrid Scheme / Solution Oriented Scheme
      cat_level_3 = Small Cap Fund / ELSS / Liquid Fund / Balanced Hybrid Fund etc.
    """
    if not cat_str or not isinstance(cat_str, str) or cat_str.strip() == "":
        return ("NA", "NA", "NA")

    cat_str = cat_str.strip()
    m = _CAT_PATTERN.match(cat_str)

    if not m:
        # No parentheses — entire string is level 1
        return (cat_str, "NA", "NA")

    level1 = m.group(1).strip()   # e.g. "Open Ended Schemes"
    inner  = m.group(2).strip()   # e.g. "Equity Scheme - Small Cap Fund"

    # Split inner on " - " to get asset class and sub-type
    parts  = [p.strip() for p in inner.split(" - ", 1)]  # max 1 split
    level2 = parts[0] if len(parts) > 0 else "NA"        # e.g. "Equity Scheme"
    level3 = parts[1] if len(parts) > 1 else "NA"        # e.g. "Small Cap Fund"

    return (level1, level2, level3)


def _detect_plan_type(name: str) -> str:
    m = _PLAN_RE.search(str(name))
    return m.group(1).capitalize() if m else "Regular"


def _detect_option_type(name: str, existing=None) -> str:
    if existing and str(existing).strip() not in ("", "nan", "NA", "None", "NaN"):
        v = str(existing).strip().lower()
        if "idcw" in v or "dividend" in v: return "IDCW"
        if "bonus" in v:                   return "Bonus"
        if "growth" in v:                  return "Growth"
    m = _OPTION_RE.search(str(name))
    if m:
        val = m.group(1).upper()
        return "IDCW" if val == "DIVIDEND" else val.capitalize()
    return "Growth"


def _enrich(df: pd.DataFrame) -> pd.DataFrame:
    if "latest_nav_date" in df.columns:
        df["latest_nav_date"] = pd.to_datetime(df["latest_nav_date"], errors="coerce")

    for col in RETURN_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # ── Category levels ──
    # Always (re)parse from scheme_category if available — most reliable source
    if "scheme_category" in df.columns:
        parsed = df["scheme_category"].apply(
            lambda x: pd.Series(_split_category(x),
                                  index=["cat_level_1", "cat_level_2", "cat_level_3"])
        )
        df["cat_level_1"] = parsed["cat_level_1"]
        df["cat_level_2"] = parsed["cat_level_2"]
        df["cat_level_3"] = parsed["cat_level_3"]
    else:
        # Fallback: use existing columns if present, else NA
        for lvl in ["cat_level_1", "cat_level_2", "cat_level_3"]:
            if lvl not in df.columns:
                df[lvl] = "NA"
            else:
                df[lvl] = df[lvl].fillna("NA")

    # ── Plan Type ──
    if "plan_type" not in df.columns:
        if "scheme_name" in df.columns:
            df["plan_type"] = df["scheme_name"].apply(_detect_plan_type)
        else:
            df["plan_type"] = "Regular"

    # ── Option / Payout Type ──
    if "scheme_name" in df.columns:
        existing = df["option_type"] if "option_type" in df.columns else pd.Series([None]*len(df))
        df["option_type"] = [
            _detect_option_type(name, ex)
            for name, ex in zip(df["scheme_name"], existing)
        ]
    elif "option_type" not in df.columns:
        df["option_type"] = "Growth"

    if "amc_name" not in df.columns:
        df["amc_name"] = "Unknown"

    # ── 3Y CAGR ──
    if "cagr_3y" not in df.columns and "return_1095d" in df.columns:
        df["cagr_3y"] = ((1 + df["return_1095d"] / 100) ** (1 / 3) - 1) * 100

    return df


def load_excel(file) -> tuple[pd.DataFrame, pd.DataFrame]:
    xl       = pd.ExcelFile(file)
    df       = pd.read_excel(xl, sheet_name="Active_Analytics")
    df       = _enrich(df)
    stale_df = pd.DataFrame()
    if "Full_Audit_Trail" in xl.sheet_names:
        audit    = pd.read_excel(xl, sheet_name="Full_Audit_Trail")
        if "status" in audit.columns:
            stale_df = audit[audit["status"] != "Active"].copy()
    return df, stale_df


@st.cache_data(ttl=1800, show_spinner=False)
def load_from_github(url: str) -> tuple[pd.DataFrame | None, pd.DataFrame]:
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return load_excel(io.BytesIO(resp.content))
    except Exception as e:
        st.error(f"GitHub load failed: {e}")
        return None, pd.DataFrame()
