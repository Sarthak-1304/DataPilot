"""
Report Builder Utility
======================
Gathers dataset metadata, workflow statistics, cleaning logs, statistical profiles,
and business insights into a unified report data structure.
"""

import pandas as pd
import numpy as np
import datetime
from typing import Dict, Any, List, Optional
import streamlit as st

from utils.cleaner import calculate_quality_score
from utils.analyzer import (
    get_dataset_shape, get_data_types, get_missing_values,
    get_unique_values, get_duplicate_info, get_summary_statistics,
    get_correlation_matrix, get_column_info, get_numeric_columns,
    get_categorical_columns
)
from utils.helpers import format_file_size, format_number


def collect_report_data(force_regenerate: bool = False) -> Dict[str, Any]:
    """Collect all available dataset, cleaning, analysis, and session state data."""
    orig_df: Optional[pd.DataFrame] = st.session_state.get("original_df")
    cleaned_df: Optional[pd.DataFrame] = st.session_state.get("cleaned_df")
    working_df = cleaned_df if cleaned_df is not None else orig_df

    if working_df is None:
        return {}

    file_name = st.session_state.get("file_name", "Dataset")
    project_id = st.session_state.get("project_id", "default_project")
    project_name = st.session_state.get("project_name", file_name)
    upload_time = st.session_state.get("upload_time", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    cleaning_history = st.session_state.get("cleaning_history", [])
    cleaning_steps = st.session_state.get("cleaning_steps", [])
    activity_log = st.session_state.get("activity_log", [])

    # Calculate scores
    orig_quality = calculate_quality_score(orig_df) if orig_df is not None else {"total": 50}
    current_quality = calculate_quality_score(working_df)

    # Metadata summaries
    rows_orig = len(orig_df) if orig_df is not None else len(working_df)
    cols_orig = len(orig_df.columns) if orig_df is not None else len(working_df.columns)
    missing_orig = int(orig_df.isnull().sum().sum()) if orig_df is not None else 0
    dups_orig = int(orig_df.duplicated().sum()) if orig_df is not None else 0
    mem_orig = orig_df.memory_usage(deep=True).sum() if orig_df is not None else 0

    rows_curr = len(working_df)
    cols_curr = len(working_df.columns)
    missing_curr = int(working_df.isnull().sum().sum())
    dups_curr = int(working_df.duplicated().sum())
    mem_curr = working_df.memory_usage(deep=True).sum()

    num_cols = get_numeric_columns(working_df)
    cat_cols = get_categorical_columns(working_df)
    date_cols = [col for col in working_df.columns if pd.api.types.is_datetime64_any_dtype(working_df[col])]

    # Column breakdown
    col_info = get_column_info(working_df)

    # Missing value details
    missing_df = get_missing_values(working_df)

    # Statistical summary
    stats_df = get_summary_statistics(working_df)

    # Correlations
    corr_df = get_correlation_matrix(working_df)
    top_corrs = []
    if not corr_df.empty:
        for i in range(len(corr_df.columns)):
            for j in range(i + 1, len(corr_df.columns)):
                c1, c2 = corr_df.columns[i], corr_df.columns[j]
                val = corr_df.iloc[i, j]
                if not pd.isna(val) and abs(val) > 0.3:
                    top_corrs.append({"col1": c1, "col2": c2, "val": round(float(val), 3)})
        top_corrs.sort(key=lambda x: abs(x["val"]), reverse=True)

    # Outliers summary
    outlier_summary = []
    for col in num_cols:
        series = working_df[col].dropna()
        if len(series) > 0:
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            if iqr > 0:
                outliers = series[(series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)]
                if len(outliers) > 0:
                    outlier_summary.append({
                        "column": col,
                        "count": len(outliers),
                        "pct": round(len(outliers) / len(series) * 100, 2),
                        "min_extreme": float(outliers.min()),
                        "max_extreme": float(outliers.max())
                    })

    # High cardinality check
    high_card_cols = []
    for col in cat_cols:
        n_uniq = working_df[col].nunique()
        if n_uniq > 20:
            high_card_cols.append({"column": col, "unique": n_uniq})

    report_data = {
        "project_id": project_id,
        "project_name": project_name,
        "file_name": file_name,
        "upload_time": upload_time,
        "report_date": datetime.datetime.now().strftime("%B %d, %Y"),
        "report_timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        
        # Datasets reference
        "original_df": orig_df,
        "cleaned_df": cleaned_df,
        "working_df": working_df,
        "is_cleaned": cleaned_df is not None,

        # Metrics comparison
        "rows_orig": rows_orig,
        "cols_orig": cols_orig,
        "missing_orig": missing_orig,
        "dups_orig": dups_orig,
        "mem_orig": mem_orig,
        "quality_orig": orig_quality.get("total", 50),

        "rows_curr": rows_curr,
        "cols_curr": cols_curr,
        "missing_curr": missing_curr,
        "dups_curr": dups_curr,
        "mem_curr": mem_curr,
        "quality_curr": current_quality.get("total", 50),
        "quality_dict": current_quality,

        # Deltas
        "rows_delta": rows_curr - rows_orig,
        "cols_delta": cols_curr - cols_orig,
        "missing_delta": missing_curr - missing_orig,
        "dups_delta": dups_curr - dups_orig,
        "quality_delta": current_quality.get("total", 50) - orig_quality.get("total", 50),

        # Column breakdown
        "num_cols": num_cols,
        "cat_cols": cat_cols,
        "date_cols": date_cols,
        "col_info": col_info,
        "missing_df": missing_df,
        "stats_df": stats_df,

        # Correlations & Outliers
        "corr_df": corr_df,
        "top_corrs": top_corrs[:8],
        "outliers": outlier_summary,
        "high_cardinality": high_card_cols,

        # Cleaning logs
        "cleaning_history": cleaning_history,
        "cleaning_steps": cleaning_steps,
        "activity_log": activity_log,
    }

    # Fetch or generate AI Report Package
    import importlib
    import ai.report_agent
    importlib.reload(ai.report_agent)
    from ai.report_agent import ReportAgent
    from ai.gemini_manager import is_gemini_configured

    cache_key = f"cached_ai_report_{project_id}_{current_quality.get('total', 50)}_{len(cleaning_steps)}"
    
    ai_package = None
    if not force_regenerate and st.session_state.get(cache_key):
        ai_package = st.session_state[cache_key]

    if not ai_package:
        if is_gemini_configured():
            ai_package = ReportAgent.generate_ai_report(report_data)
            if ai_package:
                ai_package["is_ai_generated"] = True

        if not ai_package:
            ai_package = ReportAgent.generate_fallback_report(report_data)
            ai_package["is_ai_generated"] = False

        st.session_state[cache_key] = ai_package

    report_data["executive_summary_text"] = ai_package.get("executive_summary", "")
    report_data["business_insights"] = ai_package.get("business_insights", [])
    report_data["recommendations"] = ai_package.get("recommendations", [])
    report_data["executive_conclusion"] = ai_package.get("executive_conclusion", "")
    report_data["risk_assessment"] = ai_package.get("risk_assessment", [])
    report_data["opportunities"] = ai_package.get("opportunities", [])
    report_data["ai_confidence"] = ai_package.get("ai_confidence", {"score": 90, "level": "High", "reason": "Statistical profiling."})
    report_data["is_ai_generated"] = ai_package.get("is_ai_generated", False)

    return report_data


def generate_executive_summary(data: Dict[str, Any]) -> str:
    """Generate a professional natural-language executive summary paragraph."""
    file_name = data.get("file_name", "the dataset")
    rows = data.get("rows_curr", 0)
    cols = data.get("cols_curr", 0)
    q_orig = data.get("quality_orig", 50)
    q_curr = data.get("quality_curr", 50)
    dups_removed = abs(data.get("dups_delta", 0))
    missing_resolved = abs(data.get("missing_delta", 0))
    steps_count = len(data.get("cleaning_steps", []))

    summary = (
        f"This executive report provides a comprehensive evaluation of the <b>{file_name}</b> dataset, "
        f"comprising <b>{rows:,}</b> records and <b>{cols}</b> columns. "
    )

    if data.get("is_cleaned") or steps_count > 0:
        summary += (
            f"Through automated and interactive data cleaning ({steps_count} operations applied), "
            f"data quality improved from <b>{q_orig}%</b> to <b>{q_curr}%</b>. "
            f"Deduplication resolved <b>{dups_removed:,}</b> duplicate records and <b>{missing_resolved:,}</b> missing cells were imputed or removed. "
        )
    else:
        summary += (
            f"The dataset maintains an overall data health score of <b>{q_curr}%</b>. "
        )

    num_cnt = len(data.get("num_cols", []))
    cat_cnt = len(data.get("cat_cols", []))
    summary += (
        f"Statistical analysis identified <b>{num_cnt}</b> numeric dimensions and <b>{cat_cnt}</b> categorical features. "
    )

    outliers_cnt = sum([o["count"] for o in data.get("outliers", [])])
    if outliers_cnt > 0:
        summary += f"Outlier profiling detected <b>{outliers_cnt:,}</b> extreme values across key variables. "

    if q_curr >= 80:
        summary += "Overall dataset health is <b>excellent</b> and fully prepared for downstream reporting, executive visualization, and predictive AI modeling."
    elif q_curr >= 60:
        summary += "Overall dataset health is <b>good</b>, though minor feature engineering and imputation steps are recommended before advanced modeling."
    else:
        summary += "The dataset requires additional cleaning and normalization before deployment to production business intelligence dashboards."

    return summary


def generate_business_insights_list(data: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate 10–15 structured business insights with icons, titles, and metrics."""
    insights = []
    df = data.get("working_df")
    if df is None:
        return insights

    rows = data.get("rows_curr", 0)
    cols = data.get("cols_curr", 0)
    num_cols = data.get("num_cols", [])
    cat_cols = data.get("cat_cols", [])
    top_corrs = data.get("top_corrs", [])
    outliers = data.get("outliers", [])
    q_score = data.get("quality_curr", 50)

    # 1. Dataset Scale
    insights.append({
        "icon": "📊",
        "title": "Dataset Volume & Scope",
        "desc": f"The dataset encapsulates <b>{rows:,} rows</b> across <b>{cols} dimensions</b>, establishing a robust sample size for statistical analysis.",
        "category": "Volume"
    })

    # 2. Quality Health
    status_label = "Excellent" if q_score >= 80 else "Moderate" if q_score >= 50 else "Critical"
    insights.append({
        "icon": "🎯",
        "title": "Data Quality Health Index",
        "desc": f"Overall quality score is calculated at <b>{q_score}% ({status_label})</b>, accounting for completeness, uniqueness, and format consistency.",
        "category": "Quality"
    })

    # 3. Numeric Highlights
    for col in num_cols[:3]:
        series = df[col].dropna()
        if len(series) > 0:
            mean_val = series.mean()
            median_val = series.median()
            std_val = series.std()
            insights.append({
                "icon": "📈",
                "title": f"Distribution Profile: {col}",
                "desc": f"Column <b>{col}</b> displays a mean of <b>{mean_val:,.2f}</b> (median: <b>{median_val:,.2f}</b>, std: <b>{std_val:,.2f}</b>).",
                "category": "Distribution"
            })

    # 4. Top Correlations
    for corr in top_corrs[:3]:
        c1, c2, val = corr["col1"], corr["col2"], corr["val"]
        direction = "positive" if val > 0 else "negative"
        strength = "strong" if abs(val) > 0.7 else "moderate"
        insights.append({
            "icon": "🔗",
            "title": f"Feature Correlation ({c1} & {c2})",
            "desc": f"A <b>{strength} {direction} correlation of {val:+.2f}</b> exists between <b>{c1}</b> and <b>{c2}</b>, indicating strong co-dependency.",
            "category": "Relationships"
        })

    # 5. Outliers
    if outliers:
        top_o = outliers[0]
        insights.append({
            "icon": "🚨",
            "title": f"Outlier Concentration in {top_o['column']}",
            "desc": f"Detected <b>{top_o['count']:,} outliers ({top_o['pct']}%)</b> in <b>{top_o['column']}</b> ranging between {top_o['min_extreme']:,.2f} and {top_o['max_extreme']:,.2f}.",
            "category": "Outliers"
        })

    # 6. Categorical Dominance
    for col in cat_cols[:3]:
        counts = df[col].value_counts()
        if not counts.empty:
            top_cat = counts.index[0]
            top_cnt = counts.iloc[0]
            pct = top_cnt / len(df) * 100
            insights.append({
                "icon": "🏷️",
                "title": f"Category Dominance in {col}",
                "desc": f"Category <b>'{top_cat}'</b> represents the largest share in <b>{col}</b> with <b>{top_cnt:,} records ({pct:.1f}%)</b>.",
                "category": "Categorical"
            })

    # 7. Memory Footprint
    mem_mb = data.get("mem_curr", 0) / (1024 * 1024)
    insights.append({
        "icon": "💾",
        "title": "System Memory Footprint",
        "desc": f"In-memory processing size is <b>{mem_mb:.2f} MB</b>, allowing high-performance real-time analysis.",
        "category": "Performance"
    })

    return insights


def generate_recommendations_list(data: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate prioritized actionable recommendations."""
    recs = []
    q_dict = data.get("quality_dict", {})
    missing_curr = data.get("missing_curr", 0)
    dups_curr = data.get("dups_curr", 0)
    outliers = data.get("outliers", [])
    high_card = data.get("high_cardinality", [])

    if missing_curr > 0:
        recs.append({
            "title": "Impute Missing Values",
            "desc": f"Resolve <b>{missing_curr:,} remaining missing cells</b> using median/mode imputation to avoid bias in machine learning models.",
            "type": "Data Quality",
            "priority": "High"
        })

    if dups_curr > 0:
        recs.append({
            "title": "Remove Duplicate Rows",
            "desc": f"Deduplicate <b>{dups_curr:,} exact row duplicates</b> to ensure accurate aggregations and counts.",
            "type": "Data Cleaning",
            "priority": "High"
        })

    if outliers:
        recs.append({
            "title": "Cap or Winsorize Extreme Outliers",
            "desc": f"Apply IQR percentile capping on <b>{len(outliers)} columns</b> with extreme value distributions before regression modeling.",
            "type": "Statistics",
            "priority": "Medium"
        })

    if high_card:
        recs.append({
            "title": "Group High Cardinality Categories",
            "desc": f"Columns like <b>{high_card[0]['column']}</b> have {high_card[0]['unique']} unique categories. Group rare values into an 'Other' bucket.",
            "type": "Feature Engineering",
            "priority": "Medium"
        })

    recs.append({
        "title": "Standardize Column Dtypes",
        "desc": "Ensure date/time columns are explicitly cast to DateTime objects to enable time-series decomposition.",
        "type": "Data Pipeline",
        "priority": "Low"
    })

    recs.append({
        "title": "Automate Data Quality Checks",
        "desc": "Establish continuous automated validation pipelines to verify incoming datasets against Data Pilot quality standards.",
        "type": "Governance",
        "priority": "Low"
    })

    return recs


def calculate_report_quality_score(config: Dict[str, Any], report_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate Report Quality Score (0–100%) based on sections, insights, charts, and branding."""
    score = 0
    factors = []

    sections = config.get("sections", [])
    enabled_count = len(sections)

    # 1. Section Coverage (up to 40 pts)
    sect_score = min(40, int(enabled_count * 4))
    score += sect_score
    factors.append({"name": "Section Coverage", "score": sect_score, "max": 40})

    # 2. Insights & Data Presence (up to 30 pts)
    insights_cnt = len(report_data.get("business_insights", []))
    data_score = min(30, int(insights_cnt * 2.5))
    score += data_score
    factors.append({"name": "Insights & Intelligence", "score": data_score, "max": 30})

    # 3. Branding Completeness (up to 15 pts)
    branding_score = 0
    if config.get("company_name"):
        branding_score += 5
    if config.get("author"):
        branding_score += 5
    if config.get("title"):
        branding_score += 5
    score += branding_score
    factors.append({"name": "Executive Branding", "score": branding_score, "max": 15})

    # 4. Cleaning & Pipeline Completeness (up to 15 pts)
    q_score = report_data.get("quality_curr", 50)
    cleaning_pts = int(q_score * 0.15)
    score += cleaning_pts
    factors.append({"name": "Dataset Readiness", "score": cleaning_pts, "max": 15})

    total_score = min(100, score)
    status = "Executive Grade" if total_score >= 85 else "Standard Report" if total_score >= 65 else "Draft Report"

    return {
        "score": total_score,
        "status": status,
        "factors": factors
    }
