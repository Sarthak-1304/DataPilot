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
        
        # Save status
        "save_status": "no_project",
        "last_saved_time": "",

        # AI Preferences
        "user_gemini_api_key": "",
        "pref_ai_tone": "Balanced (Recommended)",
        "pref_auto_charts": True,
        "pref_save_chat": True,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Check for active session recovery/restore status on launch
    if "recovery_checked" not in st.session_state:
        st.session_state["recovery_checked"] = True
        from utils.sync_manager import get_active_session, set_active_session, load_project, PROJECTS_DIR
        import os
        from datetime import datetime

        session = get_active_session()
        if session:
            p_id = session.get("active_project_id")
            clean = session.get("clean_exit", True)
            last_activity = session.get("last_activity_time", "")

            # Verify session freshness (under 24 hours)
            is_fresh = False
            if last_activity:
                try:
                    dt = datetime.strptime(last_activity, "%Y-%m-%d %H:%M:%S")
                    age_seconds = (datetime.now() - dt).total_seconds()
                    if age_seconds < 86400:  # 24 hours
                        is_fresh = True
                except Exception:
                    pass

            p_dir = os.path.join(PROJECTS_DIR, p_id) if p_id else None
            backup_file = os.path.join(p_dir, "backups", "latest_backup.parquet") if p_dir else None

            if is_fresh and p_dir and os.path.exists(p_dir):
                if not clean and backup_file and os.path.exists(backup_file):
                    st.session_state["show_crash_recovery"] = p_id
                else:
                    # Clean active session — automatically restore project on refresh!
                    load_project(p_id)
            else:
                # Expired session — clear active_session file
                set_active_session(None)


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
        "time": datetime.now().strftime("%I:%M %p"),
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
    Delegates to the unified implementation in utils.cleaner.
    """
    from utils.cleaner import calculate_quality_score as calc_dict
    return calc_dict(df)["total"]


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
