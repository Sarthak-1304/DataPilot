"""
Upload Page
===========
Handles CSV and Excel (.xlsx) file uploads with:
- Drag-and-drop / browse file upload
- Upload progress indication
- Multi-sheet Excel workbook support
- Dataset preview (first 20 rows)
- Full metadata display (shape, memory, dtypes, column names)
"""

import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

from utils.helpers import (
    add_activity,
    format_file_size,
    format_number,
    get_memory_usage,
    set_state,
    calculate_quality_score,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
SUPPORTED_EXTENSIONS = ["csv", "xlsx", "xls"]
MAX_PREVIEW_ROWS = 20


# =============================================================================
# Internal helpers
# =============================================================================

def _save_uploaded_file(uploaded_file) -> str:
    """Persist the uploaded file to the uploads/ directory and return the path."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path


def _read_csv(uploaded_file) -> pd.DataFrame:
    """Read a CSV file into a DataFrame with automatic encoding detection."""
    encodings = ["utf-8", "latin-1", "iso-8859-1", "cp1252"]
    for enc in encodings:
        try:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, encoding=enc)
        except (UnicodeDecodeError, Exception):
            continue
    # Last resort — ignore errors
    uploaded_file.seek(0)
    return pd.read_csv(uploaded_file, encoding="utf-8", errors="ignore")


def _get_excel_sheet_names(uploaded_file) -> list:
    """Return sheet names from an Excel workbook."""
    uploaded_file.seek(0)
    xls = pd.ExcelFile(uploaded_file, engine="openpyxl")
    return xls.sheet_names


def _read_excel(uploaded_file, sheet_name: str = None) -> pd.DataFrame:
    """Read a specific sheet from an Excel workbook."""
    uploaded_file.seek(0)
    return pd.read_excel(uploaded_file, sheet_name=sheet_name, engine="openpyxl")


def _dtype_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Build a summary table of column data types."""
    dtype_counts = df.dtypes.value_counts().reset_index()
    dtype_counts.columns = ["Data Type", "Count"]
    dtype_counts["Data Type"] = dtype_counts["Data Type"].astype(str)
    return dtype_counts


# =============================================================================
# UI Components
# =============================================================================

def _render_upload_header():
    """Render the page header."""
    st.markdown(
        """
        <div class="top-header">
            <h2>📂 Upload Dataset</h2>
            <p>Upload a CSV or Excel file to begin cleaning and analysis.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_upload_widget():
    """Render the file uploader with styling and instructions."""
    st.markdown(
        """
        <div class="content-card" style="text-align:center; padding: 1rem 1.5rem 0.5rem;">
            <div style="font-size: 2.5rem; margin-bottom: 0.3rem;">📁</div>
            <h3 style="border: none; padding: 0; margin: 0 0 0.3rem;">
                Drag &amp; Drop or Browse Files
            </h3>
            <p style="font-size: 0.82rem; color: #64748B; margin-bottom: 1rem;">
                Supported formats: <strong>CSV</strong>, <strong>Excel (.xlsx / .xls)</strong>
                &nbsp;·&nbsp; Max 200 MB
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload your dataset",
        type=SUPPORTED_EXTENSIONS,
        label_visibility="collapsed",
        key="file_uploader",
    )
    return uploaded_file


def _render_progress_bar():
    """Simulate an upload / processing progress bar."""
    progress_bar = st.progress(0, text="Reading file…")
    for pct in range(0, 101, 5):
        time.sleep(0.02)
        if pct < 40:
            text = "Reading file…"
        elif pct < 70:
            text = "Parsing columns…"
        elif pct < 90:
            text = "Analyzing structure…"
        else:
            text = "Almost done…"
        progress_bar.progress(pct, text=text)
    progress_bar.progress(100, text="✅ Upload complete!")
    time.sleep(0.3)
    progress_bar.empty()


def _render_file_info(uploaded_file, df: pd.DataFrame):
    """Display dataset metadata in metric cards."""
    file_size = len(uploaded_file.getbuffer())
    memory = df.memory_usage(deep=True).sum()

    st.markdown("### 📋 Dataset Information")

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.markdown(
            f"""
            <div class="metric-card blue">
                <div class="metric-icon">📄</div>
                <div class="metric-value">{df.shape[0]:,}</div>
                <div class="metric-label">Total Rows</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="metric-card green">
                <div class="metric-icon">📊</div>
                <div class="metric-value">{df.shape[1]:,}</div>
                <div class="metric-label">Total Columns</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""
            <div class="metric-card orange">
                <div class="metric-icon">⚠️</div>
                <div class="metric-value">{df.isnull().sum().sum():,}</div>
                <div class="metric-label">Missing Values</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            f"""
            <div class="metric-card purple">
                <div class="metric-icon">💾</div>
                <div class="metric-value">{format_file_size(file_size)}</div>
                <div class="metric-label">File Size</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c5:
        st.markdown(
            f"""
            <div class="metric-card red">
                <div class="metric-icon">🧠</div>
                <div class="metric-value">{format_file_size(memory)}</div>
                <div class="metric-label">Memory Usage</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_dataset_preview(df: pd.DataFrame):
    """Show the first N rows and column list of the dataset."""

    # --- Tabbed view: Preview | Columns | Data Types ---
    tab_preview, tab_columns, tab_dtypes = st.tabs(
        ["👀 Preview (First 20 Rows)", "📑 Column Names", "🔤 Data Types"]
    )

    with tab_preview:
        st.dataframe(
            df.head(MAX_PREVIEW_ROWS),
            use_container_width=True,
            height=450,
        )

    with tab_columns:
        col_df = pd.DataFrame({
            "Index": range(1, len(df.columns) + 1),
            "Column Name": df.columns.tolist(),
            "Data Type": [str(dt) for dt in df.dtypes],
            "Non-Null Count": [int(df[c].notna().sum()) for c in df.columns],
            "Null Count": [int(df[c].isna().sum()) for c in df.columns],
            "Unique Values": [int(df[c].nunique()) for c in df.columns],
        })
        st.dataframe(col_df, use_container_width=True, hide_index=True, height=400)

    with tab_dtypes:
        dtype_df = _dtype_summary(df)
        left, right = st.columns([1, 2])
        with left:
            st.dataframe(dtype_df, use_container_width=True, hide_index=True)
        with right:
            # Visual dtype breakdown
            st.markdown("#### Column Type Breakdown")
            for _, row in dtype_df.iterrows():
                dtype_name = row["Data Type"]
                count = int(row["Count"])
                pct = count / len(df.columns) * 100
                color_map = {
                    "int64": "#3B82F6",
                    "float64": "#10B981",
                    "object": "#F59E0B",
                    "bool": "#8B5CF6",
                    "datetime64[ns]": "#EF4444",
                }
                color = color_map.get(dtype_name, "#64748B")
                st.markdown(
                    f"""
                    <div style="margin-bottom: 0.6rem;">
                        <div style="
                            display: flex;
                            justify-content: space-between;
                            font-size: 0.82rem;
                            font-weight: 500;
                            margin-bottom: 0.2rem;
                        ">
                            <span>{dtype_name}</span>
                            <span style="color: #64748B;">{count} cols ({pct:.0f}%)</span>
                        </div>
                        <div style="
                            width: 100%;
                            height: 8px;
                            background: #E2E8F0;
                            border-radius: 100px;
                            overflow: hidden;
                        ">
                            <div style="
                                width: {pct}%;
                                height: 100%;
                                background: {color};
                                border-radius: 100px;
                                transition: width 0.6s ease;
                            "></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def _render_upload_details_card(uploaded_file, df: pd.DataFrame):
    """Show a summary card with file name, upload time, etc."""
    upload_time = datetime.now().strftime("%b %d, %Y — %I:%M %p")
    file_size = len(uploaded_file.getbuffer())

    st.markdown(
        f"""
        <div class="content-card" style="margin-top: 1rem;">
            <h3>📝 Upload Summary</h3>
            <table style="width:100%; font-size: 0.85rem; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #E2E8F0;">
                    <td style="padding: 0.55rem 0; color: #64748B; width: 160px;">File Name</td>
                    <td style="padding: 0.55rem 0; font-weight: 600;">{uploaded_file.name}</td>
                </tr>
                <tr style="border-bottom: 1px solid #E2E8F0;">
                    <td style="padding: 0.55rem 0; color: #64748B;">Upload Time</td>
                    <td style="padding: 0.55rem 0; font-weight: 500;">{upload_time}</td>
                </tr>
                <tr style="border-bottom: 1px solid #E2E8F0;">
                    <td style="padding: 0.55rem 0; color: #64748B;">Rows × Columns</td>
                    <td style="padding: 0.55rem 0; font-weight: 500;">{df.shape[0]:,} × {df.shape[1]:,}</td>
                </tr>
                <tr style="border-bottom: 1px solid #E2E8F0;">
                    <td style="padding: 0.55rem 0; color: #64748B;">File Size</td>
                    <td style="padding: 0.55rem 0; font-weight: 500;">{format_file_size(file_size)}</td>
                </tr>
                <tr>
                    <td style="padding: 0.55rem 0; color: #64748B;">Memory Usage</td>
                    <td style="padding: 0.55rem 0; font-weight: 500;">{get_memory_usage(df)}</td>
                </tr>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# Main Page Renderer
# =============================================================================

def render_upload():
    """Render the complete Upload Dataset page."""
    _render_upload_header()
    uploaded_file = _render_upload_widget()

    if uploaded_file is not None:
        file_ext = uploaded_file.name.rsplit(".", 1)[-1].lower()

        try:
            # ---- Excel: sheet selection ----
            if file_ext in ("xlsx", "xls"):
                sheet_names = _get_excel_sheet_names(uploaded_file)

                if len(sheet_names) > 1:
                    st.markdown(
                        """
                        <div class="content-card" style="margin-bottom: 1rem;">
                            <h3>📑 Select Excel Sheet</h3>
                            <p style="font-size: 0.82rem; color: #64748B;">
                                This workbook contains multiple sheets. Choose which one to load.
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    selected_sheet = st.selectbox(
                        "Choose sheet",
                        options=sheet_names,
                        index=0,
                        label_visibility="collapsed",
                    )
                else:
                    selected_sheet = sheet_names[0]

                # Check if this is a new upload or sheet change
                need_load = (
                    st.session_state.get("file_name") != uploaded_file.name
                    or st.session_state.get("_selected_sheet") != selected_sheet
                )

                if need_load:
                    _render_progress_bar()
                    df = _read_excel(uploaded_file, sheet_name=selected_sheet)
                    st.session_state["_selected_sheet"] = selected_sheet
                else:
                    df = st.session_state.get("original_df")

            # ---- CSV ----
            elif file_ext == "csv":
                need_load = st.session_state.get("file_name") != uploaded_file.name

                if need_load:
                    _render_progress_bar()
                    df = _read_csv(uploaded_file)
                else:
                    df = st.session_state.get("original_df")

            else:
                st.error(f"Unsupported file format: .{file_ext}")
                return

            # ---- Validate ----
            if df is None or df.empty:
                st.warning("⚠️ The uploaded file is empty or could not be parsed.")
                return

            # ---- Store in session state (only on new load) ----
            if st.session_state.get("file_name") != uploaded_file.name or (
                file_ext in ("xlsx", "xls")
                and st.session_state.get("_selected_sheet") != st.session_state.get("_prev_sheet")
            ):
                _save_uploaded_file(uploaded_file)
                
                # Check if a project is loaded; if not, create one automatically
                if not st.session_state.get("project_id"):
                    from utils.sync_manager import create_new_project_from_upload
                    create_new_project_from_upload(uploaded_file, df)
                else:
                    set_state("original_df", df)
                    set_state("cleaned_df", df.copy())
                    set_state("file_name", uploaded_file.name)
                    set_state("file_size", len(uploaded_file.getbuffer()))
                    set_state("upload_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    set_state("quality_score", calculate_quality_score(df))
                    set_state("cleaning_history", [])
                    set_state("cleaning_steps", [])
                    
                    from utils.sync_manager import save_project
                    save_project(st.session_state["project_id"])
                    
                set_state("_prev_sheet", st.session_state.get("_selected_sheet"))

                sheet_info = ""
                if file_ext in ("xlsx", "xls"):
                    sheet_info = f" (Sheet: {st.session_state.get('_selected_sheet', '')})"
                add_activity(
                    "Dataset Uploaded",
                    f"{uploaded_file.name}{sheet_info} — "
                    f"{df.shape[0]:,} rows × {df.shape[1]:,} columns",
                )
                st.toast(f"✅ **{uploaded_file.name}** loaded successfully!", icon="🎉")
                st.rerun()

            # ---- Render all preview sections ----
            st.markdown("---")
            _render_file_info(uploaded_file, df)
            st.markdown("")
            _render_dataset_preview(df)
            _render_upload_details_card(uploaded_file, df)

        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
            st.exception(e)

    else:
        # No file uploaded yet — show tips
        st.markdown("")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(
                """
                <div class="content-card" style="text-align: center;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">📊</div>
                    <h3 style="border: none; padding: 0; font-size: 0.95rem;">CSV Files</h3>
                    <p style="font-size: 0.8rem; color: #64748B; line-height: 1.6;">
                        Comma-separated values with automatic encoding detection.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                """
                <div class="content-card" style="text-align: center;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">📗</div>
                    <h3 style="border: none; padding: 0; font-size: 0.95rem;">Excel Files</h3>
                    <p style="font-size: 0.8rem; color: #64748B; line-height: 1.6;">
                        .xlsx and .xls workbooks with multi-sheet selection support.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col3:
            st.markdown(
                """
                <div class="content-card" style="text-align: center;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">🔒</div>
                    <h3 style="border: none; padding: 0; font-size: 0.95rem;">Secure & Local</h3>
                    <p style="font-size: 0.8rem; color: #64748B; line-height: 1.6;">
                        Your data stays on your machine. Nothing is sent to external servers.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
