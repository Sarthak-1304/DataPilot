"""
Dashboard Page
==============
Home page displaying key metrics, data quality overview, column breakdown,
recommendations, sample preview, and recent activity.
"""

import streamlit as st
import pandas as pd
import numpy as np
from utils.cleaner import calculate_quality_score


def _score_color(score: int) -> str:
    if score >= 80:
        return "#10B981"
    elif score >= 50:
        return "#F59E0B"
    return "#EF4444"


def _format_bytes(size_bytes) -> str:
    if size_bytes is None:
        return "—"
    for unit in ["B", "KB", "MB", "GB"]:
        if abs(size_bytes) < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


# ─────────────────────────────────────────────────────────────────────
# No-dataset welcome screen
# ─────────────────────────────────────────────────────────────────────

def _render_welcome():
    """Attractive landing page when no dataset is loaded."""
    st.markdown(
        """
        <div class="top-header">
            <h2>🏠 Welcome to Data Pilot</h2>
            <p>Upload a dataset to unlock powerful analysis, cleaning, and reporting tools.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Feature cards
    features = [
        ("📊", "Data Analysis",
         "Interactive histograms, scatter plots, box plots, correlation heatmaps, and more."),
        ("🧹", "Smart Cleaning",
         "One-click missing-value imputation, deduplication, outlier removal, and type conversion."),
        ("🔄", "Before vs After",
         "Side-by-side comparison showing the exact impact of every cleaning step you apply."),
        ("📄", "Export & Reports",
         "Download your cleaned data as CSV/Excel and generate a professional PDF summary."),
    ]

    cols = st.columns(len(features))
    for col, (icon, title, desc) in zip(cols, features):
        with col:
            st.markdown(
                f"""
                <div class="metric-card" style="text-align:center; min-height:180px;">
                    <div style="font-size:2.2rem; margin-bottom:0.5rem;">{icon}</div>
                    <div style="font-weight:700; font-size:1rem; margin-bottom:0.4rem;
                                color:var(--text-primary);">{title}</div>
                    <div style="font-size:0.82rem; color:var(--text-secondary);
                                line-height:1.55;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("")  # spacer

    # Call to action
    st.markdown(
        """
        <div class="content-card" style="text-align:center; padding:2.5rem 1.5rem;">
            <div style="font-size:3rem; margin-bottom:0.6rem; opacity:0.6;">📂</div>
            <h3 style="border:none; padding:0; margin-bottom:0.4rem;">Get Started</h3>
            <p style="color:var(--text-secondary); font-size:0.9rem; max-width:420px;
                      margin:0 auto 1rem auto; line-height:1.6;">
                Head over to <b>Upload Dataset</b> in the sidebar to load a CSV or Excel file.
                Your dashboard will come alive with metrics, quality insights, and recommendations.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────
# Dataset-loaded dashboard
# ─────────────────────────────────────────────────────────────────────

def _render_loaded_dashboard():
    """Full dashboard with metrics, quality score, breakdown, and preview."""
    df: pd.DataFrame = st.session_state["original_df"]
    cleaned_df = st.session_state.get("cleaned_df")
    working_df = cleaned_df if cleaned_df is not None else df
    file_name = st.session_state.get("file_name", "Dataset")

    # ── Header ──
    st.markdown(
        f"""
        <div class="top-header">
            <h2>🏠 Dashboard</h2>
            <p>Overview for <strong>{file_name}</strong> — your data at a glance.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Metric cards row ──
    total_rows = working_df.shape[0]
    total_cols = working_df.shape[1]
    missing_cells = int(working_df.isnull().sum().sum())
    total_cells = total_rows * total_cols
    missing_pct = (missing_cells / total_cells * 100) if total_cells else 0
    duplicates = int(working_df.duplicated().sum())
    mem_bytes = working_df.memory_usage(deep=True).sum()
    score = calculate_quality_score(working_df)["total"]

    m1, m2, m3, m4, m5 = st.columns(5)

    def _card(col, icon, value, label, accent):
        with col:
            st.markdown(
                f"""
                <div class="metric-card {accent}">
                    <div class="metric-icon">{icon}</div>
                    <div class="metric-value">{value}</div>
                    <div class="metric-label">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    _card(m1, "📋", f"{total_rows:,}", "Rows", "blue")
    _card(m2, "📐", f"{total_cols}", "Columns", "purple")
    _card(m3, "⚠️", f"{missing_cells:,}", f"Missing ({missing_pct:.1f}%)", "orange")
    _card(m4, "🔁", f"{duplicates:,}", "Duplicate Rows", "red")
    _card(m5, "💾", _format_bytes(mem_bytes), "Memory", "green")

    st.markdown("")  # spacer

    # ── Quality score + Column breakdown ──
    left_col, right_col = st.columns([1, 2])

    with left_col:
        color = _score_color(score)
        st.markdown(
            f"""
            <div class="content-card">
                <h3>🎯 Data Quality Score</h3>
                <div class="quality-score-container">
                    <div class="quality-score-value" style="color:{color};">{score}</div>
                    <div class="quality-score-label">out of 100</div>
                    <div class="quality-bar">
                        <div class="quality-bar-fill"
                             style="width:{score}%; background:linear-gradient(90deg,{color},
                                    {color}dd);"></div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right_col:
        # Column type breakdown
        numeric_count = len(working_df.select_dtypes(include="number").columns)
        cat_count = len(working_df.select_dtypes(include=["object", "category"]).columns)
        datetime_count = len(working_df.select_dtypes(include="datetime").columns)
        bool_count = len(working_df.select_dtypes(include="bool").columns)
        other_count = total_cols - numeric_count - cat_count - datetime_count - bool_count

        st.markdown(
            """
            <div class="content-card">
                <h3>🧬 Column Type Breakdown</h3>
            """,
            unsafe_allow_html=True,
        )

        breakdown_data = [
            ("Numeric", numeric_count, "#3B82F6"),
            ("Categorical / Text", cat_count, "#8B5CF6"),
            ("Datetime", datetime_count, "#F59E0B"),
            ("Boolean", bool_count, "#10B981"),
        ]
        if other_count > 0:
            breakdown_data.append(("Other", other_count, "#64748B"))

        for label, count, bar_color in breakdown_data:
            pct = (count / total_cols * 100) if total_cols else 0
            st.markdown(
                f"""
                <div style="display:flex; align-items:center; gap:0.6rem;
                            margin-bottom:0.55rem;">
                    <div style="min-width:140px; font-size:0.82rem; font-weight:500;
                                color:var(--text-secondary);">{label}</div>
                    <div style="flex:1; height:8px; background:var(--border-color);
                                border-radius:100px; overflow:hidden;">
                        <div style="width:{pct}%; height:100%;
                                    background:{bar_color}; border-radius:100px;
                                    transition:width 0.6s ease;"></div>
                    </div>
                    <div style="min-width:35px; text-align:right; font-size:0.82rem;
                                font-weight:700; color:var(--text-primary);">{count}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("")  # spacer

    # ── Recommendations ──
    recommendations = []

    if missing_pct > 0:
        recommendations.append(
            (f"⚠️ {missing_pct:.1f}% of cells contain missing values — consider imputation or removal.",
             "")
        )
    if duplicates > 0:
        recommendations.append(
            (f"🔁 Found {duplicates:,} duplicate rows — consider deduplication.", "")
        )

    # Check for high-cardinality categoricals
    for c in working_df.select_dtypes(include=["object", "category"]).columns:
        nunique = working_df[c].nunique()
        if nunique > 50:
            recommendations.append(
                (f"📑 Column <b>{c}</b> has {nunique} unique values — may need grouping or encoding.", "info")
            )

    # Check for potential date columns stored as strings
    for c in working_df.select_dtypes(include="object").columns:
        sample = working_df[c].dropna().head(20)
        if sample.empty:
            continue
        try:
            pd.to_datetime(sample, infer_datetime_format=True)
            recommendations.append(
                (f"📅 Column <b>{c}</b> looks like a date but is stored as text — consider converting.", "info")
            )
        except (ValueError, TypeError):
            pass

    if score == 100 and not recommendations:
        recommendations.append(
            ("✅ Your data looks clean! No immediate issues detected.", "")
        )

    rec_col, act_col = st.columns([3, 2])

    with rec_col:
        st.markdown(
            '<div class="content-card"><h3>💡 Recommendations</h3>',
            unsafe_allow_html=True,
        )
        if recommendations:
            for text, style in recommendations[:6]:
                cls = "recommendation info" if style == "info" else "recommendation"
                st.markdown(f'<div class="{cls}">{text}</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                '<p style="color:var(--text-muted); font-size:0.85rem;">No recommendations right now.</p>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with act_col:
        st.markdown(
            '<div class="content-card"><h3>🕒 Recent Activity</h3>',
            unsafe_allow_html=True,
        )
        activity_log = st.session_state.get("activity_log", [])
        if activity_log:
            for entry in activity_log[-5:][::-1]:
                action = entry.get("action", "Action")
                timestamp = entry.get("time", "")
                st.markdown(
                    f"""
                    <div class="activity-item">
                        <div class="activity-dot"></div>
                        <div>
                            <div>{action}</div>
                            <div class="activity-time">{timestamp}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                """
                <div style="text-align:center; padding:1.5rem 0;">
                    <div style="font-size:1.5rem; opacity:0.3; margin-bottom:0.4rem;">📝</div>
                    <p style="color:var(--text-muted); font-size:0.82rem;">
                        No actions yet.<br>Start cleaning to see your history.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("")  # spacer

    # ── Data preview ──
    st.markdown(
        '<div class="content-card"><h3>🔍 Sample Data Preview</h3>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)
    st.dataframe(working_df.head(8), use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────

def render_dashboard():
    """Render the Dashboard home page."""
    if st.session_state.get("original_df") is None:
        st.info("📂 Please upload a dataset to view the dashboard.")
        return
    _render_loaded_dashboard()
