# utils/filters.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

# ── Light professional theme — Bloomberg daylight ──────────────────────────────
C = {
    "bg":       "#F8FAFC",   "card":     "#FFFFFF",   "border":   "#E2E8F0",
    "blue":     "#2563EB",   "blue2":    "#3B82F6",   "cyan":     "#0EA5E9",
    "green":    "#16A34A",   "red":      "#DC2626",   "amber":    "#D97706",
    "slate":    "#64748B",   "slate2":   "#94A3B8",   "text":     "#0F172A",
    "subtext":  "#475569",   "muted":    "#94A3B8",   "accent":   "#1E40AF",
}

PLOTLY_THEME = dict(
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#F8FAFC",
    font=dict(family="DM Sans, sans-serif", color="#475569", size=12),
    xaxis=dict(gridcolor="#E2E8F0", zeroline=False, linecolor="#CBD5E1",
               tickfont=dict(color="#64748B", size=11)),
    yaxis=dict(gridcolor="#E2E8F0", zeroline=False, linecolor="#CBD5E1",
               tickfont=dict(color="#64748B", size=11)),
    margin=dict(l=40, r=20, t=50, b=40),
)


def plot_layout(**overrides) -> dict:
    base = {k: (dict(v) if isinstance(v, dict) else v) for k, v in PLOTLY_THEME.items()}
    for axis in ("xaxis", "yaxis", "margin", "font", "legend"):
        if axis in overrides and axis in base:
            merged = dict(base[axis])
            merged.update(overrides.pop(axis))
            overrides[axis] = merged
    base.update(overrides)
    return base


# ── Helpers ────────────────────────────────────────────────────────────────────
def fmt_ret(val, suffix="%"):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "—"
    sign = "+" if val >= 0 else ""
    cls  = "ret-pos" if val >= 0 else "ret-neg"
    return f'<span class="{cls}">{sign}{val:.2f}{suffix}</span>'


def color_ret(val):
    if pd.isna(val):  return "color: #94A3B8"
    if val > 0:       return "color: #16A34A; font-weight:600"
    if val < 0:       return "color: #DC2626; font-weight:600"
    return "color: #64748B"


def style_returns_df(df: pd.DataFrame, ret_cols: list):
    fmt = {c: "{:+.2f}%" for c in ret_cols if c in df.columns}
    return (
        df.style
          .format(fmt, na_rep="—")
          .applymap(color_ret, subset=[c for c in ret_cols if c in df.columns])
          .set_properties(**{
              "background-color": "#FFFFFF",
              "color": "#0F172A",
              "border": "1px solid #E2E8F0",
              "font-family": "DM Mono, monospace",
              "font-size": "12px",
              "padding": "6px 10px",
          })
          .set_table_styles([{
              "selector": "th",
              "props": [("background-color","#F1F5F9"),("color","#475569"),
                        ("font-size","11px"),("border","1px solid #E2E8F0"),
                        ("padding","8px 12px"),("font-weight","600"),
                        ("text-transform","uppercase"),("letter-spacing","0.5px")],
          }])
    )


# ── The canonical analysis grouping level for MF analytics ─────────────────────
# cat_level_1 = Open Ended / Close Ended  (scheme structure — filter use only)
# cat_level_2 = Equity / Debt / Hybrid    (asset class — primary analysis grouping)
# cat_level_3 = Small Cap / Mid Cap / ELSS etc. (sub-type — THE key analytics level)
# We group by cat_level_3 (sub-type) for all charts — it's the meaningful peer group.
# cat_level_2 is the header/context. Nothing below cat_level_3 is shown.

def get_group_col(df: pd.DataFrame) -> str:
    """Return the best column to group by — always cat_level_3 if populated, else cat_level_2."""
    for lvl in ("cat_level_3", "cat_level_2"):
        if lvl in df.columns:
            valid = df[lvl].replace({"NA": pd.NA, "": pd.NA, "Unknown": pd.NA}).dropna()
            if valid.nunique() >= 1:
                return lvl
    return "cat_level_2"


# ── Charts ─────────────────────────────────────────────────────────────────────
def heatmap_category_returns(df: pd.DataFrame, ret_cols: dict,
                              group_col: str = None) -> go.Figure:
    present  = {k: v for k, v in ret_cols.items() if k in df.columns}
    if not group_col:
        group_col = get_group_col(df)

    if not present or group_col not in df.columns:
        return go.Figure()

    pivot = (
        df[~df[group_col].isin(("NA", "", "Unknown", None))]
        .groupby(group_col)[list(present.keys())]
        .median()
        .rename(columns=present)
        .dropna(how="all")
        .sort_index()
    )
    if pivot.empty:
        return go.Figure()

    text_vals = [
        [f"{v:+.1f}%" if not np.isnan(v) else "—" for v in row]
        for row in pivot.values
    ]

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[[0,"#FEE2E2"],[0.45,"#F1F5F9"],[1,"#DCFCE7"]],
        zmid=0,
        text=text_vals,
        texttemplate="%{text}",
        textfont=dict(size=11, family="DM Mono, monospace", color="#0F172A"),
        showscale=True,
        colorbar=dict(
            tickfont=dict(color="#64748B"),
            outlinecolor="#E2E8F0",
            title=dict(text="%", font=dict(color="#64748B")),
            bgcolor="#FFFFFF",
        ),
        hovertemplate="<b>%{y}</b><br>%{x}: %{text}<extra></extra>",
    ))
    fig.update_layout(**plot_layout(
        title=f"Median Returns by Sub-Type (%) — {len(pivot)} categories",
        height=max(380, 44 * len(pivot)),
        yaxis=dict(autorange="reversed"),
        margin=dict(l=220, r=80, t=60, b=40),
    ))
    return fig


def bar_top_bottom(df: pd.DataFrame, col: str, label: str, n: int = 15) -> go.Figure:
    sub      = df.dropna(subset=[col]).copy().sort_values(col)
    bottom   = sub.head(n)
    top      = sub.tail(n).iloc[::-1]
    combined = pd.concat([top, bottom])
    colors   = [C["green"] if v >= 0 else C["red"] for v in combined[col]]

    fig = go.Figure(go.Bar(
        x=combined[col],
        y=combined["scheme_name"].str[:50],
        orientation="h",
        marker_color=colors,
        marker_line_width=0,
        text=[f"{v:+.1f}%" for v in combined[col]],
        textposition="outside",
        textfont=dict(family="DM Mono, monospace", size=10, color="#475569"),
    ))
    fig.update_layout(**plot_layout(
        title=f"Top & Bottom {n} Schemes — {label}",
        height=max(500, 22 * len(combined)),
        yaxis=dict(autorange="reversed"),
    ))
    return fig


def waterfall_returns(scheme_row: pd.Series, ret_map: dict) -> go.Figure:
    labels, values = [], []
    for col, label in ret_map.items():
        if col in scheme_row and not pd.isna(scheme_row[col]):
            labels.append(label)
            values.append(float(scheme_row[col]))

    colors = [C["green"] if v >= 0 else C["red"] for v in values]
    fig = go.Figure(go.Bar(
        x=labels, y=values,
        marker_color=colors,
        marker_line_width=0,
        text=[f"{v:+.2f}%" for v in values],
        textposition="outside",
        textfont=dict(family="DM Mono, monospace", size=11, color="#475569"),
    ))
    fig.add_hline(y=0, line_color="#E2E8F0", line_width=1)
    fig.update_layout(**plot_layout(title="Returns Across All Periods", height=340))
    return fig


def category_comparison_bar(df: pd.DataFrame, col: str, label: str) -> go.Figure:
    """Avg + Median bar by sub-type — key analytics chart."""
    grp = get_group_col(df)
    if grp not in df.columns or col not in df.columns:
        return go.Figure()
    cat_avg = (
        df[~df[grp].isin(("NA","","Unknown"))]
        .groupby(grp)[col]
        .agg(["mean","median","count","std"])
        .rename(columns={"mean":"Avg","median":"Median","count":"N","std":"Std"})
        .sort_values("Avg", ascending=False).reset_index()
    )
    if cat_avg.empty:
        return go.Figure()

    colors = [C["blue"] if v >= 0 else C["red"] for v in cat_avg["Avg"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=cat_avg[grp], y=cat_avg["Avg"], name="Avg Return",
        marker_color=colors, marker_line_width=0,
        text=[f"{v:+.1f}%" for v in cat_avg["Avg"]],
        textposition="outside",
        error_y=dict(type="data", array=cat_avg["Std"].fillna(0), visible=True,
                     color="#CBD5E1", thickness=1.5, width=4),
        customdata=cat_avg["N"],
        hovertemplate="<b>%{x}</b><br>Avg: %{y:+.1f}%<br>Schemes: %{customdata}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=cat_avg[grp], y=cat_avg["Median"], mode="markers", name="Median",
        marker=dict(color=C["amber"], size=9, symbol="diamond",
                    line=dict(width=1, color="#FFFFFF")),
        hovertemplate="<b>%{x}</b><br>Median: %{y:+.1f}%<extra></extra>",
    ))
    fig.update_layout(**plot_layout(
        title=f"Sub-Type Performance — {label} (error bars = std dev)",
        height=400, xaxis=dict(tickangle=-30),
        legend=dict(font=dict(color="#475569"), bgcolor="rgba(255,255,255,0.9)",
                    bordercolor="#E2E8F0", borderwidth=1),
    ))
    return fig
