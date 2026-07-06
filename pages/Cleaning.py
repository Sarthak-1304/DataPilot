"""
Data Cleaning Page
==================
Interactive data cleaning with live preview, undo, history, and quality score.
"""

import streamlit as st
import pandas as pd
import io
from datetime import datetime

from utils.cleaner import (
    remove_duplicates, get_duplicate_count,
    fill_missing_numeric, fill_missing_categorical,
    change_dtype, rename_columns, drop_columns,
    standardize_text, replace_values,
    detect_outliers_iqr, detect_outliers_zscore,
    remove_outliers, cap_outliers,
    remove_null_rows,
    find_constant_columns, remove_constant_columns,
    find_highly_missing_columns, remove_highly_missing_columns,
    calculate_quality_score,
)
from utils.helpers import add_activity, format_number


# ─── Helpers ────────────────────────────────────────────────────────

def _alert(text: str, level: str = "warning"):
    """Render a beautiful, high-contrast custom alert banner."""
    if level == "warning":
        bg = "rgba(245, 158, 11, 0.08)"
        border = "#F59E0B"
        color = "#D97706"
        icon = "⚠️"
    elif level == "success":
        bg = "rgba(16, 185, 129, 0.08)"
        border = "#10B981"
        color = "#059669"
        icon = "✅"
    elif level == "info":
        bg = "rgba(59, 130, 246, 0.08)"
        border = "#3B82F6"
        color = "#2563EB"
        icon = "ℹ️"
    else:  # error
        bg = "rgba(220, 38, 38, 0.08)"
        border = "#DC2626"
        color = "#DC2626"
        icon = "❌"

    st.markdown(f"""
    <div style="background-color: {bg}; border: 1px solid {border}; padding: 0.65rem 0.95rem; border-radius: 8px; font-size: 0.85rem; margin-bottom: 1rem; font-weight: 500; display: flex; align-items: center; gap: 0.5rem; width: 100%;">
        <span style="font-size: 1.1rem; line-height: 1; color: {color};">{icon}</span>
        <span style="color: var(--text-primary);">{text}</span>
    </div>
    """, unsafe_allow_html=True)


def _wdf():
    """Return the current working DataFrame."""
    c = st.session_state.get("cleaned_df")
    return c if c is not None else st.session_state["original_df"]


def _apply(new_df, description):
    """Snapshot → update cleaned_df → log."""
    # Save undo snapshot
    history = st.session_state.setdefault("cleaning_history", [])
    history.append(st.session_state.get("cleaned_df",
                   st.session_state["original_df"]).copy())
    # Save step
    steps = st.session_state.setdefault("cleaning_steps", [])
    steps.append({"step": description,
                  "timestamp": datetime.now().strftime("%I:%M %p")})
    st.session_state["cleaned_df"] = new_df
    add_activity(description)


def _fmt(n):
    return f"{n:,}" if isinstance(n, int) else str(n)


# ─── Quality Score Gauge ────────────────────────────────────────────

def _render_quality_gauge(df):
    info = calculate_quality_score(df)
    score, label = info["total"], info["label"]
    if score >= 80:
        color = "#10B981"
    elif score >= 60:
        color = "#F59E0B"
    else:
        color = "#EF4444"

    st.markdown(f"""
    <div class="content-card" style="text-align:center;">
        <h3>🎯 Data Quality Score</h3>
        <div style="position:relative;width:140px;height:140px;margin:0.5rem auto;">
            <svg viewBox="0 0 36 36" style="transform:rotate(-90deg);width:100%;height:100%;">
                <path d="M18 2.0845a 15.9155 15.9155 0 0 1 0 31.831a 15.9155 15.9155 0 0 1 0 -31.831"
                      fill="none" stroke="#E2E8F0" stroke-width="3"/>
                <path d="M18 2.0845a 15.9155 15.9155 0 0 1 0 31.831a 15.9155 15.9155 0 0 1 0 -31.831"
                      fill="none" stroke="{color}" stroke-width="3"
                      stroke-dasharray="{score}, 100" stroke-linecap="round"/>
            </svg>
            <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
                        font-size:1.8rem;font-weight:800;color:{color};">{score}</div>
        </div>
        <div style="font-size:0.85rem;font-weight:600;color:{color};margin-top:0.2rem;">
            {label}
        </div>
        <div style="display:flex;flex-wrap:wrap;gap:0.4rem;justify-content:center;margin-top:0.8rem;">
            <span class="badge badge-green">Completeness {info['completeness']}/30</span>
            <span class="badge badge-blue">Uniqueness {info['uniqueness']}/20</span>
            <span class="badge badge-purple">Consistency {info['consistency']}/20</span>
        </div>
    </div>""", unsafe_allow_html=True)


# ─── Status Cards ───────────────────────────────────────────────────

def _render_status(df):
    total = df.shape[0] * df.shape[1]
    miss = int(df.isnull().sum().sum())
    miss_p = (miss / total * 100) if total else 0
    dups = get_duplicate_count(df)
    mem = df.memory_usage(deep=True).sum()
    mem_str = f"{mem/1024:.1f} KB" if mem < 1048576 else f"{mem/1048576:.1f} MB"
    dtypes = str(df.dtypes.nunique())
    score = calculate_quality_score(df)["total"]

    items = [
        ("📋", f"{df.shape[0]:,}", "Rows", "blue"),
        ("📐", str(df.shape[1]), "Columns", "green"),
        ("⚠️", _fmt(miss), f"Missing ({miss_p:.1f}%)", "orange"),
        ("🔁", _fmt(dups), "Duplicates", "red"),
        ("🔤", dtypes, "Data Types", "purple"),
        ("💾", mem_str, "Memory", "blue"),
        ("🎯", str(score), "Quality", "green"),
    ]
    cols = st.columns(len(items))
    for col, (icon, val, lbl, accent) in zip(cols, items):
        with col:
            st.markdown(f"""
            <div class="metric-card {accent}">
                <div class="metric-icon">{icon}</div>
                <div class="metric-value">{val}</div>
                <div class="metric-label">{lbl}</div>
            </div>""", unsafe_allow_html=True)


# ─── Undo / Reset / History ────────────────────────────────────────

def _render_controls():
    steps = st.session_state.get("cleaning_steps", [])
    c1, c2, c3 = st.columns([1, 1, 3])

    with c1:
        if st.button("↩️ Undo Last", disabled=len(steps) == 0,
                     use_container_width=True):
            hist = st.session_state.get("cleaning_history", [])
            if hist:
                st.session_state["cleaned_df"] = hist.pop()
                steps.pop()
                add_activity("Undo", "Reverted last cleaning step")
                st.rerun()

    with c2:
        if st.button("🔄 Reset All", disabled=len(steps) == 0,
                     use_container_width=True, type="secondary"):
            st.session_state["cleaned_df"] = st.session_state["original_df"].copy()
            st.session_state["cleaning_history"] = []
            st.session_state["cleaning_steps"] = []
            add_activity("Reset", "Restored original dataset")
            st.rerun()

    with c3:
        if steps:
            st.markdown(f"""
            <div style="padding:0.5rem 0.8rem;background:rgba(59,130,246,0.08);
                        border-radius:8px;font-size:0.82rem;color:var(--text-secondary);">
                ✅ <strong>{len(steps)}</strong> cleaning step(s) applied
            </div>""", unsafe_allow_html=True)


def _render_history():
    steps = st.session_state.get("cleaning_steps", [])

    if not steps:
        return

    st.markdown("### 📋 Cleaning History")

    for s in reversed(steps):
        step_text = s["step"]
        time_text = s.get("timestamp", "")

        html_content = (
            f'<div style="background:#F8FAFC; border-left:4px solid #3B82F6; '
            f'border-radius:8px; padding:12px 16px; margin-bottom:10px;">'
            f'<div style="font-weight:600; color:#0F172A;">{step_text}</div>'
            f'<div style="font-size:13px; color:#64748B; margin-top:6px;">🕒 {time_text}</div>'
            f'</div>'
        )
        st.markdown(html_content, unsafe_allow_html=True)



# ─── Operation Tabs ─────────────────────────────────────────────────

def _op_duplicates(df):
    dup_count = get_duplicate_count(df)
    if dup_count == 0:
        _alert("No duplicate rows found!", "success")
        return
    _alert(f"Found <strong>{dup_count:,}</strong> duplicate rows ({dup_count/len(df)*100:.1f}%)", "warning")
    c1, c2 = st.columns(2)
    with c1:
        keep = st.selectbox("Keep", ["first", "last"], key="dup_keep")
    with c2:
        subset = st.multiselect("Consider columns (optional)",
                                list(df.columns), key="dup_sub")
    sub = subset if subset else None
    preview = remove_duplicates(df, subset=sub, keep=keep)
    removed = len(df) - len(preview)
    _alert(f"Preview: {len(df):,} → {len(preview):,} rows ({removed:,} removed)", "info")
    if st.button("✅ Remove Duplicates", type="primary", key="go_dup"):
        _apply(preview, f"Removed {removed:,} duplicate rows")
        st.rerun()



def _op_missing(df):
    miss = df.isnull().sum()
    cols_miss = miss[miss > 0]
    if cols_miss.empty:
        _alert("No missing values!", "success")
        return

    miss_df = pd.DataFrame({"Column": cols_miss.index,
                            "Missing": cols_miss.values,
                            "Pct": [f"{v/len(df)*100:.1f}%" for v in cols_miss.values],
                            "Type": [str(df[c].dtype) for c in cols_miss.index]})
    st.dataframe(miss_df, use_container_width=True, hide_index=True, height=200)

    col_type = st.radio("Column type", ["Numeric", "Categorical"],
                        horizontal=True, key="miss_type")

    if col_type == "Numeric":
        num_miss = [c for c in cols_miss.index if pd.api.types.is_numeric_dtype(df[c])]
        if not num_miss:
            _alert("No numeric columns with missing values.", "info")
            return
        c1, c2 = st.columns(2)
        with c1:
            strat = st.selectbox("Strategy",
                                 ["median", "mean", "mode", "constant",
                                  "drop_rows", "drop_column"], key="n_strat")
        const = 0.0
        if strat == "constant":
            const = st.number_input("Constant value", value=0.0, key="n_const")
        with c2:
            sel = st.multiselect("Columns", num_miss, default=num_miss, key="n_cols")
        if sel and st.button("✅ Apply", type="primary", key="go_nmiss"):
            before = int(df[sel].isnull().sum().sum())
            new = fill_missing_numeric(df, sel, strat, const)
            after = int(new[[c for c in sel if c in new.columns]].isnull().sum().sum())
            _apply(new, f"Filled {before-after} missing numeric values ({strat})")
            st.rerun()
    else:
        cat_miss = [c for c in cols_miss.index
                    if df[c].dtype == "object" or df[c].dtype.name == "category"]
        if not cat_miss:
            _alert("No categorical columns with missing values.", "info")
            return
        c1, c2 = st.columns(2)
        with c1:
            strat = st.selectbox("Strategy",
                                 ["mode", "constant", "forward_fill",
                                  "backward_fill", "drop_rows", "drop_column"],
                                 key="c_strat")
        const = "Unknown"
        if strat == "constant":
            const = st.text_input("Constant value", "Unknown", key="c_const")
        with c2:
            sel = st.multiselect("Columns", cat_miss, default=cat_miss, key="c_cols")
        if sel and st.button("✅ Apply", type="primary", key="go_cmiss"):
            before = int(df[sel].isnull().sum().sum())
            new = fill_missing_categorical(df, sel, strat, const)
            after = int(new[[c for c in sel if c in new.columns]].isnull().sum().sum())
            _apply(new, f"Filled {before-after} missing categorical values ({strat})")
            st.rerun()


def _op_dtypes(df):
    st.markdown("##### Convert Column Types")
    c1, c2 = st.columns(2)
    with c1:
        col = st.selectbox("Column", list(df.columns), key="dt_col")
    with c2:
        target = st.selectbox("Convert to",
                              ["integer", "float", "string", "boolean", "datetime"],
                              key="dt_target")
    _alert(f"Current type: <strong>{df[col].dtype}</strong> &rarr; Target: <strong>{target}</strong>", "info")
    if st.button("✅ Convert", type="primary", key="go_dtype"):
        new = change_dtype(df, col, target)
        _apply(new, f"Converted '{col}' to {target}")
        st.rerun()


def _op_rename(df):
    st.markdown("##### Rename Columns")
    col = st.selectbox("Column to rename", list(df.columns), key="ren_col")
    new_name = st.text_input("New name", value=col, key="ren_name")
    if new_name and new_name != col:
        if new_name in df.columns:
            st.error(f"Column '{new_name}' already exists!")
        elif st.button("✅ Rename", type="primary", key="go_ren"):
            new = rename_columns(df, {col: new_name})
            _apply(new, f"Renamed '{col}' → '{new_name}'")
            st.rerun()


def _op_remove_cols(df):
    sel = st.multiselect("Select columns to remove", list(df.columns), key="rm_cols")
    if sel:
        _alert(f"Will permanently remove: <strong>{', '.join(sel)}</strong>", "warning")
        if st.button("✅ Remove Columns", type="primary", key="go_rmcol"):
            new = drop_columns(df, sel)
            _apply(new, f"Removed {len(sel)} column(s): {', '.join(sel)}")
            st.rerun()


def _op_text(df):
    text_cols = df.select_dtypes(include="object").columns.tolist()
    if not text_cols:
        _alert("No text columns found.", "info")
        return
    c1, c2 = st.columns(2)
    with c1:
        sel = st.multiselect("Columns", text_cols, default=text_cols[:3], key="txt_cols")
    with c2:
        op = st.selectbox("Operation",
                          ["lowercase", "uppercase", "title_case",
                           "trim_spaces", "remove_extra_spaces"], key="txt_op")
    if sel and st.button("✅ Apply", type="primary", key="go_txt"):
        new = standardize_text(df, sel, op)
        _apply(new, f"Applied {op} to {len(sel)} column(s)")
        st.rerun()


def _op_replace(df):
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        col = st.selectbox("Column", list(df.columns), key="rep_col")
    with c2:
        find = st.text_input("Find", key="rep_find")
    with c3:
        repl = st.text_input("Replace with", key="rep_repl")
    use_regex = st.checkbox("Use regex", key="rep_regex")
    if find and st.button("✅ Replace", type="primary", key="go_rep"):
        new = replace_values(df, col, find, repl, use_regex)
        _apply(new, f"Replaced '{find}' → '{repl}' in '{col}'")
        st.rerun()


def _op_outliers(df):
    num_cols = df.select_dtypes(include="number").columns.tolist()
    if not num_cols:
        _alert("No numeric columns.", "info")
        return
    c1, c2 = st.columns(2)
    with c1:
        col = st.selectbox("Column", num_cols, key="out_col")
    with c2:
        method = st.selectbox("Method", ["IQR", "Z-Score"], key="out_method")

    if method == "IQR":
        factor = st.slider("IQR multiplier", 1.0, 3.0, 1.5, 0.1, key="out_fac")
        info = detect_outliers_iqr(df, col, factor)
        _alert(f"Bounds: [{info['lower_bound']:.2f}, {info['upper_bound']:.2f}] &mdash; "
               f"<strong>{info['outlier_count']}</strong> outliers detected", "info")
    else:
        thresh = st.slider("Z-Score threshold", 1.0, 5.0, 3.0, 0.1, key="out_z")
        info = detect_outliers_zscore(df, col, thresh)
        _alert(f"<strong>{info['outlier_count']}</strong> outliers detected (|z| &gt; {thresh})", "info")

    if info["outlier_count"] == 0:
        _alert("No outliers detected!", "success")
        return

    action = st.radio("Action", ["Remove rows", "Cap values (Winsorize)"],
                      horizontal=True, key="out_act")
    if st.button("✅ Apply", type="primary", key="go_out"):
        if action == "Remove rows":
            if method == "IQR":
                new = remove_outliers(df, col, "iqr", factor)
            else:
                new = remove_outliers(df, col, "zscore", z_threshold=thresh)
            removed = len(df) - len(new)
            _apply(new, f"Removed {removed} outlier rows from '{col}'")
        else:
            new = cap_outliers(df, col, factor if method == "IQR" else 1.5)
            _apply(new, f"Capped outliers in '{col}'")
        st.rerun()


def _op_null_rows(df):
    null_rows = int(df.isnull().any(axis=1).sum())
    if null_rows == 0:
        _alert("No rows with null values!", "success")
        return
    _alert(f"Found <strong>{null_rows:,}</strong> rows containing null values", "warning")
    how = st.radio("Remove rows where", ["Any column is null", "All columns are null"],
                   horizontal=True, key="null_how")
    h = "any" if "Any" in how else "all"
    preview = remove_null_rows(df, how=h)
    removed = len(df) - len(preview)
    _alert(f"Preview: {len(df):,} &rarr; {len(preview):,} rows ({removed:,} removed)", "info")
    if st.button("✅ Remove Null Rows", type="primary", key="go_null"):
        _apply(preview, f"Removed {removed:,} null rows (how={h})")
        st.rerun()


def _op_constant_cols(df):
    const = find_constant_columns(df)
    if not const:
        _alert("No constant columns found!", "success")
        return
    _alert(f"Found <strong>{len(const)}</strong> constant column(s): <strong>{', '.join(const)}</strong>", "warning")
    if st.button("✅ Remove Constant Columns", type="primary", key="go_const"):
        new = remove_constant_columns(df)
        _apply(new, f"Removed {len(const)} constant column(s)")
        st.rerun()


def _op_high_missing(df):
    thresh = st.slider("Missing threshold (%)", 10, 100, 70, 5, key="hm_thresh",
                       help="Columns with more missing values than this will be removed.")
    cols = find_highly_missing_columns(df, thresh / 100)
    if not cols:
        _alert(f"No columns exceed {thresh}% missing.", "success")
        return
    info = []
    for c in cols:
        pct = df[c].isnull().mean() * 100
        info.append({"Column": c, "Missing %": f"{pct:.1f}%"})
    st.dataframe(pd.DataFrame(info), use_container_width=True, hide_index=True)
    if st.button("✅ Remove Columns", type="primary", key="go_hm"):
        new = remove_highly_missing_columns(df, thresh / 100)
        _apply(new, f"Removed {len(cols)} highly-missing column(s) (>{thresh}%)")
        st.rerun()



# ─── Preview ────────────────────────────────────────────────────────

def _render_preview(df):
    orig = st.session_state["original_df"]
    st.markdown('<div class="content-card"><h3>🔍 Live Preview</h3></div>',
                unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Before** (Original)")
        st.dataframe(orig.head(8), use_container_width=True, hide_index=True)
    with c2:
        st.markdown("**After** (Cleaned)")
        st.dataframe(df.head(8), use_container_width=True, hide_index=True)


# ─── Downloads ──────────────────────────────────────────────────────

def _render_downloads(df):
    st.markdown("""
    <div class="content-card" style="margin-top: 1.5rem; margin-bottom: 0.5rem;">
        <h3 style="margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem; border-bottom: none; padding-bottom: 0;">
            <span>⬇️</span> Export Cleaned Dataset
        </h3>
        <p style="color: var(--text-secondary); font-size: 0.85rem; margin: 0;">
            Save your cleaned dataset to your computer in CSV or Excel formats, or export the processing log.
        </p>
    </div>
    """, unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📄 Download CSV File",
            data=csv,
            file_name="cleaned_dataset.csv",
            mime="text/csv",
            use_container_width=True,
            key="dl_csv"
        )
    with c2:
        buf = io.BytesIO()
        df.to_excel(buf, index=False, engine="openpyxl")
        st.download_button(
            label="📊 Download Excel File",
            data=buf.getvalue(),
            file_name="cleaned_dataset.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="dl_xlsx"
        )
    with c3:
        steps = st.session_state.get("cleaning_steps", [])
        log_text = "\n".join(
            f"[{s.get('timestamp','')}] {s['step']}" for s in steps
        ) if steps else "No cleaning steps applied."
        st.download_button(
            label="📋 Download Cleaning Log",
            data=log_text.encode(),
            file_name="cleaning_log.txt",
            mime="text/plain",
            use_container_width=True,
            key="dl_log"
        )



# ─── Main Renderer ──────────────────────────────────────────────────

def render_cleaning():
    st.markdown("""
    <div class="top-header">
        <h2>🧹 Data Cleaning</h2>
        <p>Select and apply cleaning operations — every step is tracked and undoable.</p>
    </div>""", unsafe_allow_html=True)

    if st.session_state.get("original_df") is None:
        st.markdown("""
        <div class="content-card">
            <div class="empty-state">
                <div class="empty-icon">🧹</div>
                <h3>No Dataset Loaded</h3>
                <p>Upload a CSV or Excel file first to start cleaning.</p>
            </div>
        </div>""", unsafe_allow_html=True)
        return

    # Initialize cleaned_df
    if st.session_state.get("cleaned_df") is None:
        st.session_state["cleaned_df"] = st.session_state["original_df"].copy()

    df = _wdf()

    # Status cards
    _render_status(df)
    st.markdown("")

    # Controls + Quality side by side
    ctrl_col, q_col = st.columns([3, 1])
    with ctrl_col:
        _render_controls()
        st.markdown("")
        _render_history()
    with q_col:
        _render_quality_gauge(df)

    st.markdown("")

    # Cleaning operations
    st.markdown('<div class="content-card"><h3>🛠️ Cleaning Operations</h3></div>',
                unsafe_allow_html=True)

    tabs = st.tabs([
        "🔁 Duplicates", "⚠️ Missing Values", "🔤 Data Types",
        "✏️ Rename", "🗑️ Remove Cols", "📝 Text", "🔄 Replace",
        "📊 Outliers", "❌ Null Rows", "📌 Constant Cols", "📉 High Missing",
    ])

    with tabs[0]:  _op_duplicates(df)
    with tabs[1]:  _op_missing(df)
    with tabs[2]:  _op_dtypes(df)
    with tabs[3]:  _op_rename(df)
    with tabs[4]:  _op_remove_cols(df)
    with tabs[5]:  _op_text(df)
    with tabs[6]:  _op_replace(df)
    with tabs[7]:  _op_outliers(df)
    with tabs[8]:  _op_null_rows(df)
    with tabs[9]:  _op_constant_cols(df)
    with tabs[10]: _op_high_missing(df)

    st.markdown("")

    # Preview + Downloads
    _render_preview(df)
    st.markdown("")
    _render_downloads(df)
