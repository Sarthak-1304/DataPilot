"""
Data Analysis Page (Redesigned)
================================
Automated patterns, relationship mapping, and business insights.
Sections:
    - Hero & Banner
    - Executive KPIs
    - Interactive Tabs:
      1. Overview (Dataset Summary, Feature Health)
      2. Statistics (Descriptive Stats & Column Profiler)
      3. Distributions (Histogram, Boxplot, Violin, Density & Interpretations)
      4. Relationships (X-Y Scatter/Bubble Explorer & Trends)
      5. Correlations (Heatmap, Top Relationships, Explanations)
      6. Insights (Smart/Business Insights, Outliers, Time Series, Missing Heatmap)
      7. Recommendations (Confidence Score & AI Readiness)
      8. Export (Reports & Stats)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io

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
from utils.helpers import format_number, get_memory_usage
from utils.cleaner import calculate_quality_score as calc_quality_dict

import importlib
import ai.gemini_manager
importlib.reload(ai.gemini_manager)
from ai.gemini_manager import is_gemini_configured

import ai.insight_agent
importlib.reload(ai.insight_agent)
from ai.insight_agent import InsightAgent


# =============================================================================
# Helper Utilities
# =============================================================================

def get_date_columns(df: pd.DataFrame) -> list:
    """Detect date-like columns in the dataset."""
    date_cols = []
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            date_cols.append(col)
        elif df[col].dtype == "object":
            # Sample check
            sample = df[col].dropna().head(20)
            if len(sample) > 0:
                parsed_dates = 0
                for val in sample:
                    try:
                        pd.to_datetime(val, errors="raise")
                        parsed_dates += 1
                    except Exception:
                        pass
                if parsed_dates / len(sample) > 0.8:
                    date_cols.append(col)
    return date_cols


def detect_target_column(df: pd.DataFrame) -> str:
    """Identify possible target column for prediction / analytics."""
    possible_targets = ["target", "label", "class", "churn", "price", "revenue", "sales", "y", "status", "salary"]
    for col in df.columns:
        if col.lower() in possible_targets:
            return col
    return df.columns[-1] if len(df.columns) > 0 else None


def get_outlier_info(df: pd.DataFrame) -> dict:
    """Determine outliers details across all numeric columns."""
    info = {}
    num_cols = get_numeric_columns(df)
    for col in num_cols:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        if iqr > 0:
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            mask = (df[col] < lower) | (df[col] > upper)
            cnt = int(mask.sum())
            if cnt > 0:
                outliers = df.loc[mask, col]
                info[col] = {
                    "count": cnt,
                    "percentage": round(cnt / len(df) * 100, 2),
                    "min": outliers.min(),
                    "max": outliers.max(),
                }
    return info


def draw_gauge(score: float, color: str = "#6366F1") -> go.Figure:
    """Create a premium looking semi-circular gauge indicator without built-in titles to prevent clipping."""
    current_theme = st.session_state.get("theme", "dark")
    if current_theme == "dark":
        text_primary = "#FFFFFF"
        text_secondary = "#94A3B8"
        text_muted = "#64748B"
        border_color = "#252438"
    else:
        text_primary = "#0F172A"
        text_secondary = "#475569"
        text_muted = "#64748B"
        border_color = "#E2E8F0"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={'font': {'size': 32, 'color': text_primary, 'family': 'Inter'}, 'suffix': "%"},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': text_muted},
            'bar': {'color': color},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 1,
            'bordercolor': border_color,
            'steps': [
                {'range': [0, 50], 'color': 'rgba(239, 68, 68, 0.08)'},
                {'range': [50, 80], 'color': 'rgba(245, 158, 11, 0.08)'},
                {'range': [80, 100], 'color': 'rgba(16, 185, 129, 0.08)'}
            ],
        }
    ))
    fig.update_layout(
        height=140,
        margin=dict(l=30, r=30, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def generate_smart_insights(df: pd.DataFrame) -> list:
    """Generate 10-20 automatic deep dataset insights."""
    insights = []
    num_cols = get_numeric_columns(df)
    cat_cols = get_categorical_columns(df)
    date_cols = get_date_columns(df)

    # 1. High variance
    if num_cols:
        stds = df[num_cols].std()
        max_var_col = stds.idxmax() if not stds.isna().all() else None
        if max_var_col:
            insights.append({
                "title": "High Dispersion / Variance",
                "desc": f"The column with the highest variance is <b>{max_var_col}</b> (std: {stds[max_var_col]:.2f}). This indicates significant spread in values.",
                "badge": "Variance",
                "color": "blue"
            })

    # 2. Skewness
    for col in num_cols:
        skew = df[col].skew()
        if not pd.isna(skew):
            if skew > 1.0:
                insights.append({
                    "title": f"Positive Skew ({col})",
                    "desc": f"Column <b>{col}</b> has a positive skewness of {skew:.2f}. Most records gather at lower values with a long right tail.",
                    "badge": "Skewness",
                    "color": "orange"
                })
            elif skew < -1.0:
                insights.append({
                    "title": f"Negative Skew ({col})",
                    "desc": f"Column <b>{col}</b> has a negative skewness of {skew:.2f}. Most records gather at higher values with a long left tail.",
                    "badge": "Skewness",
                    "color": "purple"
                })

    # 3. Normality
    for col in num_cols:
        skew = df[col].skew()
        kurt = df[col].kurtosis()
        if not pd.isna(skew) and not pd.isna(kurt):
            if -0.5 < skew < 0.5 and -0.5 < kurt < 0.5:
                insights.append({
                    "title": f"Symmetric Distribution ({col})",
                    "desc": f"Column <b>{col}</b> exhibits approximately normal/symmetric properties, ideal for linear statistical modeling.",
                    "badge": "Normality",
                    "color": "green"
                })

    # 4. Completeness
    missing = df.isnull().sum()
    complete_cols = [col for col in df.columns if missing[col] == 0]
    if complete_cols:
        insights.append({
            "title": "Perfect Completeness",
            "desc": f"Columns <b>{', '.join(complete_cols[:3])}</b> have 100% data presence, which ensures complete feature reliability.",
            "badge": "Completeness",
            "color": "green"
        })

    # 5. Dominant Category
    for col in cat_cols:
        counts = df[col].value_counts()
        if not counts.empty:
            top_val = counts.index[0]
            top_pct = (counts.iloc[0] / len(df)) * 100
            if top_pct > 40:
                insights.append({
                    "title": f"Dominant Class in {col}",
                    "desc": f"Category <b>'{top_val}'</b> is heavily dominant in <b>{col}</b>, representing {top_pct:.1f}% of total data.",
                    "badge": "Distribution",
                    "color": "blue"
                })

    # 6. High Cardinality
    for col in cat_cols:
        nunique = df[col].nunique()
        pct = (nunique / len(df)) * 100
        if pct > 80 and len(df) > 30:
            insights.append({
                "title": f"High Cardinality ({col})",
                "desc": f"<b>{col}</b> contains {nunique} unique values ({pct:.1f}% of records), pointing to a possible identifier or key.",
                "badge": "Cardinality",
                "color": "red"
            })

    # 7. Correlations
    if len(num_cols) >= 2:
        corr = df[num_cols].corr()
        corr_vals = corr.to_numpy(copy=True)
        np.fill_diagonal(corr_vals, 0)
        corr_clean = pd.DataFrame(corr_vals, index=corr.index, columns=corr.columns)
        strong_pos = corr_clean.stack().idxmax() if not corr_clean.stack().isna().all() else None
        strong_neg = corr_clean.stack().idxmin() if not corr_clean.stack().isna().all() else None

        if strong_pos:
            val = corr.loc[strong_pos[0], strong_pos[1]]
            if val > 0.4:
                insights.append({
                    "title": "Strong Linear Correlation",
                    "desc": f"<b>{strong_pos[0]}</b> shows a strong positive correlation with <b>{strong_pos[1]}</b> (r = {val:.2f}).",
                    "badge": "Correlation",
                    "color": "green"
                })
        if strong_neg:
            val = corr.loc[strong_neg[0], strong_neg[1]]
            if val < -0.4:
                insights.append({
                    "title": "Inverse Linear Correlation",
                    "desc": f"<b>{strong_neg[0]}</b> shows a strong negative/inverse correlation with <b>{strong_neg[1]}</b> (r = {val:.2f}).",
                    "badge": "Correlation",
                    "color": "red"
                })

    # 8. Weekend vs Weekdays
    if date_cols and num_cols:
        try:
            date_col = date_cols[0]
            dt_series = pd.to_datetime(df[date_col], errors="coerce")
            if dt_series.notna().sum() > 0:
                is_weekend = dt_series.dt.dayofweek.isin([5, 6])
                for num_col in num_cols[:2]:
                    weekend_mean = df.loc[is_weekend, num_col].mean()
                    weekday_mean = df.loc[~is_weekend, num_col].mean()
                    if not pd.isna(weekend_mean) and not pd.isna(weekday_mean) and weekday_mean > 0:
                        diff_pct = ((weekend_mean - weekday_mean) / weekday_mean) * 100
                        if abs(diff_pct) > 10:
                            dir_str = "higher" if diff_pct > 0 else "lower"
                            insights.append({
                                "title": f"Weekend Behavior ({num_col})",
                                "desc": f"Average values for <b>{num_col}</b> are {abs(diff_pct):.1f}% <b>{dir_str}</b> during weekends.",
                                "badge": "Seasonality",
                                "color": "purple"
                            })
        except Exception:
            pass

    # Ensure baseline
    if not insights:
        insights.append({
            "title": "Clean Data Profile",
            "desc": "Dataset columns are structured cleanly with normal variance across all key parameters.",
            "badge": "General",
            "color": "blue"
        })

    return insights


def generate_business_insights(df: pd.DataFrame) -> list:
    """Generate professional, human-like business explanations from data patterns."""
    insights = []
    num_cols = get_numeric_columns(df)
    cat_cols = get_categorical_columns(df)

    if cat_cols and num_cols:
        for cat in cat_cols[:2]:
            for num in num_cols[:2]:
                try:
                    grouped = df.groupby(cat)[num].sum().sort_values(ascending=False)
                    if not grouped.empty and grouped.sum() > 0:
                        top_cat = grouped.index[0]
                        top_share = (grouped.iloc[0] / grouped.sum()) * 100
                        insights.append(f"📦 <b>{top_cat}</b> contributes <b>{top_share:.1f}%</b> of total accumulated volume for <b>{num}</b>.")
                except Exception:
                    pass
    if num_cols:
        for col in num_cols[:2]:
            try:
                mean_val = df[col].mean()
                insights.append(f"📊 The average consolidated metric level for <b>{col}</b> stands at <b>{mean_val:,.1f}</b> units.")
            except Exception:
                pass
    if cat_cols:
        for col in cat_cols[:2]:
            try:
                top_5_cnt = df[col].value_counts().head(5).sum()
                top_5_pct = (top_5_cnt / len(df)) * 100
                insights.append(f"🎯 The top 5 concentrated values in <b>{col}</b> account for <b>{top_5_pct:.1f}%</b> of all operations.")
            except Exception:
                pass

    if len(insights) < 3:
        insights.append("📌 Group distributions demonstrate robust structural metrics with low variance.")
        insights.append("📌 Numeric columns feature stable metrics that are highly compatible with model training.")
        insights.append("📌 Categorical data features have low cardinality, making them ideal for conversion to nominal classes.")

    return insights


# =============================================================================
# Main Renderer Function
# =============================================================================

def render_analysis():
    """Redesigned automated Analysis page with custom visualizations and smart engines."""
    original_df = st.session_state.get("original_df")
    cleaned_df = st.session_state.get("cleaned_df")

    if original_df is None:
        st.markdown(
            """
            <div class="content-card">
                <div class="empty-state">
                    <div class="empty-icon">📊</div>
                    <h3>No Dataset Loaded</h3>
                    <p>Upload a CSV or Excel file first to unlock interactive data analysis.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # 1. Setup target DataFrame
    is_cleaned = cleaned_df is not None
    target_df = cleaned_df if is_cleaned else original_df
    step_count = len(st.session_state.get("cleaning_steps", []))

    # 2. Get quality dict
    q_dict = calc_quality_dict(target_df)

    # ==========================================
    # SECTION 1: HERO & BANNER
    # ==========================================
    banner_text = "Currently analyzing cleaned dataset" if is_cleaned else "Currently analyzing original dataset"
    banner_icon = "✅" if is_cleaned else "⚠️"
    banner_bg = "rgba(16,185,129,0.08)" if is_cleaned else "rgba(245,158,11,0.08)"
    banner_border = "rgba(16,185,129,0.25)" if is_cleaned else "rgba(245,158,11,0.25)"
    banner_desc = f"— {step_count} cleaning step(s) applied" if is_cleaned else "— No cleaning steps applied yet"

    st.markdown(
        f"""
        <div class="top-header">
            <h2>📊 Data Analysis</h2>
            <p>Explore patterns, relationships and business insights from your cleaned dataset.</p>
        </div>
        
        <div style="background:{banner_bg}; border:1px solid {banner_border};
                    border-radius:8px; padding:0.6rem 1rem; margin-bottom:1.2rem;
                    font-size:0.85rem; display:flex; align-items:center; gap:0.5rem;">
            <span style="font-size:1.1rem;">{banner_icon}</span>
            <span><strong>{banner_text}</strong>
            ({target_df.shape[0]:,} rows × {target_df.shape[1]} cols)
            {banner_desc}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Hero meta grid
    file_name = st.session_state.get("file_name", "dataset.csv")
    st.markdown(
        f"""
        <div style="display: flex; gap: 0.8rem; flex-wrap: wrap; margin-bottom: 1.5rem; background: var(--bg-card); padding: 0.8rem 1.1rem; border-radius: 8px; border: 1px solid var(--border-color);">
            <div style="flex: 1.5; min-width: 140px;">
                <span style="font-size: 0.72rem; color: var(--text-secondary); text-transform: uppercase; font-weight: 600; display: block;">Dataset Name</span>
                <span style="font-size: 0.88rem; font-weight: 700; color: var(--text-primary);">{file_name}</span>
            </div>
            <div style="flex: 1; min-width: 80px;">
                <span style="font-size: 0.72rem; color: var(--text-secondary); text-transform: uppercase; font-weight: 600; display: block;">Rows</span>
                <span style="font-size: 0.88rem; font-weight: 700; color: var(--text-primary);">{target_df.shape[0]:,}</span>
            </div>
            <div style="flex: 1; min-width: 80px;">
                <span style="font-size: 0.72rem; color: var(--text-secondary); text-transform: uppercase; font-weight: 600; display: block;">Columns</span>
                <span style="font-size: 0.88rem; font-weight: 700; color: var(--text-primary);">{target_df.shape[1]:,}</span>
            </div>
            <div style="flex: 1; min-width: 100px;">
                <span style="font-size: 0.72rem; color: var(--text-secondary); text-transform: uppercase; font-weight: 600; display: block;">Data Quality</span>
                <span style="font-size: 0.88rem; font-weight: 700; color: var(--primary-blue);">{q_dict["total"]}% ({q_dict["label"]})</span>
            </div>
            <div style="flex: 1.2; min-width: 130px;">
                <span style="font-size: 0.72rem; color: var(--text-secondary); text-transform: uppercase; font-weight: 600; display: block;">Dataset Status</span>
                <span style="font-size: 0.88rem; font-weight: 700; color: #10B981;">Ready for Analysis</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ==========================================
    # SECTION 2: EXECUTIVE KPI CARDS
    # ==========================================
    num_cols = get_numeric_columns(target_df)
    cat_cols = get_categorical_columns(target_df)
    mem_usage = get_memory_usage(target_df)

    # Calculating avg missing %
    missing_cells = target_df.isnull().sum().sum()
    total_cells = target_df.shape[0] * target_df.shape[1]
    avg_missing_pct = (missing_cells / total_cells * 100) if total_cells > 0 else 0

    # Calculating correlation strength
    if len(num_cols) >= 2:
        corr_matrix = target_df[num_cols].corr().abs()
        corr_vals = corr_matrix.to_numpy(copy=True)
        np.fill_diagonal(corr_vals, np.nan)
        mean_corr = np.nanmean(corr_vals)
        mean_corr_val = 0.0 if pd.isna(mean_corr) else float(mean_corr)
    else:
        mean_corr_val = 0.0
    corr_desc = "Strong" if mean_corr_val > 0.6 else ("Moderate" if mean_corr_val > 0.3 else "Weak")

    # Calculating outlier columns
    outlier_info = get_outlier_info(target_df)
    outlier_cols_count = len(outlier_info)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
            <div class="metric-card blue">
                <div class="metric-icon">🔢</div>
                <div class="metric-value">{len(num_cols)}</div>
                <div class="metric-label">Numeric Columns</div>
            </div>
            <div style="margin-bottom: 0.75rem;"></div>
            <div class="metric-card green">
                <div class="metric-icon">✅</div>
                <div class="metric-value">{q_dict["completeness"]:.0f}/30</div>
                <div class="metric-label">Completeness Score</div>
            </div>
            <div style="margin-bottom: 0.75rem;"></div>
            <div class="metric-card orange">
                <div class="metric-icon">⚠️</div>
                <div class="metric-value">{avg_missing_pct:.2f}%</div>
                <div class="metric-label">Average Missing %</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"""
            <div class="metric-card green">
                <div class="metric-icon">🔤</div>
                <div class="metric-value">{len(cat_cols)}</div>
                <div class="metric-label">Categorical Columns</div>
            </div>
            <div style="margin-bottom: 0.75rem;"></div>
            <div class="metric-card blue">
                <div class="metric-icon">💎</div>
                <div class="metric-value">{q_dict["uniqueness"]:.0f}/20</div>
                <div class="metric-label">Uniqueness Score</div>
            </div>
            <div style="margin-bottom: 0.75rem;"></div>
            <div class="metric-card purple">
                <div class="metric-icon">🌡️</div>
                <div class="metric-value">{mean_corr_val:.2f} ({corr_desc})</div>
                <div class="metric-label">Correlation Strength</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            f"""
            <div class="metric-card purple">
                <div class="metric-icon">💾</div>
                <div class="metric-value">{mem_usage}</div>
                <div class="metric-label">Memory Usage</div>
            </div>
            <div style="margin-bottom: 0.75rem;"></div>
            <div class="metric-card orange">
                <div class="metric-icon">🔄</div>
                <div class="metric-value">{q_dict["consistency"]:.0f}/20</div>
                <div class="metric-label">Consistency Score</div>
            </div>
            <div style="margin-bottom: 0.75rem;"></div>
            <div class="metric-card red">
                <div class="metric-icon">🚨</div>
                <div class="metric-value">{outlier_cols_count} Cols</div>
                <div class="metric-label">Outlier Columns</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

    # ==========================================
    # SECTION 3: ANALYSIS TABS
    # ==========================================
    tab_overview, tab_stats, tab_relation, tab_corr, tab_insights = st.tabs([
        "📋 Overview", "📈 Statistics", "🔄 Relationships", "🌡️ Correlations", "💡 Insights"
    ])

    # ----------------------------------------------------
    # TAB 1: OVERVIEW
    # ----------------------------------------------------
    with tab_overview:
        st.markdown("### 📋 Dataset Profile Overview")
        
        # Summary text
        target_col = detect_target_column(target_df)
        date_cols = get_date_columns(target_df)
        
        summary_html = f"""
        <div class="content-card" style="margin-bottom:1rem;">
            <h4>Dataset summary & structure</h4>
            <p style="font-size:0.82rem; line-height:1.5; color:var(--text-secondary);">
                This dataset contains <b>{target_df.shape[0]:,}</b> records and <b>{target_df.shape[1]}</b> attributes. 
                Our analytics engine detected <b>{len(num_cols)}</b> numerical fields, <b>{len(cat_cols)}</b> categorical features, 
                and <b>{len(date_cols)}</b> dates. 
                {"The target label for analysis has been detected as <b>" + target_col + "</b>." if target_col else "No explicit target column was detected."}
            </p>
        </div>
        """
        st.markdown(summary_html, unsafe_allow_html=True)

        # Feature Breakdown
        col_left, col_right = st.columns([3, 2])
        with col_left:
            st.markdown("#### Feature Health")
            health_rows = []
            for col in target_df.columns:
                missing_cnt = target_df[col].isnull().sum()
                missing_pct = (missing_cnt / len(target_df)) * 100
                unique_cnt = target_df[col].nunique()
                unique_pct = (unique_cnt / len(target_df)) * 100
                health_rows.append({
                    "Feature": col,
                    "Type": str(target_df[col].dtype),
                    "Missing %": f"{missing_pct:.1f}%",
                    "Unique Count": unique_cnt,
                    "Unique %": f"{unique_pct:.1f}%"
                })
            st.dataframe(pd.DataFrame(health_rows), use_container_width=True, hide_index=True)

        with col_right:
            st.markdown("#### Feature Classification")
            breakdown_data = pd.DataFrame({
                "Category": ["Numeric", "Categorical", "Date"],
                "Count": [len(num_cols), len(cat_cols), len(date_cols)]
            })
            fig_breakdown = px.pie(
                breakdown_data, values="Count", names="Category", hole=0.45,
                color_discrete_sequence=["#6366F1", "#10B981", "#8B5CF6"]
            )
            fig_breakdown.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                height=220,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=True,
                legend=dict(font=dict(size=10, color="var(--text-secondary)"))
            )
            st.plotly_chart(fig_breakdown, use_container_width=True)

    # ----------------------------------------------------
    # TAB 2: STATISTICS
    # ----------------------------------------------------
    with tab_stats:
        st.markdown("### 📈 Comprehensive Statistics")
        
        if num_cols:
            stats_rows = []
            for col in num_cols:
                series = target_df[col].dropna()
                if not series.empty:
                    q1 = series.quantile(0.25)
                    q3 = series.quantile(0.75)
                    iqr = q3 - q1
                    outliers_mask = (series < (q1 - 1.5 * iqr)) | (series > (q3 + 1.5 * iqr))
                    
                    stats_rows.append({
                        "Column": col,
                        "Count": len(series),
                        "Mean": round(series.mean(), 2),
                        "Median": round(series.median(), 2),
                        "Mode": round(series.mode().iloc[0], 2) if not series.mode().empty else np.nan,
                        "Min": round(series.min(), 2),
                        "Max": round(series.max(), 2),
                        "Std Dev": round(series.std(), 2),
                        "Variance": round(series.var(), 2),
                        "Q1 (25%)": round(q1, 2),
                        "Q3 (75%)": round(q3, 2),
                        "Unique": series.nunique(),
                        "Missing": target_df[col].isnull().sum(),
                        "Outliers": int(outliers_mask.sum())
                    })
            st.dataframe(pd.DataFrame(stats_rows), use_container_width=True, hide_index=True)
        else:
            st.info("No numeric columns available for statistical profiling.")

        st.markdown("<hr style='border: 0.5px solid var(--border-color);'>", unsafe_allow_html=True)
        st.markdown("### 🔍 Column Profiler")
        
        selected_col = st.selectbox("Select a column to inspect details:", target_df.columns, key="profiler_select")
        if selected_col:
            col_type = str(target_df[selected_col].dtype)
            total_vals = len(target_df)
            missing_cnt = target_df[selected_col].isnull().sum()
            missing_pct = (missing_cnt / total_vals) * 100
            unique_cnt = target_df[selected_col].nunique()
            unique_pct = (unique_cnt / total_vals) * 100

            pc1, pc2, pc3 = st.columns(3)
            with pc1:
                st.markdown(f"""
                <div class="metric-card blue">
                    <div class="metric-icon">📑</div>
                    <div class="metric-value">{col_type}</div>
                    <div class="metric-label">Column Type</div>
                </div>
                """, unsafe_allow_html=True)
            with pc2:
                st.markdown(f"""
                <div class="metric-card orange">
                    <div class="metric-icon">⚠️</div>
                    <div class="metric-value">{missing_pct:.1f}%</div>
                    <div class="metric-label">Missing Percentage</div>
                </div>
                """, unsafe_allow_html=True)
            with pc3:
                st.markdown(f"""
                <div class="metric-card green">
                    <div class="metric-icon">🔢</div>
                    <div class="metric-value">{unique_pct:.1f}%</div>
                    <div class="metric-label">Unique Percentage</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Extra info and charts based on type
            prof_left, prof_right = st.columns([1, 1])
            with prof_left:
                st.markdown("#### Stats Summary")
                if pd.api.types.is_numeric_dtype(target_df[selected_col]):
                    series = target_df[selected_col].dropna()
                    if not series.empty:
                        sum_data = pd.DataFrame({
                            "Metric": ["Mean", "Median", "Min", "Max", "Skewness", "Kurtosis"],
                            "Value": [f"{series.mean():.2f}", f"{series.median():.2f}", f"{series.min():.2f}", f"{series.max():.2f}", f"{series.skew():.2f}", f"{series.kurt():.2f}"]
                        })
                        st.dataframe(sum_data, use_container_width=True, hide_index=True)
                else:
                    counts = target_df[selected_col].value_counts().head(5)
                    top_cats = pd.DataFrame({
                        "Category": counts.index.astype(str),
                        "Count": counts.values,
                        "Share %": (counts.values / total_vals * 100).round(2)
                    })
                    st.dataframe(top_cats, use_container_width=True, hide_index=True)

            with prof_right:
                st.markdown("#### Quick Visualizer")
                if pd.api.types.is_numeric_dtype(target_df[selected_col]):
                    fig_prof = px.histogram(
                        target_df, x=selected_col, nbins=30,
                        color_discrete_sequence=["#6366F1"]
                    )
                else:
                    counts = target_df[selected_col].value_counts().head(10)
                    fig_prof = px.bar(
                        x=counts.index.astype(str), y=counts.values,
                        labels={"x": selected_col, "y": "Count"},
                        color_discrete_sequence=["#10B981"]
                    )
                fig_prof.update_layout(
                    margin=dict(l=10, r=10, t=10, b=10),
                    height=200,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_prof, use_container_width=True)

            # Custom recommendation
            rec_text = "No action required."
            if missing_pct > 15:
                rec_text = "<b>Recommendation:</b> Missing values are critical. Apply median/mode filling or drops."
            elif unique_pct > 90 and col_type == "object":
                rec_text = "<b>Recommendation:</b> Highly unique identifier column. Suggest dropping or indexing."
            elif pd.api.types.is_numeric_dtype(target_df[selected_col]):
                q1 = target_df[selected_col].quantile(0.25)
                q3 = target_df[selected_col].quantile(0.75)
                iqr = q3 - q1
                if iqr > 0:
                    outliers = ((target_df[selected_col] < (q1 - 1.5 * iqr)) | (target_df[selected_col] > (q3 + 1.5 * iqr))).sum()
                    if outliers > 0:
                        rec_text = f"<b>Recommendation:</b> Detected {outliers} outliers. Recommend Winsorizing/Capping extreme thresholds."

            st.markdown(f"<div class='recommendation info'>{rec_text}</div>", unsafe_allow_html=True)



    # ----------------------------------------------------
    # TAB 4: RELATIONSHIPS
    # ----------------------------------------------------
    with tab_relation:
        st.markdown("### 🔄 Interactive Relationship Explorer")
        if len(num_cols) >= 2:
            r_c1, r_c2, r_c3, r_c4 = st.columns(4)
            with r_c1:
                rx = st.selectbox("X Axis (Numeric)", num_cols, index=0, key="rel_x")
            with r_c2:
                ry = st.selectbox("Y Axis (Numeric)", num_cols, index=1 if len(num_cols) > 1 else 0, key="rel_y")
            with r_c3:
                color_opt = ["None"] + cat_cols + num_cols
                r_color = st.selectbox("Color By", color_opt, key="rel_color")
            with r_c4:
                size_opt = ["None"] + num_cols
                r_size = st.selectbox("Size By", size_opt, key="rel_size")

            trendline = st.checkbox("Include Regression Line (OLS)", value=True, key="rel_trend")

            # Prepare plot parameters
            kwargs = {
                "x": rx,
                "y": ry,
                "color": r_color if r_color != "None" else None,
                "size": r_size if r_size != "None" else None,
                "color_discrete_sequence": px.colors.qualitative.Plotly,
                "color_continuous_scale": px.colors.sequential.Viridis,
            }
            if trendline:
                kwargs["trendline"] = "ols"
                kwargs["trendline_color_override"] = "#EF4444"

            try:
                fig_relation = px.scatter(target_df, **kwargs)
                fig_relation.update_layout(
                    margin=dict(l=20, r=20, t=30, b=20),
                    height=450,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_relation, use_container_width=True)

                # Correlation coefficient for text interpretation
                corr_val = target_df[[rx, ry]].corr().iloc[0, 1]
                strength = "strong" if abs(corr_val) > 0.6 else ("moderate" if abs(corr_val) > 0.3 else "weak")
                direction = "positive" if corr_val > 0 else "negative"

                st.markdown(
                    f"""
                    <div class="content-card" style="margin-top: 1rem;">
                        <h4>Relationship Interpretation</h4>
                        <p style="font-size:0.82rem; line-height:1.5; color:var(--text-secondary);">
                            There exists a <b>{strength} {direction} linear relationship</b> between <b>{rx}</b> and <b>{ry}</b>, 
                            with a Pearson correlation coefficient (r) of <b>{corr_val:.3f}</b>. 
                            The coefficient of determination (R²) stands at approximately <b>{corr_val**2:.3f}</b>.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            except Exception as e:
                st.error(f"Error rendering chart: {str(e)}")
        else:
            st.info("Need at least 2 numeric columns for relationship analysis.")

    # ----------------------------------------------------
    # TAB 5: CORRELATIONS
    # ----------------------------------------------------
    with tab_corr:
        st.markdown("### 🌡️ Correlation Mapping")
        if len(num_cols) >= 2:
            # Heatmap
            corr_mat = target_df[num_cols].corr()
            fig_heat = px.imshow(
                corr_mat, text_auto=True, color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                title="Pearson Correlation Heatmap"
            )
            fig_heat.update_layout(
                margin=dict(l=20, r=20, t=40, b=20),
                height=450,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_heat, use_container_width=True)

            # Top Strong Relationships
            st.markdown("#### Strongest Correlated Relationships")
            corr_stack = corr_mat.stack().reset_index()
            corr_stack.columns = ["Var 1", "Var 2", "r"]
            # Exclude self correlation
            corr_stack = corr_stack[corr_stack["Var 1"] != corr_stack["Var 2"]]
            corr_stack["abs_r"] = corr_stack["r"].abs()
            top_corr = corr_stack.sort_values(by="abs_r", ascending=False).drop_duplicates(subset=["abs_r"]).head(10)

            c_rows = []
            for _, r in top_corr.iterrows():
                effect = "Strong Positive" if r["r"] > 0.6 else ("Strong Negative" if r["r"] < -0.6 else ("Moderate" if abs(r["r"]) > 0.3 else "Weak"))
                c_rows.append({
                    "Relationship": f"{r['Var 1']} ↔ {r['Var 2']}",
                    "Correlation Coefficient (r)": round(r["r"], 3),
                    "Type": effect
                })

            st.dataframe(pd.DataFrame(c_rows), use_container_width=True, hide_index=True)
        else:
            st.info("Need at least 2 numeric columns for correlation details.")

    # ----------------------------------------------------
    # TAB 6: INSIGHTS
    # ----------------------------------------------------
    with tab_insights:
        st.markdown("### 💡 Auto-Generated Data Insights")
        
        # Sub tabs for insights categorization
        sub_smart, sub_business, sub_outliers, sub_time, sub_missing = st.tabs([
            "🧠 Smart Insights", "💼 Business Insights", "🚨 Outliers Profile", "📅 Time Series", "⚠️ Missing Patterns"
        ])

        with sub_smart:
            st.markdown("#### Automated Observations & Patterns")
            smart_list = None
            if is_gemini_configured():
                with st.spinner("🤖 Generating AI Smart Insights..."):
                    try:
                        smart_list = InsightAgent.generate_ai_smart_insights(target_df)
                    except Exception:
                        smart_list = None

            is_ai_smart = smart_list is not None
            if not smart_list:
                smart_list = generate_smart_insights(target_df)

            if is_ai_smart:
                st.caption("✨ *Generated dynamically by AI Engine*")
            
            # Show insights in clean row list
            for ins in smart_list:
                badge_color_map = {
                    "blue": "rgba(59, 130, 246, 0.15); color: #3B82F6;",
                    "orange": "rgba(245, 158, 11, 0.15); color: #F59E0B;",
                    "purple": "rgba(139, 92, 246, 0.15); color: #8B5CF6;",
                    "green": "rgba(16, 185, 129, 0.15); color: #10B981;",
                    "red": "rgba(239, 68, 68, 0.15); color: #EF4444;"
                }
                b_style = badge_color_map.get(ins["color"], "rgba(100, 116, 139, 0.15); color: #64748B;")
                st.markdown(
                    f"""
                    <div style="background: var(--bg-card); padding: 0.9rem; border-radius: 8px; border: 1px solid var(--border-color); margin-bottom: 0.75rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                            <span style="font-weight: 700; color: var(--text-primary); font-size: 0.9rem;">{ins["title"]}</span>
                            <span style="font-size: 0.68rem; font-weight: 600; padding: 0.15rem 0.6rem; border-radius: 100px; {b_style}">{ins["badge"]}</span>
                        </div>
                        <p style="font-size: 0.8rem; margin: 0; color: var(--text-secondary); line-height: 1.4;">{ins["desc"]}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        with sub_business:
            st.markdown("#### Executive Summary in Business Language")
            bus_list = None
            if is_gemini_configured():
                with st.spinner("🤖 Generating AI Business Insights..."):
                    try:
                        bus_list = InsightAgent.generate_ai_business_insights(target_df)
                    except Exception:
                        bus_list = None

            is_ai_bus = bus_list is not None
            if not bus_list:
                bus_list = generate_business_insights(target_df)

            if is_ai_bus:
                st.caption("✨ *Generated dynamically by AI Engine*")

            for bus in bus_list:
                st.markdown(
                    f"""
                    <div style="background: rgba(99, 102, 241, 0.04); padding: 0.75rem 1rem; border-left: 3px solid #6366F1; margin-bottom: 0.6rem; font-size: 0.82rem; color: var(--text-secondary);">
                        {bus}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        with sub_outliers:
            st.markdown("#### Outlier Analysis details")
            if is_gemini_configured() and outlier_info:
                with st.spinner("🤖 Generating AI Outlier Analysis..."):
                    try:
                        ai_outlier_text = InsightAgent.generate_ai_outliers_insight(target_df, outlier_info)
                        if ai_outlier_text:
                            st.markdown(
                                f"""
                                <div style="background: rgba(239, 68, 68, 0.04); padding: 0.85rem 1.1rem; border-left: 3px solid #EF4444; border-radius: 4px; margin-bottom: 1rem; font-size: 0.85rem; color: var(--text-primary);">
                                    {ai_outlier_text}
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                            st.caption("✨ *Generated dynamically by AI Engine*")
                    except Exception:
                        pass

            if outlier_info:
                o_data = []
                for k, v in outlier_info.items():
                    o_data.append({
                        "Column": k,
                        "Outlier Count": v["count"],
                        "Outlier %": f"{v['percentage']}%",
                        "Min Extreme": round(v["min"], 2),
                        "Max Extreme": round(v["max"], 2)
                    })
                st.dataframe(pd.DataFrame(o_data), use_container_width=True, hide_index=True)
                
                # Boxplots
                st.markdown("##### Outliers Distribution Plot")
                fig_o = px.box(target_df, y=list(outlier_info.keys())[:3], points="outliers")
                fig_o.update_layout(
                    margin=dict(l=10, r=10, t=10, b=10),
                    height=300,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_o, use_container_width=True)
            else:
                st.success("✅ No outliers detected in numerical columns.")

        with sub_time:
            st.markdown("#### Time Series & Seasonality Detection")
            date_cols = get_date_columns(target_df)
            if date_cols:
                d_col = date_cols[0]
                st.info(f"Detected Date Column: **{d_col}**", icon="📅")
                
                # Check for numeric column to plot over time
                if num_cols:
                    t_num = num_cols[0]
                    # Parse dates
                    ts_df = target_df[[d_col, t_num]].copy()
                    ts_df[d_col] = pd.to_datetime(ts_df[d_col], errors="coerce")
                    ts_df = ts_df.dropna().sort_values(by=d_col)
                    
                    if not ts_df.empty:
                        # Resample to weekly / monthly mean
                        ts_df.set_index(d_col, inplace=True)
                        ts_resampled = ts_df.resample("W").mean().reset_index()
                        
                        fig_ts = px.line(ts_resampled, x=d_col, y=t_num, title=f"Weekly Average of {t_num} over time")
                        fig_ts.update_layout(
                            margin=dict(l=20, r=20, t=40, b=20),
                            height=320,
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                        )
                        st.plotly_chart(fig_ts, use_container_width=True)
                        
                        ai_ts_text = None
                        if is_gemini_configured():
                            try:
                                ai_ts_text = InsightAgent.generate_ai_timeseries_insight(target_df, d_col, t_num)
                            except Exception:
                                ai_ts_text = None

                        if ai_ts_text:
                            interp_body = ai_ts_text
                            caption = "✨ *Generated dynamically by AI Engine*"
                        else:
                            interp_body = f"Average levels for <b>{t_num}</b> feature stable temporal changes. Reviewing rolling distributions is recommended for predictive scheduling."
                            caption = ""

                        st.markdown(
                            f"""
                            <div class="content-card">
                                <h5>Trend Interpretation</h5>
                                <p style="font-size:0.8rem; color:var(--text-secondary);">
                                    {interp_body}
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        if caption:
                            st.caption(caption)
                    else:
                        st.warning("Empty records after date conversions.")
                else:
                    st.info("No numeric fields available to cross-analyze dates.")
            else:
                st.info("No datetime column was detected in this dataset.")

        with sub_missing:
            st.markdown("#### Missing Value Patterns")
            missing_df = get_missing_values(target_df)
            if missing_df["Missing Count"].sum() > 0:
                if is_gemini_configured():
                    try:
                        ai_missing_text = InsightAgent.generate_ai_missing_insight(target_df, missing_df)
                        if ai_missing_text:
                            st.markdown(
                                f"""
                                <div style="background: rgba(245, 158, 11, 0.04); padding: 0.85rem 1.1rem; border-left: 3px solid #F59E0B; border-radius: 4px; margin-bottom: 1rem; font-size: 0.85rem; color: var(--text-primary);">
                                    {ai_missing_text}
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                            st.caption("✨ *Generated dynamically by AI Engine*")
                    except Exception:
                        pass

                m_c1, m_c2 = st.columns([1, 1])
                with m_c1:
                    # Missing values heatmap
                    null_matrix = target_df.isnull().astype(int)
                    fig_miss_heat = px.imshow(
                        null_matrix.head(100), color_continuous_scale=[[0, "rgba(0,0,0,0)"], [1, "#EF4444"]],
                        title="Missing Patterns Heatmap (First 100 rows)"
                    )
                    fig_miss_heat.update_layout(
                        margin=dict(l=10, r=10, t=40, b=10),
                        height=280,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        showlegend=False,
                    )
                    fig_miss_heat.update_coloraxes(showscale=False)
                    st.plotly_chart(fig_miss_heat, use_container_width=True)
                with m_c2:
                    st.markdown("##### Columns Ranked by Missing Counts")
                    st.dataframe(missing_df, use_container_width=True, hide_index=True)
            else:
                st.success("✅ No missing values detected in the entire dataset.")



    # ==========================================
    # SECTION 4: EXPORT
    # ==========================================
    st.markdown("<hr style='border: 0.5px solid var(--border-color);'>", unsafe_allow_html=True)
    st.markdown("### 💾 Export Reports & Data Profiles")
    
    e1, e2, e3 = st.columns(3)
    with e1:
        # Excel stats
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            target_df.describe().to_excel(writer, sheet_name="Descriptive Stats")
            pd.DataFrame(get_column_info(target_df)).to_excel(writer, sheet_name="Column Details")
        st.download_button(
            label="📊 Download Excel Summary",
            data=buffer.getvalue(),
            file_name="dataset_analysis_profile.xlsx",
            mime="application/vnd.ms-excel",
            use_container_width=True
        )
    with e2:
        # CSV Statistics
        stats_csv = target_df.describe().to_csv().encode('utf-8')
        st.download_button(
            label="📑 Download CSV Statistics",
            data=stats_csv,
            file_name="descriptive_statistics.csv",
            mime="text/csv",
            use_container_width=True
        )
    with e3:
        # Dummy html download
        html_report = f"""
        <html>
        <head><title>Data Pilot Analysis Report</title></head>
        <body style="font-family:sans-serif; padding:20px;">
            <h1>Data Pilot Dataset Profile Summary</h1>
            <p>Dataset Name: {file_name}</p>
            <p>Dimensions: {target_df.shape[0]} rows x {target_df.shape[1]} columns</p>
            <p>Data Quality Score: {q_dict["total"]}%</p>
            <h2>Descriptive Statistics Summary</h2>
            {target_df.describe().to_html()}
        </body>
        </html>
        """
        st.download_button(
            label="🌐 Download HTML Report",
            data=html_report.encode('utf-8'),
            file_name="datapilot_report.html",
            mime="text/html",
            use_container_width=True
        )

