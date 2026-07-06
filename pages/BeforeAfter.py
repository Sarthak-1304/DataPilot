"""
Before vs After Page
====================
Side-by-side comparison of original and cleaned datasets.
"""

import streamlit as st
import pandas as pd
import numpy as np
import io
import plotly.graph_objects as go
from utils.cleaner import calculate_quality_score


def _score_color(score: int) -> str:
    if score >= 90:
        return "#10B981"  # green
    elif score >= 75:
        return "#3B82F6"  # blue
    elif score >= 55:
        return "#F59E0B"  # orange
    return "#EF4444"  # red


def get_health_status(score):
    if score >= 95:
        return "✅ Production Ready", "badge-green"
    elif score >= 85:
        return "✨ Excellent Health", "badge-green"
    elif score >= 70:
        return "🟡 Good Health", "badge-blue"
    elif score >= 50:
        return "⚠️ Needs Review", "badge-orange"
    else:
        return "🚨 Poor Health", "badge-red"


def count_outliers(df):
    num_cols = df.select_dtypes(include=np.number).columns
    total = 0
    for c in num_cols:
        q1 = df[c].quantile(0.25)
        q3 = df[c].quantile(0.75)
        iqr = q3 - q1
        if iqr > 0:
            total += ((df[c] < q1 - 1.5 * iqr) | (df[c] > q3 + 1.5 * iqr)).sum()
    return int(total)


def render_impact_metric_card(icon, label, value, pct, desc, color_class):
    st.markdown(
        f"""
        <div class="metric-card {color_class} animate-in" style="margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <span style="font-size: 1.5rem;">{icon}</span>
                <span class="badge badge-{color_class}">{pct:.0f}%</span>
            </div>
            <div class="metric-value" style="margin-top: 0.5rem; font-size: 1.6rem;">{value}</div>
            <div class="metric-label" style="font-size: 0.78rem; font-weight: 600; color: var(--text-primary);">{label}</div>
            <div style="font-size: 0.72rem; color: var(--text-secondary); margin-top: 0.2rem;">{desc}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_kpi_comparison_card(icon, label, orig_val, clean_val, direction="lower_better"):
    try:
        delta = clean_val - orig_val
    except:
        delta = 0

    if delta == 0:
        delta_text = "No change"
        delta_class = "badge-blue"
        arrow = "🔵"
    elif direction == "lower_better":
        if delta < 0:
            delta_text = f"↓ {abs(delta):,}"
            delta_class = "badge-green"
            arrow = "🟢"
        else:
            delta_text = f"↑ {abs(delta):,}"
            delta_class = "badge-red"
            arrow = "🔴"
    else:  # higher_better
        if delta > 0:
            delta_text = f"↑ {abs(delta):,}"
            delta_class = "badge-green"
            arrow = "🟢"
        else:
            delta_text = f"↓ {abs(delta):,}"
            delta_class = "badge-red"
            arrow = "🔴"

    orig_str = f"{orig_val:,}" if isinstance(orig_val, (int, float)) else str(orig_val)
    clean_str = f"{clean_val:,}" if isinstance(clean_val, (int, float)) else str(clean_val)

    st.markdown(
        f"""
        <div class="metric-card blue animate-in">
            <span class="metric-icon">{icon}</span>
            <div style="font-size: 0.8rem; color: var(--text-secondary); text-transform: uppercase; font-weight: 600;">{label}</div>
            <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 0.5rem;">
                <div style="font-size: 1.35rem; font-weight: 700; color: var(--text-secondary);">{orig_str}</div>
                <div style="font-size: 1.1rem; color: var(--text-muted);">➔</div>
                <div style="font-size: 1.6rem; font-weight: 800; color: var(--text-primary);">{clean_str}</div>
            </div>
            <div style="margin-top: 0.5rem; display: flex; justify-content: space-between; align-items: center;">
                <span class="badge {delta_class}">{delta_text}</span>
                <span>{arrow}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


@st.cache_data
def convert_df_to_excel(original_df, cleaned_df, steps):
    output = io.BytesIO()
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Summary Sheet
            summary_data = {
                "Metric": ["Original Rows", "Cleaned Rows", "Original Columns", "Cleaned Columns", "Original Score", "Cleaned Score"],
                "Value": [len(original_df), len(cleaned_df), len(original_df.columns), len(cleaned_df.columns), calculate_quality_score(original_df)["total"], calculate_quality_score(cleaned_df)["total"]]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary", index=False)
            
            # Log Sheet
            log_data = [{"Timestamp": s.get("timestamp", ""), "Step": s["step"]} for s in steps]
            if log_data:
                pd.DataFrame(log_data).to_excel(writer, sheet_name="Cleaning Log", index=False)
                
            original_df.head(10000).to_excel(writer, sheet_name="Original Data", index=False)
            cleaned_df.head(10000).to_excel(writer, sheet_name="Cleaned Data", index=False)
    except Exception:
        return None
    return output.getvalue()


def render_before_after():
    """Render the Before vs After comparison page."""
    st.markdown(
        """
        <div class="top-header">
            <h2>🔄 Before vs After Comparison</h2>
            <p>Review the effects of your cleaning pipeline. Observe how the dataset size, data quality score, missing values, duplicates, and schema changed.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.get("original_df") is None:
        st.markdown(
            """
            <div class="content-card animate-in">
                <div class="empty-state">
                    <div class="empty-icon">🔄</div>
                    <h3>No Dataset Loaded</h3>
                    <p>Upload a CSV or Excel file first to view the Before vs After comparison here.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    original_df = st.session_state["original_df"]
    cleaned_df = st.session_state.get("cleaned_df", original_df)
    steps = st.session_state.get("cleaning_steps", [])

    # Initialize variables to avoid UnboundLocalErrors when no steps are applied yet
    has_dtype_change = False
    has_text_change = False
    has_col_change = False
    rename_count = 0

    # Basic calculations
    rows_orig = len(original_df)
    rows_clean = len(cleaned_df)
    cols_orig = len(original_df.columns)
    cols_clean = len(cleaned_df.columns)
    
    missing_orig = int(original_df.isnull().sum().sum())
    missing_clean = int(cleaned_df.isnull().sum().sum())
    missing_fixed = max(0, missing_orig - missing_clean)
    
    dup_orig = int(original_df.duplicated().sum())
    dup_clean = int(cleaned_df.duplicated().sum())
    dup_removed = max(0, dup_orig - dup_clean)
    
    out_orig = count_outliers(original_df)
    out_clean = count_outliers(cleaned_df)
    out_removed = max(0, out_orig - out_clean)

    score_info_orig = calculate_quality_score(original_df)
    score_info_clean = calculate_quality_score(cleaned_df)
    score_orig = score_info_orig["total"]
    score_clean = score_info_clean["total"]

    # --- SECTION 1: CLEANING IMPACT DASHBOARD ---
    st.markdown("### 📊 1. Cleaning Impact Dashboard")
    
    # Calculate impact score
    if not steps:
        impact_score = 0
        impact_label = "No Changes"
    else:
        dup_score = 100.0 if dup_orig == 0 else (dup_removed / dup_orig) * 100.0
        missing_score = 100.0 if missing_orig == 0 else (missing_fixed / missing_orig) * 100.0
        outlier_score = 100.0 if out_orig == 0 else (out_removed / out_orig) * 100.0
        
        common_cols = [c for c in original_df.columns if c in cleaned_df.columns]
        has_dtype_change = any(original_df[c].dtype != cleaned_df[c].dtype for c in common_cols)
        if has_dtype_change or any("dtype" in s["step"].lower() or "type" in s["step"].lower() for s in steps):
            dtype_score = 100.0
        else:
            dtype_score = 100.0 if score_info_orig["consistency"] >= 19.0 else 0.0
            
        has_text_change = any("text" in s["step"].lower() or "standard" in s["step"].lower() or "case" in s["step"].lower() or "trim" in s["step"].lower() for s in steps)
        if has_text_change:
            text_score = 100.0
        else:
            text_score = 100.0 if score_info_orig["naming"] >= 9.5 else 50.0
            
        has_col_change = any("drop" in s["step"].lower() or "remove" in s["step"].lower() or "constant" in s["step"].lower() or "highly missing" in s["step"].lower() for s in steps)
        if has_col_change or len(original_df.columns) != len(cleaned_df.columns):
            col_score = 100.0
        else:
            col_score = 100.0 if score_info_orig["validity"] >= 19.5 else 75.0
            
        impact_score = int(
            dup_score * 0.20 + 
            missing_score * 0.30 + 
            outlier_score * 0.20 + 
            dtype_score * 0.10 + 
            text_score * 0.10 + 
            col_score * 0.10
        )
        impact_score = max(0, min(100, impact_score))

    if impact_score >= 85:
        impact_label = "Excellent"
    elif impact_score >= 70:
        impact_label = "Good"
    elif impact_score >= 50:
        impact_label = "Average"
    else:
        impact_label = "Poor"

    # Display impact indicators
    hero1, hero2 = st.columns([1, 2])
    with hero1:
        st.markdown(
            f"""
            <div class="content-card animate-in" style="height: 100%; text-align: center; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 2rem;">
                <div style="font-size: 0.95rem; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em;">Overall Cleaning Impact</div>
                <div style="font-size: 3.5rem; font-weight: 800; color: #3B82F6; margin: 0.8rem 0; line-height: 1;">{impact_score}%</div>
                <div class="badge badge-blue" style="font-size: 0.9rem; padding: 0.4rem 1rem;">{impact_label}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with hero2:
        st.markdown(
            """
            <div class="content-card animate-in" style="height: 100%;">
                <h3 style="margin-top: 0;">🎯 Data Quality Improvement</h3>
            """,
            unsafe_allow_html=True
        )
        
        c_orig_color = _score_color(score_orig)
        c_clean_color = _score_color(score_clean)
        diff_score = score_clean - score_orig
        diff_sign = "+" if diff_score >= 0 else ""
        diff_class = "badge-green" if diff_score >= 0 else "badge-red"

        st.markdown(
            f"""
            <div style="display: flex; align-items: center; justify-content: space-around; padding: 1rem 0;">
                <div style="text-align: center;">
                    <div style="font-size: 0.8rem; color: var(--text-secondary); text-transform: uppercase; font-weight: 600;">Before Quality</div>
                    <div style="font-size: 2.2rem; font-weight: 800; color: {c_orig_color};">{score_orig}%</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted); font-weight: 500;">{score_info_orig['label']}</div>
                </div>
                <div style="font-size: 2rem; color: var(--text-muted);">➔</div>
                <div style="text-align: center;">
                    <div style="font-size: 0.8rem; color: var(--text-secondary); text-transform: uppercase; font-weight: 600;">After Quality</div>
                    <div style="font-size: 2.5rem; font-weight: 800; color: {c_clean_color};">{score_clean}%</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted); font-weight: 500;">{score_info_clean['label']}</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 0.8rem; color: var(--text-secondary); text-transform: uppercase; font-weight: 600;">Improvement</div>
                    <div style="font-size: 2.2rem; font-weight: 800; color: #10B981;"><span class="badge {diff_class}" style="font-size: 1.5rem; padding: 0.2rem 0.8rem;">{diff_sign}{diff_score}%</span></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # 1.2 Cleaning Metrics Cards Grid
    st.markdown("#### Detailed Cleaning Metrics")
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        render_impact_metric_card("🗑️", "Duplicates Removed", f"{dup_removed:,}", 100.0 if dup_orig == 0 else (dup_removed/dup_orig)*100.0, "Duplicate rows deleted", "red")
    with m_col2:
        render_impact_metric_card("🩹", "Missing Values Fixed", f"{missing_fixed:,}", 100.0 if missing_orig == 0 else (missing_fixed/missing_orig)*100.0, "Null fields filled", "orange")
    with m_col3:
        render_impact_metric_card("📉", "Outliers Handled", f"{out_removed:,}", 100.0 if out_orig == 0 else (out_removed/out_orig)*100.0, "Statistical outliers capped", "purple")
    with m_col4:
        rename_count = sum(1 for s in steps if "rename" in s["step"].lower())
        col_opt_val = len(original_df.columns) - len(cleaned_df.columns)
        render_impact_metric_card("🗂️", "Columns Dropped/Renamed", f"{col_opt_val} / {rename_count}", 100.0, "Schema changes completed", "blue")

    # 1.3 Health & Efficiency & AI Readiness
    st.markdown("<br>", unsafe_allow_html=True)
    eff1, eff2, eff3 = st.columns(3)
    
    with eff1:
        st.markdown(
            """
            <div class="content-card animate-in" style="height: 100%;">
                <h3>🩺 Dataset Health Status</h3>
            """,
            unsafe_allow_html=True
        )
        h_before_lbl, h_before_cls = get_health_status(score_orig)
        h_after_lbl, h_after_cls = get_health_status(score_clean)
        st.markdown(
            f"""
            <div style="display: flex; flex-direction: column; gap: 1rem; padding: 0.5rem 0;">
                <div>
                    <span style="font-size: 0.8rem; font-weight: 600; color: var(--text-secondary);">BEFORE CLEANING</span>
                    <div style="margin-top: 0.2rem;"><span class="badge {h_before_cls}" style="font-size: 0.9rem; padding: 0.35rem 0.75rem;">{h_before_lbl}</span></div>
                </div>
                <div style="border-top: 1px solid var(--border-color); padding-top: 0.8rem;">
                    <span style="font-size: 0.8rem; font-weight: 600; color: var(--text-secondary);">AFTER CLEANING</span>
                    <div style="margin-top: 0.2rem;"><span class="badge {h_after_cls}" style="font-size: 1rem; padding: 0.4rem 0.9rem;">{h_after_lbl}</span></div>
                </div>
            </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with eff2:
        # Align indexes and count cells modified
        common_idx = original_df.index.intersection(cleaned_df.index)
        orig_shared = original_df.loc[common_idx]
        clean_shared = cleaned_df.loc[common_idx]
        common_cols = [c for c in original_df.columns if c in cleaned_df.columns]
        
        cells_modified = 0
        rows_updated_set = set()
        for col in common_cols:
            s_orig = orig_shared[col]
            s_clean = clean_shared[col]
            diff_mask = (s_orig != s_clean) | (s_orig.isna() != s_clean.isna())
            cells_modified += diff_mask.sum()
            rows_updated_set.update(orig_shared[diff_mask].index)
        rows_updated = len(rows_updated_set)

        st.markdown(
            f"""
            <div class="content-card animate-in" style="height: 100%;">
                <h3>⏱️ Cleaning Efficiency</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; font-size: 0.82rem; color: var(--text-secondary);">
                    <div>
                        <div style="font-weight: 600; color: var(--text-primary); font-size: 1.15rem;">{max(0, rows_orig - rows_clean):,}</div>
                        <div>Rows Removed</div>
                    </div>
                    <div>
                        <div style="font-weight: 600; color: var(--text-primary); font-size: 1.15rem;">{rows_updated:,}</div>
                        <div>Rows Updated</div>
                    </div>
                    <div>
                        <div style="font-weight: 600; color: var(--text-primary); font-size: 1.15rem;">{cells_modified:,}</div>
                        <div>Cells Modified</div>
                    </div>
                    <div>
                        <div style="font-weight: 600; color: var(--text-primary); font-size: 1.15rem;">{len(steps):,}</div>
                        <div>Operations Applied</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with eff3:
        # Dataset Readiness
        chk_miss = missing_clean == 0
        chk_dup = dup_clean == 0
        chk_dtype = has_dtype_change or any("dtype" in s["step"].lower() or "type" in s["step"].lower() for s in steps) or score_info_clean["consistency"] >= 18.0
        chk_text = has_text_change or score_info_clean["naming"] >= 9.5
        chk_out = out_clean <= (0.05 * len(cleaned_df))
        chk_quality = score_clean >= 85

        checks = [chk_miss, chk_dup, chk_dtype, chk_text, chk_out, chk_quality]
        readiness_score = int((sum(checks) / len(checks)) * 100)
        readiness_lbl = "🟢 Ready for Export" if readiness_score >= 90 else "🟡 Partially Ready" if readiness_score >= 70 else "🔴 Needs Review"
        
        st.markdown(
            f"""
            <div class="content-card animate-in" style="height: 100%;">
                <h3>⚙️ Dataset Readiness Score</h3>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                    <span style="font-size: 1.6rem; font-weight: 800; color: var(--text-primary);">{readiness_score}%</span>
                    <span class="badge badge-green">{readiness_lbl}</span>
                </div>
                <div style="font-size: 0.76rem; color: var(--text-secondary); line-height: 1.35; padding-top: 0.2rem;">
                    {"✔" if chk_miss else "✖"} Missing values resolved<br>
                    {"✔" if chk_dup else "✖"} Duplicate records removed<br>
                    {"✔" if chk_dtype else "✖"} Datatypes corrected<br>
                    {"✔" if chk_text else "✖"} Text formatted & standardized<br>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # --- SECTION 2: BEFORE vs AFTER KPI SUMMARY ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📊 2. Before vs After KPI Summary")
    
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1:
        render_kpi_comparison_card("📐", "Rows", rows_orig, rows_clean, direction="higher_better")
    with k2:
        render_kpi_comparison_card("🗂️", "Columns", cols_orig, cols_clean, direction="higher_better")
    with k3:
        render_kpi_comparison_card("⚠️", "Missing Values", missing_orig, missing_clean, direction="lower_better")
    with k4:
        render_kpi_comparison_card("👥", "Duplicates", dup_orig, dup_clean, direction="lower_better")
    with k5:
        render_kpi_comparison_card("📉", "Outliers", out_orig, out_clean, direction="lower_better")
    with k6:
        orig_mem = round(original_df.memory_usage(deep=True).sum() / (1024 * 1024), 2)
        clean_mem = round(cleaned_df.memory_usage(deep=True).sum() / (1024 * 1024), 2)
        render_kpi_comparison_card("💾", "Memory (MB)", orig_mem, clean_mem, direction="lower_better")

    # --- SECTION 3: EXECUTIVE CLEANING SUMMARY ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### ✍️ 3. Executive Cleaning Summary")
    st.markdown(
        """
        <div class="content-card animate-in">
            <h3 style="margin-top: 0; color: var(--text-primary);">📝 Executive Summary</h3>
        """,
        unsafe_allow_html=True
    )
    
    # Checklist generator
    bullets = []
    if dup_removed > 0:
        bullets.append(f"<li>Removed <b>{dup_removed:,}</b> duplicate rows to enforce uniqueness.</li>")
    if missing_fixed > 0:
        bullets.append(f"<li>Filled <b>{missing_fixed:,}</b> missing values, restoring complete data records.</li>")
    if out_removed > 0:
        bullets.append(f"<li>Addressed <b>{out_removed:,}</b> statistical outliers to prevent skewed analytical insights.</li>")
    if cols_orig != cols_clean:
        bullets.append(f"<li>Optimized dataset structure (from {cols_orig} columns to {cols_clean} columns).</li>")
    if rename_count > 0:
        bullets.append(f"<li>Renamed <b>{rename_count}</b> columns to fit clean standard headers.</li>")
    if has_dtype_change:
        bullets.append("<li>Corrected mismatched datatypes (parsed fields into appropriate Datetime or Numeric values).</li>")
    if has_text_change:
        bullets.append("<li>Standardized text styles and trimmed extra whitespaces across text fields.</li>")

    if not bullets:
        bullets.append("<li>No operations applied yet. Dataset remains in its original form.</li>")
        narrative = f"The dataset was analyzed and has an initial quality score of <b>{score_orig}%</b>. No cleaning actions have been executed yet."
    else:
        narrative = (
            f"The cleaning process successfully improved overall data quality from <b>{score_orig}%</b> to <b>{score_clean}%</b>. "
            f"Key operations included eliminating duplicate rows, resolving null values, and formatting structural inconsistencies. "
            f"The resulting dataset has been cleaned according to enterprise analytics standards and is fully optimized for business reporting, "
            f"interactive dashboards, and predictive ML modeling."
        )

    bullets_html = "\n".join(bullets)
    st.markdown(
        f"""
        <div style="font-size: 0.9rem; color: var(--text-primary); line-height: 1.6;">
            <p>{narrative}</p>
            <ul style="padding-left: 1.2rem; margin-top: 0.6rem; color: var(--text-secondary);">
                {bullets_html}
            </ul>
        </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- SECTION 4: SIDE BY SIDE DATASET COMPARISON ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📄 4. Side-by-Side Dataset Comparison")
    
    col_prev1, col_prev2 = st.columns(2)
    with col_prev1:
        st.markdown("<h4>Original Dataset (First 100 rows)</h4>", unsafe_allow_html=True)
        st.dataframe(original_df.head(100), use_container_width=True, height=350)
    with col_prev2:
        st.markdown("<h4>Cleaned Dataset (First 100 rows)</h4>", unsafe_allow_html=True)
        st.dataframe(cleaned_df.head(100), use_container_width=True, height=350)

    # --- SECTION 5: COLUMN COMPARISON ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📋 5. Column Comparison Matrix")
    
    dropped_cols = list(set(original_df.columns) - set(cleaned_df.columns))
    added_cols = list(set(cleaned_df.columns) - set(original_df.columns))
    all_cols = sorted(list(set(original_df.columns).union(set(cleaned_df.columns))))
    
    col_comp_data = []
    for col in all_cols:
        if col in dropped_cols:
            orig_dt = str(original_df[col].dtype)
            orig_miss = int(original_df[col].isnull().sum())
            orig_uniq = int(original_df[col].nunique())
            col_comp_data.append({
                "Column Name": col,
                "Datatype": f"{orig_dt} ➔ (Dropped)",
                "Missing Values": f"{orig_miss:,} ➔ -",
                "Unique Values": f"{orig_uniq:,} ➔ -",
                "Status": "❌ Dropped"
            })
        elif col in added_cols:
            clean_dt = str(cleaned_df[col].dtype)
            clean_miss = int(cleaned_df[col].isnull().sum())
            clean_uniq = int(cleaned_df[col].nunique())
            col_comp_data.append({
                "Column Name": col,
                "Datatype": f"- ➔ {clean_dt}",
                "Missing Values": f"- ➔ {clean_miss:,}",
                "Unique Values": f"- ➔ {clean_uniq:,}",
                "Status": "🆕 Added"
            })
        else:
            orig_dt = str(original_df[col].dtype)
            clean_dt = str(cleaned_df[col].dtype)
            orig_miss = int(original_df[col].isnull().sum())
            clean_miss = int(cleaned_df[col].isnull().sum())
            orig_uniq = int(original_df[col].nunique())
            clean_uniq = int(cleaned_df[col].nunique())
            
            dt_changed = orig_dt != clean_dt
            miss_fixed = orig_miss > clean_miss
            uniq_changed = orig_uniq != clean_uniq
            
            status = "✨ Improved" if (dt_changed or miss_fixed or (orig_uniq > clean_uniq and orig_dt == "object")) else "⚪ Unchanged"
            
            dt_str = f"{orig_dt} ➔ {clean_dt}" if dt_changed else orig_dt
            miss_str = f"{orig_miss:,} ➔ {clean_miss:,}" if orig_miss != clean_miss else f"{orig_miss:,}"
            uniq_str = f"{orig_uniq:,} ➔ {clean_uniq:,}" if orig_uniq != clean_uniq else f"{orig_uniq:,}"
            
            col_comp_data.append({
                "Column Name": col,
                "Datatype": dt_str,
                "Missing Values": miss_str,
                "Unique Values": uniq_str,
                "Status": status
            })

    col_comp_df = pd.DataFrame(col_comp_data)
    st.dataframe(col_comp_df, use_container_width=True, hide_index=True)

    # --- SECTION 6: VISUAL COMPARISONS ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📈 6. Visual Comparisons")
    
    tab_charts, tab_dist, tab_out, tab_text = st.tabs([
        "📊 Overall Health Charts", "📐 Numeric Distribution", "📦 Outlier Boxplots", "🔤 Text Standardizations"
    ])
    
    with tab_charts:
        # Plotly comparison charts
        c_left, c_right = st.columns(2)
        
        with c_left:
            # Missing values chart
            miss_orig_dict = original_df.isnull().sum().to_dict()
            miss_clean_dict = cleaned_df.isnull().sum().to_dict()
            c_names = sorted(list(set(miss_orig_dict.keys()).union(set(miss_clean_dict.keys()))))
            y_orig = [miss_orig_dict.get(c, 0) for c in c_names]
            y_clean = [miss_clean_dict.get(c, 0) for c in c_names]
            
            fig_miss = go.Figure(data=[
                go.Bar(name='Original', x=c_names, y=y_orig, marker_color='#F59E0B'),
                go.Bar(name='Cleaned', x=c_names, y=y_clean, marker_color='#10B981')
            ])
            fig_miss.update_layout(
                title=dict(text="Missing Values per Column", font=dict(color="#0F172A", size=16)),
                font=dict(color="#334155", family="Inter, sans-serif"),
                barmode='group',
                height=260,
                margin=dict(l=10, r=10, t=40, b=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(gridcolor='#E2E8F0', tickfont=dict(color="#475569")),
                xaxis=dict(tickfont=dict(color="#475569")),
                legend=dict(font=dict(color="#475569"))
            )
            st.plotly_chart(fig_miss, use_container_width=True, config={'displayModeBar': False})
            
        with c_right:
            # Memory and Duplicates
            dup_chart = go.Figure(data=[
                go.Bar(name='Original', x=['Duplicates', 'Outliers'], y=[dup_orig, out_orig], marker_color='#EF4444'),
                go.Bar(name='Cleaned', x=['Duplicates', 'Outliers'], y=[dup_clean, out_clean], marker_color='#3B82F6')
            ])
            dup_chart.update_layout(
                title=dict(text="Duplicates & Outliers Count", font=dict(color="#0F172A", size=16)),
                font=dict(color="#334155", family="Inter, sans-serif"),
                barmode='group',
                height=260,
                margin=dict(l=10, r=10, t=40, b=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(gridcolor='#E2E8F0', tickfont=dict(color="#475569")),
                xaxis=dict(tickfont=dict(color="#475569")),
                legend=dict(font=dict(color="#475569"))
            )
            st.plotly_chart(dup_chart, use_container_width=True, config={'displayModeBar': False})

    with tab_dist:
        num_cols = original_df.select_dtypes(include=np.number).columns
        if not len(num_cols):
            st.info("No numeric columns available to display distribution charts.")
        else:
            selected_num_col = st.selectbox(
                "Select numeric column for distribution comparison:", 
                options=num_cols,
                key="num_dist_sel"
            )
            
            col_d1, col_d2 = st.columns([2, 1])
            with col_d1:
                # Plotly overlaid histograms
                fig_hist = go.Figure()
                fig_hist.add_trace(go.Histogram(x=original_df[selected_num_col], name='Original', marker_color='#94A3B8', opacity=0.6))
                if selected_num_col in cleaned_df.columns:
                    fig_hist.add_trace(go.Histogram(x=cleaned_df[selected_num_col], name='Cleaned', marker_color='#3B82F6', opacity=0.7))
                fig_hist.update_layout(
                    title=dict(text=f"Value Distribution: {selected_num_col}", font=dict(color="#0F172A", size=16)),
                    font=dict(color="#334155", family="Inter, sans-serif"),
                    barmode='overlay',
                    height=280,
                    showlegend=True,
                    margin=dict(l=10, r=10, t=40, b=10),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    yaxis=dict(gridcolor='#E2E8F0', tickfont=dict(color="#475569"), title_font=dict(color="#475569")),
                    xaxis=dict(tickfont=dict(color="#475569"), title_font=dict(color="#475569")),
                    legend=dict(font=dict(color="#475569"))
                )
                st.plotly_chart(fig_hist, use_container_width=True, config={'displayModeBar': False})
                
            with col_d2:
                # Stats calculation
                st.markdown("##### Descriptive Statistics")
                stats_rows = []
                for label, df_t in [("Before", original_df), ("After", cleaned_df)]:
                    if selected_num_col in df_t.columns:
                        col_s = df_t[selected_num_col]
                        stats_rows.append({
                            "Metric": label,
                            "Mean": round(col_s.mean(), 2) if col_s.notna().any() else 0,
                            "Median": round(col_s.median(), 2) if col_s.notna().any() else 0,
                            "Std Dev": round(col_s.std(), 2) if col_s.notna().any() else 0,
                            "Min": round(col_s.min(), 2) if col_s.notna().any() else 0,
                            "Max": round(col_s.max(), 2) if col_s.notna().any() else 0,
                        })
                st.dataframe(pd.DataFrame(stats_rows), use_container_width=True, hide_index=True)

    with tab_out:
        num_cols = original_df.select_dtypes(include=np.number).columns
        if not len(num_cols):
            st.info("No numeric columns available to display outlier boxplots.")
        else:
            selected_box_col = st.selectbox(
                "Select numeric column for boxplot comparison:", 
                options=num_cols,
                key="box_out_sel"
            )
            
            fig_box = go.Figure()
            fig_box.add_trace(go.Box(y=original_df[selected_box_col], name='Original', marker_color='#EF4444'))
            if selected_box_col in cleaned_df.columns:
                fig_box.add_trace(go.Box(y=cleaned_df[selected_box_col], name='Cleaned', marker_color='#10B981'))
            
            fig_box.update_layout(
                title=dict(text=f"Outlier Dispersion: {selected_box_col}", font=dict(color="#0F172A", size=16)),
                font=dict(color="#334155", family="Inter, sans-serif"),
                height=280,
                showlegend=True,
                margin=dict(l=10, r=10, t=40, b=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(gridcolor='#E2E8F0', tickfont=dict(color="#475569"), title_font=dict(color="#475569")),
                xaxis=dict(tickfont=dict(color="#475569"), title_font=dict(color="#475569")),
                legend=dict(font=dict(color="#475569"))
            )
            st.plotly_chart(fig_box, use_container_width=True, config={'displayModeBar': False})

    with tab_text:
        # Align on index to avoid shape mismatches
        common_idx = original_df.index.intersection(cleaned_df.index)
        orig_shared = original_df.loc[common_idx]
        clean_shared = cleaned_df.loc[common_idx]
        
        text_cols = orig_shared.select_dtypes(include="object").columns.intersection(clean_shared.select_dtypes(include="object").columns)
        
        text_examples = []
        for col in text_cols:
            mask = (orig_shared[col] != clean_shared[col]) & orig_shared[col].notna() & clean_shared[col].notna()
            diff_df = pd.DataFrame({"Before": orig_shared.loc[mask, col], "After": clean_shared.loc[mask, col]})
            if not diff_df.empty:
                transitions = diff_df.drop_duplicates().head(6)
                for _, row in transitions.iterrows():
                    text_examples.append({
                        "Column": col,
                        "Before Value": f'"{row["Before"]}"',
                        "After Value": f'"{row["After"]}"'
                    })
                    
        if not text_examples:
            st.markdown(
                """
                <div style="background-color: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 8px; padding: 1.2rem; text-align: center; margin: 1rem 0; color: #475569; font-size: 0.9rem;">
                    💡 No text standardization examples found in the modifications.
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown("##### Standardized Text Transitions")
            st.dataframe(pd.DataFrame(text_examples), use_container_width=True, hide_index=True)

    # --- SECTION 7: CLEANING TIMELINE ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🕒 7. Cleaning Timeline")
    
    if not steps:
        st.markdown(
            """
            <div class="activity-item animate-in">
                <div class="activity-dot" style="background: var(--warning-orange);"></div>
                <div style="flex-grow: 1;">
                    <div style="font-weight: 600; color: var(--text-primary);">Dataset Uploaded</div>
                    <div class="activity-time">No edits have been made yet.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        for idx, item in enumerate(steps):
            step_desc = item.get("step", "Cleaning Operation")
            step_time = item.get("timestamp", "")
            st.markdown(
                f"""
                <div class="activity-item animate-in">
                    <div class="activity-dot"></div>
                    <div style="flex-grow: 1;">
                        <span style="font-weight: 600; color: var(--text-primary);">{step_desc}</span>
                        <div class="activity-time">🕒 {step_time}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # --- SECTION 8: DOWNLOAD SECTION & SUCCESS BANNER ---
    st.markdown("<br>", unsafe_allow_html=True)
    if score_clean >= 90:
        st.markdown(
            """
            <div style="background-color: #ECFDF5; border: 1px solid #10B981; border-radius: 8px; padding: 1.2rem; margin-bottom: 1.5rem;">
                <h4 style="color: #065F46; margin: 0 0 0.4rem 0; font-weight: 700; border: none; padding: 0; display: flex; align-items: center; gap: 0.5rem;">
                    <span>✅</span> Dataset Successfully Cleaned
                </h4>
                <p style="color: #047857; margin: 0; font-size: 0.9rem; line-height: 1.5;">
                    The dataset is fully prepared and optimized. Ready for <b>Analysis, Dashboard, AI Insights,</b> and <b>Export</b>.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div style="background-color: #FFFBEB; border: 1px solid #F59E0B; border-radius: 8px; padding: 1.2rem; margin-bottom: 1.5rem;">
                <h4 style="color: #92400E; margin: 0 0 0.4rem 0; font-weight: 700; border: none; padding: 0; display: flex; align-items: center; gap: 0.5rem;">
                    <span>⚠️</span> Quality Issues Remaining
                </h4>
                <p style="color: #78350F; margin: 0; font-size: 0.9rem; line-height: 1.5;">
                    Dataset still contains quality issues. We recommend checking for additional outliers, missing fields, or datatype anomalies before final export.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("### 💾 8. Download Comparison Reports")
    d_col1, d_col2 = st.columns(2)
    
    with d_col1:
        excel_data = convert_df_to_excel(original_df, cleaned_df, steps)
        st.download_button(
            label="📊 Download Excel Comparison Report",
            data=excel_data if excel_data else b"",
            file_name="dataset_before_after_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            disabled=(excel_data is None),
            use_container_width=True
        )
        
    with d_col2:
        log_text = "\n".join(
            f"[{s.get('timestamp','')}] {s['step']}" for s in steps
        ) if steps else "No cleaning steps applied."
        st.download_button(
            label="📝 Download Cleaning Log File",
            data=log_text.encode("utf-8"),
            file_name="data_cleaning_log.txt",
            mime="text/plain",
            use_container_width=True
        )

    # --- SECTION 9: CONTINUE TO ANALYSIS ---
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➡ Continue to Analysis", type="primary", use_container_width=True):
        st.session_state["current_page"] = "Analysis"
        st.rerun()
