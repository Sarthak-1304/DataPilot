"""
General Helper Functions
========================
Provides session state management, activity logging, file size formatting,
and other shared utilities used across all pages.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Any, Optional


# =============================================================================
# Session State Management
# =============================================================================

def initialize_session_state():
    """Initialize all required session state variables with default values."""
    defaults = {
        # Dataset storage
        "original_df": None,
        "cleaned_df": None,
        "file_name": None,
        "file_size": None,
        "upload_time": None,

        # Navigation
        "current_page": "Dashboard",

        # Theme
        "theme": "dark",

        # Activity log
        "activity_log": [],

        # Cleaning history (for undo)
        "cleaning_history": [],
        "cleaning_steps": [],

        # Cleaning pipeline
        "saved_pipelines": [],

        # Data quality score
        "quality_score": 0,

        # Report path
        "report_path": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_state(key: str, default: Any = None) -> Any:
    """Safely retrieve a value from session state."""
    return st.session_state.get(key, default)


def set_state(key: str, value: Any):
    """Set a value in session state."""
    st.session_state[key] = value


def has_dataset() -> bool:
    """Check if a dataset has been uploaded."""
    return st.session_state.get("original_df") is not None


def has_cleaned_data() -> bool:
    """Check if cleaned data exists."""
    return st.session_state.get("cleaned_df") is not None


def get_working_df() -> Optional[pd.DataFrame]:
    """Return the cleaned DataFrame if available, otherwise the original."""
    if has_cleaned_data():
        return st.session_state["cleaned_df"]
    elif has_dataset():
        return st.session_state["original_df"]
    return None


# =============================================================================
# Activity Logging
# =============================================================================

def add_activity(action: str, details: str = ""):
    """
    Add an entry to the activity log.

    Args:
        action: Short description of the action (e.g., 'Dataset Uploaded').
        details: Additional context about the action.
    """
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "details": details,
    }
    if "activity_log" not in st.session_state:
        st.session_state["activity_log"] = []
    st.session_state["activity_log"].insert(0, entry)


def get_activity_log() -> list:
    """Return the full activity log (most recent first)."""
    return st.session_state.get("activity_log", [])


def clear_activity_log():
    """Clear the entire activity log."""
    st.session_state["activity_log"] = []


# =============================================================================
# Formatting Utilities
# =============================================================================

def format_file_size(size_bytes: int) -> str:
    """Convert bytes to a human-readable file size string."""
    if size_bytes is None:
        return "N/A"
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


def format_number(number: int) -> str:
    """Format large numbers with comma separators."""
    if number is None:
        return "N/A"
    return f"{number:,}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format a float as a percentage string."""
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}%"


def get_memory_usage(df: pd.DataFrame) -> str:
    """Calculate and format the memory usage of a DataFrame."""
    if df is None:
        return "N/A"
    memory_bytes = df.memory_usage(deep=True).sum()
    return format_file_size(memory_bytes)


# =============================================================================
# Data Quality Score
# =============================================================================

def calculate_quality_score(df: pd.DataFrame) -> int:
    """
    Calculate a data quality score from 0-100.

    Factors considered:
        - Completeness (no missing values)     : 35 points
        - Uniqueness (no duplicate rows)        : 20 points
        - Consistency (column types detected)   : 15 points
        - Validity (no fully-empty columns)     : 15 points
        - Column naming quality                 : 15 points
    """
    if df is None or df.empty:
        return 0

    score = 0.0
    total_cells = df.shape[0] * df.shape[1]

    # --- Completeness (35 pts) ---
    if total_cells > 0:
        missing_ratio = df.isnull().sum().sum() / total_cells
        score += (1 - missing_ratio) * 35

    # --- Uniqueness (20 pts) ---
    if len(df) > 0:
        duplicate_ratio = df.duplicated().sum() / len(df)
        score += (1 - duplicate_ratio) * 20

    # --- Consistency: ratio of columns with proper types (15 pts) ---
    type_counts = df.dtypes.value_counts()
    object_ratio = type_counts.get("object", 0) / len(df.columns) if len(df.columns) > 0 else 1
    score += (1 - object_ratio * 0.5) * 15

    # --- Validity: penalize fully-empty columns (15 pts) ---
    if len(df.columns) > 0:
        empty_cols = (df.isnull().all()).sum()
        score += (1 - empty_cols / len(df.columns)) * 15

    # --- Column naming: penalize unnamed / default columns (15 pts) ---
    if len(df.columns) > 0:
        bad_names = sum(
            1 for c in df.columns
            if str(c).startswith("Unnamed") or str(c).strip() == ""
        )
        score += (1 - bad_names / len(df.columns)) * 15

    return min(100, max(0, int(round(score))))


# =============================================================================
# Smart Recommendations
# =============================================================================

def generate_recommendations(df: pd.DataFrame) -> list:
    """
    Analyze a DataFrame and return a list of actionable cleaning recommendations.

    Returns:
        List of dicts with keys: 'icon', 'message', 'severity'.
    """
    if df is None or df.empty:
        return []

    recommendations = []

    # Missing values
    missing = df.isnull().sum()
    for col in missing[missing > 0].index:
        count = missing[col]
        pct = (count / len(df)) * 100
        if df[col].dtype in ("float64", "int64"):
            recommendations.append({
                "icon": "🔧",
                "message": f"Column **{col}** has {count} missing values ({pct:.1f}%). "
                           f"Recommended: Fill using **Median**.",
                "severity": "warning" if pct > 10 else "info",
            })
        else:
            recommendations.append({
                "icon": "🔧",
                "message": f"Column **{col}** has {count} missing values ({pct:.1f}%). "
                           f"Recommended: Fill with **'Unknown'** or **Mode**.",
                "severity": "warning" if pct > 10 else "info",
            })

    # Duplicates
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        recommendations.append({
            "icon": "♻️",
            "message": f"Dataset contains **{dup_count}** duplicate rows. "
                       f"Recommended: **Remove duplicates**.",
            "severity": "warning",
        })

    # Object columns that look like dates
    for col in df.select_dtypes(include=["object"]).columns:
        sample = df[col].dropna().head(20)
        date_parseable = 0
        for val in sample:
            try:
                pd.to_datetime(val)
                date_parseable += 1
            except (ValueError, TypeError):
                pass
        if len(sample) > 0 and date_parseable / len(sample) > 0.8:
            recommendations.append({
                "icon": "📅",
                "message": f"Column **{col}** appears to contain dates. "
                           f"Recommended: **Convert to datetime**.",
                "severity": "info",
            })

    # Outliers in numeric columns (IQR method)
    for col in df.select_dtypes(include=["float64", "int64"]).columns:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        if iqr > 0:
            outliers = ((df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)).sum()
            if outliers > 0:
                recommendations.append({
                    "icon": "📊",
                    "message": f"Column **{col}** contains **{outliers}** outliers. "
                               f"Recommended: Review or **cap outliers**.",
                    "severity": "info",
                })

    # Columns with very high cardinality strings
    for col in df.select_dtypes(include=["object"]).columns:
        nunique = df[col].nunique()
        if nunique > 0.9 * len(df) and len(df) > 50:
            recommendations.append({
                "icon": "⚠️",
                "message": f"Column **{col}** has very high cardinality ({nunique} unique). "
                           f"It may be an ID column.",
                "severity": "info",
            })

    return recommendations


# =============================================================================
# Cleaning History (Undo Support)
# =============================================================================

def save_cleaning_snapshot(description: str):
    """Save a snapshot of the current cleaned DataFrame for undo support."""
    if has_cleaned_data():
        snapshot = {
            "description": description,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "dataframe": st.session_state["cleaned_df"].copy(),
        }
        st.session_state["cleaning_history"].append(snapshot)
        st.session_state["cleaning_steps"].append({
            "step": description,
            "timestamp": snapshot["timestamp"],
        })


def undo_last_cleaning():
    """Revert to the previous cleaning snapshot. Returns True if successful."""
    history = st.session_state.get("cleaning_history", [])
    if len(history) > 0:
        history.pop()  # Remove latest
        if len(history) > 0:
            st.session_state["cleaned_df"] = history[-1]["dataframe"].copy()
        else:
            # No more history — revert to original
            st.session_state["cleaned_df"] = st.session_state["original_df"].copy()
        # Also remove last cleaning step
        steps = st.session_state.get("cleaning_steps", [])
        if steps:
            steps.pop()
        add_activity("Undo", "Reverted last cleaning step")
        return True
    return False
