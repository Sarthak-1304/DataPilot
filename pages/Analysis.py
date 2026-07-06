"""
Data Analysis Page
==================
Automatic dataset profiling with interactive Plotly visualizations.
Sections:
    1. Overview metrics (shape, types, missing, duplicates)
    2. Summary Statistics
    3. Column Information table
    4. Correlation Matrix
    5. Interactive Visualizations (tabbed)
       - Missing Value Heatmap & Bar
       - Histograms / Distribution
       - Box Plots
       - Bar / Pie Charts (categorical)
       - Scatter Plot
       - Correlation Heatmap
       - Numeric Overview grid
"""

import streamlit as st
import pandas as pd

from utils.analyzer import (
    get_dataset_shape,
    get_data_types,
    get_missing_values,
    get_unique_values,
    get_duplicate_info,
    get_summary_statistics,
    get_correlation_matrix,
    get_column_info,
    get_numeric_columns,
    get_categorical_columns,
)
from utils.charts import (
    missing_value_bar,
    missing_value_heatmap,
    histogram,
    distribution_plot,
    box_plot,
    bar_chart,
    pie_chart,
    correlation_heatmap,
    scatter_plot,
    numeric_overview,
)
from utils.helpers import format_number, get_memory_usage


# =============================================================================
# Section renderers
# =============================================================================

def _render_header():
    st.markdown(
        """
        <div class="top-header">
            <h2>📊 Data Analysis</h2>
            <p>Explore your dataset with automated profiling and interactive charts.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_overview_metrics(df: pd.DataFrame):
    """Top-row metric cards for quick dataset overview."""
    shape = get_dataset_shape(df)
    dup = get_duplicate_info(df)
    missing_total = int(df.isnull().sum().sum())
    total_cells = shape["rows"] * shape["columns"]
    missing_pct = round(missing_total / total_cells * 100, 1) if total_cells > 0 else 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    cards = [
        (c1, "📐", format_number(shape["rows"]), "Total Rows", "blue"),
        (c2, "📊", format_number(shape["columns"]), "Total Columns", "green"),
        (c3, "⚠️", f"{format_number(missing_total)}", "Missing Values", "orange"),
        (c4, "♻️", format_number(dup["duplicate_count"]), "Duplicate Rows", "red"),
        (c5, "💾", get_memory_usage(df), "Memory Usage", "purple"),
        (c6, "🔤", str(df.dtypes.nunique()), "Data Types", "blue"),
    ]

    for col, icon, value, label, color in cards:
        with col:
            st.markdown(
                f"""
                <div class="metric-card {color}">
                    <div class="metric-icon">{icon}</div>
                    <div class="metric-value">{value}</div>
                    <div class="metric-label">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_dataset_info(df: pd.DataFrame):
    """Expandable section with data types, missing values, unique values."""
    st.markdown("### 📋 Dataset Overview")

    tab_types, tab_missing, tab_unique, tab_info = st.tabs(
        ["🔤 Data Types", "⚠️ Missing Values", "🔢 Unique Values", "📑 Column Info"]
    )

    with tab_types:
        dtype_df = get_data_types(df)
        col_left, col_right = st.columns([3, 2])
        with col_left:
            st.dataframe(dtype_df, use_container_width=True, hide_index=True, height=350)
        with col_right:
            # Summary counts
            cat_counts = dtype_df["Category"].value_counts()
            st.markdown("#### Type Summary")
            for cat, count in cat_counts.items():
                pct = count / len(df.columns) * 100
                color_map = {"Numeric": "#3B82F6", "Categorical": "#F59E0B",
                             "DateTime": "#EF4444", "Boolean": "#8B5CF6"}
                color = color_map.get(cat, "#64748B")
                st.markdown(
                    f"""
                    <div style="margin-bottom:0.6rem;">
                        <div style="display:flex;justify-content:space-between;font-size:0.82rem;font-weight:500;margin-bottom:0.2rem;">
                            <span>{cat}</span>
                            <span style="color:#64748B;">{count} cols ({pct:.0f}%)</span>
                        </div>
                        <div style="width:100%;height:8px;background:#E2E8F0;border-radius:100px;overflow:hidden;">
                            <div style="width:{pct}%;height:100%;background:{color};border-radius:100px;"></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with tab_missing:
        missing_df = get_missing_values(df)
        has_missing = missing_df["Missing Count"].sum() > 0
        if has_missing:
            st.dataframe(missing_df, use_container_width=True, hide_index=True, height=350)
        else:
            st.success("✅ No missing values found! Your dataset is complete.")

    with tab_unique:
        unique_df = get_unique_values(df)
        st.dataframe(unique_df, use_container_width=True, hide_index=True, height=350)

    with tab_info:
        info_df = get_column_info(df)
        st.dataframe(info_df, use_container_width=True, hide_index=True, height=400)


def _render_summary_statistics(df: pd.DataFrame):
    """Descriptive statistics table."""
    st.markdown("### 📈 Summary Statistics")
    stats_df = get_summary_statistics(df)
    if not stats_df.empty:
        st.dataframe(stats_df, use_container_width=True, hide_index=True, height=400)
    else:
        st.info("No summary statistics available for this dataset.")


def _render_visualizations(df: pd.DataFrame):
    """Tabbed interactive Plotly charts section."""
    st.markdown("### 📊 Interactive Visualizations")

    numeric_cols = get_numeric_columns(df)
    categorical_cols = get_categorical_columns(df)

    # Main chart tabs
    (
        tab_missing,
        tab_hist,
        tab_box,
        tab_bar_pie,
        tab_scatter,
        tab_corr,
        tab_overview,
    ) = st.tabs([
        "⚠️ Missing Values",
        "📊 Histogram",
        "📦 Box Plot",
        "📊 Bar / Pie",
        "🔵 Scatter Plot",
        "🌡️ Correlation",
        "🔢 Overview",
    ])

    # ---- Missing Values ----
    with tab_missing:
        sub_tab1, sub_tab2 = st.tabs(["Bar Chart", "Heatmap"])
        with sub_tab1:
            st.plotly_chart(missing_value_bar(df), use_container_width=True)
        with sub_tab2:
            st.plotly_chart(missing_value_heatmap(df), use_container_width=True)

    # ---- Histogram / Distribution ----
    with tab_hist:
        if numeric_cols:
            col_sel, col_bins = st.columns([3, 1])
            with col_sel:
                selected = st.selectbox("Select column", numeric_cols, key="hist_col")
            with col_bins:
                bins = st.slider(
                    "Histogram Bins",
                    10,
                    100,
                    30,
                    key="hist_bins",
                    help="Adjust the number of bins (vertical bars) to change the granularity of the data distribution.",
                )

            chart_type = st.radio(
                "Chart type", ["Histogram", "Distribution (KDE)"],
                horizontal=True, key="hist_type",
            )
            if chart_type == "Histogram":
                st.plotly_chart(histogram(df, selected, bins), use_container_width=True)
            else:
                st.plotly_chart(distribution_plot(df, selected), use_container_width=True)
        else:
            st.info("No numeric columns available for histogram.")

    # ---- Box Plot ----
    with tab_box:
        if numeric_cols:
            col1, col2 = st.columns(2)
            with col1:
                box_col = st.selectbox("Numeric column", numeric_cols, key="box_col")
            with col2:
                group_options = ["None"] + categorical_cols
                group_col = st.selectbox("Group by", group_options, key="box_group")

            group = group_col if group_col != "None" else None
            st.plotly_chart(box_plot(df, box_col, group), use_container_width=True)
        else:
            st.info("No numeric columns available for box plot.")

    # ---- Bar / Pie Charts ----
    with tab_bar_pie:
        if categorical_cols:
            cat_col = st.selectbox("Select column", categorical_cols, key="cat_col")
            top_n = st.slider(
                "Display Limit (Top N Categories)",
                5,
                30,
                10,
                key="cat_topn",
                help="Select the maximum number of most frequent categories to display in the charts to avoid clutter.",
            )

            sub1, sub2 = st.columns(2)
            with sub1:
                st.plotly_chart(bar_chart(df, cat_col, top_n), use_container_width=True)
            with sub2:
                st.plotly_chart(pie_chart(df, cat_col, top_n), use_container_width=True)
        else:
            st.info("No categorical columns available for bar/pie charts.")

    # ---- Scatter Plot ----
    with tab_scatter:
        if len(numeric_cols) >= 2:
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                x_col = st.selectbox("X axis", numeric_cols, index=0, key="scatter_x")
            with sc2:
                y_default = 1 if len(numeric_cols) > 1 else 0
                y_col = st.selectbox("Y axis", numeric_cols, index=y_default, key="scatter_y")
            with sc3:
                color_options = ["None"] + categorical_cols
                color_col = st.selectbox("Color by", color_options, key="scatter_color")

            color = color_col if color_col != "None" else None
            st.plotly_chart(scatter_plot(df, x_col, y_col, color), use_container_width=True)
        else:
            st.info("Need at least 2 numeric columns for a scatter plot.")

    # ---- Correlation Heatmap ----
    with tab_corr:
        if len(numeric_cols) >= 2:
            st.plotly_chart(correlation_heatmap(df), use_container_width=True)

            # Also show the correlation table
            with st.expander("📋 Correlation Table"):
                corr_df = get_correlation_matrix(df)
                if not corr_df.empty:
                    st.dataframe(corr_df, use_container_width=True)
        else:
            st.info("Need at least 2 numeric columns for a correlation analysis.")

    # ---- Numeric Overview Grid ----
    with tab_overview:
        if numeric_cols:
            max_cols = st.slider(
                "Columns to Display in Grid",
                2,
                12,
                6,
                key="overview_max",
                help="Adjust the maximum number of numeric columns to render in the grid overview at once.",
            )
            st.plotly_chart(
                numeric_overview(df, numeric_cols, max_cols),
                use_container_width=True,
            )
        else:
            st.info("No numeric columns available for the overview.")


# =============================================================================
# Main page renderer
# =============================================================================

def render_analysis():
    """Render the complete Data Analysis page."""
    _render_header()

    df = st.session_state.get("original_df")
    if df is None:
        st.markdown(
            """
            <div class="content-card">
                <div class="empty-state">
                    <div class="empty-icon">📊</div>
                    <h3>No Dataset Loaded</h3>
                    <p>Upload a CSV or Excel file first to explore your data here.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    original_df = st.session_state["original_df"]
    cleaned_df = st.session_state.get("cleaned_df")

    if cleaned_df is not None:
        target_df = cleaned_df
        banner_text = "Currently analyzing cleaned dataset"
        banner_icon = "✅"
        banner_bg = "rgba(16,185,129,0.08)"
        banner_border = "rgba(16,185,129,0.25)"
        steps = st.session_state.get("cleaning_steps", [])
        step_count = len(steps) if steps else 0
        banner_desc = f"— {step_count} cleaning step(s) applied"
    else:
        target_df = original_df
        banner_text = "Currently analyzing original dataset"
        banner_icon = "⚠️"
        banner_bg = "rgba(245,158,11,0.08)"
        banner_border = "rgba(245,158,11,0.25)"
        banner_desc = "— No cleaning steps applied yet"

    st.markdown(
        f"""
        <div style="background:{banner_bg}; border:1px solid {banner_border};
                    border-radius:8px; padding:0.6rem 1rem; margin-bottom:1rem;
                    font-size:0.85rem; display:flex; align-items:center; gap:0.5rem;">
            <span style="font-size:1.1rem;">{banner_icon}</span>
            <span><strong>{banner_text}</strong>
            ({target_df.shape[0]:,} rows × {target_df.shape[1]} cols)
            {banner_desc}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Analysis runs on target_df
    _render_overview_metrics(target_df)
    st.markdown("")
    _render_dataset_info(target_df)
    st.markdown("")
    _render_summary_statistics(target_df)
    st.markdown("")
    _render_visualizations(target_df)


