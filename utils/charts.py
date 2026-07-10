import streamlit as st
"""
Chart Generation Utility Functions
====================================
Plotly chart factory for interactive data visualizations.
All charts use a consistent, premium color palette and modern styling.
Compatible with Plotly 6.x.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional, List

# =============================================================================

def _get_theme_styles():
    try:
        theme = st.session_state.get("theme", "dark")
    except Exception:
        theme = "dark"
    if theme == "dark":
        return {
            "text_title": "#FFFFFF",
            "text_body": "#94A3B8",
            "text_muted": "#64748B",
            "plot_bg": "#161525",
            "grid_color": "#252438",
            "border_color": "#252438",
            "legend_bg": "rgba(22, 21, 37, 0.85)"
        }
    else:
        return {
            "text_title": "#0F172A",
            "text_body": "#475569",
            "text_muted": "#64748B",
            "plot_bg": "#FAF9FD",
            "grid_color": "#E2E8F0",
            "border_color": "#E2E8F0",
            "legend_bg": "rgba(255, 255, 255, 0.85)"
        }

# Shared theme / color constants
# =============================================================================

COLOR_PALETTE = [
    "#6366F1",  # indigo
    "#10B981",  # emerald
    "#F59E0B",  # amber
    "#EF4444",  # red
    "#8B5CF6",  # violet
    "#EC4899",  # pink
    "#06B6D4",  # cyan
    "#F97316",  # orange
    "#14B8A6",  # teal
    "#3B82F6",  # blue
]

GRADIENT_BLUE = ["#818CF8", "#6366F1", "#4F46E5", "#4338CA", "#3730A3"]
GRADIENT_GREEN = ["#6EE7B7", "#34D399", "#10B981", "#059669", "#047857"]

LAYOUT_DEFAULTS = dict(
    font=dict(family="Inter, sans-serif", size=13, color="#334155"),
    plot_bgcolor="#FAFBFD",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=55, r=40, t=75, b=55),
    hoverlabel=dict(
        bgcolor="#1E293B",
        font_size=13,
        font_family="Inter, sans-serif",
        font_color="#F8FAFC",
    ),
    colorway=COLOR_PALETTE,
)


def _apply_layout(fig, title: str = "", height: int = 460, show_legend: bool = True):
    """Apply premium consistent styling to a Plotly figure."""
    styles = _get_theme_styles()
    
    layout_args = dict(
        font=dict(family="Inter, sans-serif", size=13, color=styles["text_body"]),
        plot_bgcolor=styles["plot_bg"],
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=55, r=40, t=75, b=55),
        hoverlabel=dict(
            bgcolor="#1E293B" if styles["plot_bg"] != "#161525" else "#252438",
            font_size=13,
            font_family="Inter, sans-serif",
            font_color="#F8FAFC",
        ),
        colorway=COLOR_PALETTE,
    )
    
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>",
            font=dict(size=17, color=styles["text_title"]),
            x=0.02,
            y=0.97,
        ),
        height=height,
        showlegend=show_legend,
        legend=dict(
            bgcolor=styles["legend_bg"],
            bordercolor=styles["border_color"],
            borderwidth=1,
            font=dict(size=12, color=styles["text_body"]),
        ),
        **layout_args,
    )
    fig.update_xaxes(
        gridcolor=styles["grid_color"],
        gridwidth=1,
        zerolinecolor=styles["border_color"],
        zerolinewidth=1.5,
        tickfont=dict(color=styles["text_muted"], size=11),
        title_font=dict(size=13, color=styles["text_body"], family="Inter, sans-serif"),
    )
    fig.update_yaxes(
        gridcolor=styles["grid_color"],
        gridwidth=1,
        zerolinecolor=styles["border_color"],
        zerolinewidth=1.5,
        tickfont=dict(color=styles["text_muted"], size=11),
        title_font=dict(size=13, color=styles["text_body"], family="Inter, sans-serif"),
    )
    return fig


# =============================================================================
# Missing Value Charts
# =============================================================================

def missing_value_bar(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of missing values per column."""
    missing = df.isnull().sum()
    missing = missing[missing > 0].sort_values(ascending=True)

    if missing.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="✅  No missing values found — dataset is complete!",
            showarrow=False,
            font=dict(size=16, color="#10B981", family="Inter"),
        )
        return _apply_layout(fig, "Missing Values by Column", 300, show_legend=False)

    # Color bars by severity
    colors = []
    for v in missing.values:
        pct = v / len(df)
        if pct < 0.05:
            colors.append("#6366F1")
        elif pct < 0.15:
            colors.append("#F59E0B")
        else:
            colors.append("#EF4444")

    fig = go.Figure(
        go.Bar(
            x=missing.values,
            y=missing.index,
            orientation="h",
            marker=dict(color=colors, line=dict(color="rgba(0,0,0,0.08)", width=1)),
            text=[f"  {v}  ({v / len(df) * 100:.1f}%)" for v in missing.values],
            textposition="outside",
            textfont=dict(color=_get_theme_styles()["text_body"], size=12),
            hovertemplate="<b>%{y}</b><br>Missing: %{x} values<extra></extra>",
        )
    )
    return _apply_layout(
        fig,
        "Missing Values by Column",
        max(350, len(missing) * 42 + 110),
        show_legend=False,
    )


def missing_value_heatmap(df: pd.DataFrame) -> go.Figure:
    """Binary heatmap showing null pattern (sampled to max 200 rows)."""
    sample = df.head(200) if len(df) > 200 else df
    null_matrix = sample.isnull().astype(int)

    fig = go.Figure(
        go.Heatmap(
            z=null_matrix.values,
            x=null_matrix.columns.tolist(),
            y=list(range(len(null_matrix))),
            colorscale=[[0, _get_theme_styles()["plot_bg"]], [1, "#EF4444"]],
            showscale=True,
            xgap=2,
            ygap=0.5,
            colorbar=dict(
                title=dict(text="Status"),
                tickvals=[0, 1],
                ticktext=["Present", "Missing"],
                thickness=14,
                len=0.6,
                outlinewidth=0,
            ),
            hovertemplate="Row %{y} · <b>%{x}</b><br>%{z}<extra></extra>",
        )
    )
    fig = _apply_layout(
        fig, "Missing Value Pattern (first 200 rows)", 460, show_legend=False
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=False, zeroline=False, autorange="reversed")
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)")
    return fig


# =============================================================================
# Distribution Charts
# =============================================================================

def histogram(df: pd.DataFrame, column: str, bins: int = 30) -> go.Figure:
    """Histogram with marginal box plot for a numeric column."""
    data = df[column].dropna()

    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.18, 0.82],
        shared_xaxes=True,
        vertical_spacing=0.03,
    )

    # Box plot on top
    fig.add_trace(
        go.Box(
            x=data,
            marker_color=COLOR_PALETTE[0],
            line=dict(color=COLOR_PALETTE[0], width=2),
            fillcolor="rgba(99,102,241,0.2)",
            name="",
            showlegend=False,
            boxmean=True,
        ),
        row=1, col=1,
    )

    # Histogram below
    fig.add_trace(
        go.Histogram(
            x=data,
            nbinsx=bins,
            marker=dict(
                color=COLOR_PALETTE[0],
                line=dict(color="rgba(255,255,255,0.6)", width=1),
            ),
            opacity=0.88,
            name="Count",
            showlegend=False,
            hovertemplate="Range: %{x}<br>Count: %{y}<extra></extra>",
        ),
        row=2, col=1,
    )

    fig.update_xaxes(title_text=column, row=2, col=1)
    fig.update_yaxes(title_text="Frequency", row=2, col=1)
    fig.update_yaxes(showticklabels=False, showgrid=False, row=1, col=1)

    return _apply_layout(fig, f"Distribution of {column}", 480, show_legend=False)


def distribution_plot(df: pd.DataFrame, column: str) -> go.Figure:
    """KDE-style distribution plot for a numeric column."""
    data = df[column].dropna()
    fig = go.Figure()

    # Histogram
    fig.add_trace(
        go.Histogram(
            x=data,
            nbinsx=40,
            name="Histogram",
            marker=dict(
                color="rgba(99,102,241,0.35)",
                line=dict(color="rgba(99,102,241,0.5)", width=1),
            ),
            histnorm="probability density",
        )
    )

    # KDE curve
    if len(data) > 2:
        try:
            from scipy.stats import gaussian_kde

            kde = gaussian_kde(data)
            x_range = np.linspace(data.min(), data.max(), 200)
            kde_y = kde(x_range)
            fig.add_trace(
                go.Scatter(
                    x=x_range,
                    y=kde_y,
                    mode="lines",
                    name="Density (KDE)",
                    line=dict(color="#EF4444", width=3, shape="spline"),
                    fill="tozeroy",
                    fillcolor="rgba(239,68,68,0.1)",
                )
            )
        except Exception:
            pass

    fig.update_layout(barmode="overlay")
    return _apply_layout(fig, f"Density Distribution — {column}")


def box_plot(
    df: pd.DataFrame, column: str, group_by: Optional[str] = None
) -> go.Figure:
    """Box plot for a numeric column, optionally grouped."""
    if group_by and group_by in df.columns:
        fig = px.box(
            df,
            x=group_by,
            y=column,
            color=group_by,
            color_discrete_sequence=COLOR_PALETTE,
            points="outliers",
        )
    else:
        fig = px.box(
            df,
            y=column,
            color_discrete_sequence=[COLOR_PALETTE[0]],
            points="outliers",
        )

    fig.update_traces(boxmean=True, line=dict(width=2))
    return _apply_layout(fig, f"Box Plot — {column}", show_legend=bool(group_by))


# =============================================================================
# Categorical Charts
# =============================================================================

def bar_chart(df: pd.DataFrame, column: str, top_n: int = 15) -> go.Figure:
    """Bar chart of value counts for a categorical column."""
    counts = df[column].value_counts().head(top_n)
    n = len(counts)

    fig = go.Figure(
        go.Bar(
            x=counts.index.astype(str),
            y=counts.values,
            marker=dict(
                color=COLOR_PALETTE[:n] if n <= len(COLOR_PALETTE) else (COLOR_PALETTE * 3)[:n],
                line=dict(color="rgba(0,0,0,0.08)", width=1),
            ),
            text=counts.values,
            textposition="outside",
            textfont=dict(color=_get_theme_styles()["text_body"], size=12),
            hovertemplate="<b>%{x}</b><br>Count: %{y}<extra></extra>",
        )
    )
    return _apply_layout(fig, f"Value Counts — {column}", show_legend=False)


def pie_chart(df: pd.DataFrame, column: str, top_n: int = 10) -> go.Figure:
    """Donut chart of value distribution for a categorical column."""
    counts = df[column].value_counts().head(top_n)
    n = len(counts)
    colors = COLOR_PALETTE[:n] if n <= len(COLOR_PALETTE) else (COLOR_PALETTE * 3)[:n]

    fig = go.Figure(
        go.Pie(
            labels=counts.index.astype(str),
            values=counts.values,
            hole=0.52,
            marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2.5)),
            textinfo="percent+label",
            textposition="inside",
            insidetextorientation="radial",
            textfont=dict(size=11, color="#FFFFFF"),
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>",
        )
    )
    return _apply_layout(fig, f"Distribution — {column}")


# =============================================================================
# Correlation Charts
# =============================================================================

def correlation_heatmap(df: pd.DataFrame) -> go.Figure:
    """Interactive correlation heatmap for numeric columns."""
    numeric_df = df.select_dtypes(include=["number"])
    if numeric_df.shape[1] < 2:
        fig = go.Figure()
        fig.add_annotation(
            text="Need at least 2 numeric columns for correlation analysis.",
            showarrow=False,
            font=dict(size=14, color="#64748B"),
        )
        return _apply_layout(fig, "Correlation Heatmap", 300, show_legend=False)

    corr = numeric_df.corr().round(3)

    # Custom divergent colorscale: blue → white → red
    styles = _get_theme_styles()
    custom_scale = [
        [0.0, "#3730A3"],
        [0.25, "#818CF8"],
        [0.5, styles["plot_bg"]],
        [0.75, "#FCA5A5"],
        [1.0, "#B91C1C"],
    ]

    fig = go.Figure(
        go.Heatmap(
            z=corr.values,
            x=corr.columns.tolist(),
            y=corr.columns.tolist(),
            colorscale=custom_scale,
            zmin=-1,
            zmax=1,
            text=corr.values.round(2),
            texttemplate="%{text}",
            textfont=dict(size=13, color=_get_theme_styles()["text_title"]),
            xgap=3,
            ygap=3,
            hovertemplate="<b>%{x}</b> vs <b>%{y}</b><br>r = %{z:.3f}<extra></extra>",
            colorbar=dict(
                title=dict(text="r", font=dict(size=13)),
                thickness=14,
                len=0.75,
                outlinewidth=0,
            ),
        )
    )
    size = max(480, corr.shape[0] * 70 + 120)
    fig = _apply_layout(fig, "Feature Correlation Matrix", size, show_legend=False)
    fig.update_xaxes(showgrid=False, zeroline=False, tickangle=45)
    fig.update_yaxes(showgrid=False, zeroline=False)
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)")
    return fig


# =============================================================================
# Scatter Plot
# =============================================================================

def scatter_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: Optional[str] = None,
) -> go.Figure:
    """Scatter plot of two numeric columns with optional color grouping."""
    kwargs = dict(
        x=x_col,
        y=y_col,
        color_discrete_sequence=COLOR_PALETTE,
        opacity=0.72,
    )
    if color_col and color_col in df.columns:
        kwargs["color"] = color_col

    fig = px.scatter(df, **kwargs, trendline="ols")

    # Style the markers
    fig.update_traces(
        marker=dict(size=8, line=dict(width=0.8, color="rgba(0,0,0,0.25)")),
        selector=dict(mode="markers"),
    )
    # Style the trendline
    fig.update_traces(
        line=dict(dash="dash", width=2, color="#EF4444"),
        selector=dict(mode="lines"),
    )

    return _apply_layout(fig, f"{x_col} vs {y_col}", height=520)


# =============================================================================
# Multi-Column Overview
# =============================================================================

def numeric_overview(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    max_cols: int = 6,
) -> go.Figure:
    """Grid of mini histograms for multiple numeric columns."""
    if columns is None:
        columns = df.select_dtypes(include=["number"]).columns.tolist()
    columns = columns[:max_cols]

    if not columns:
        fig = go.Figure()
        fig.add_annotation(text="No numeric columns available.", showarrow=False)
        return _apply_layout(fig, "Numeric Overview", 300, show_legend=False)

    n_cols_grid = min(3, len(columns))
    n_rows = (len(columns) + n_cols_grid - 1) // n_cols_grid

    fig = make_subplots(
        rows=n_rows,
        cols=n_cols_grid,
        subplot_titles=[f"<b>{c}</b>" for c in columns],
        vertical_spacing=0.14,
        horizontal_spacing=0.07,
    )

    for i, col in enumerate(columns):
        r = i // n_cols_grid + 1
        c = i % n_cols_grid + 1
        color = COLOR_PALETTE[i % len(COLOR_PALETTE)]
        fig.add_trace(
            go.Histogram(
                x=df[col].dropna(),
                nbinsx=28,
                marker=dict(
                    color=color,
                    line=dict(color="rgba(255,255,255,0.5)", width=1),
                ),
                opacity=0.85,
                name=col,
                showlegend=False,
                hovertemplate=f"<b>{col}</b><br>" + "Range: %{x}<br>Count: %{y}<extra></extra>",
            ),
            row=r,
            col=c,
        )

    fig = _apply_layout(
        fig,
        "Dataset Numeric Overview",
        n_rows * 280 + 100,
        show_legend=False,
    )

    # Subtle grids in subplots using theme styles
    _styles = _get_theme_styles()
    fig.update_xaxes(showgrid=True, gridcolor=_styles["grid_color"], zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor=_styles["grid_color"], zeroline=False)

    # Style subplot titles
    for annotation in fig["layout"]["annotations"]:
        annotation["font"] = dict(size=14, color=_get_theme_styles()["text_title"])

    return fig
