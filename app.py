"""
Data Pilot — Main Application Entry Point
=====================================================
A professional data cleaning and analysis dashboard built with Streamlit.
Handles page configuration, sidebar navigation, CSS injection, and page routing.
"""

import streamlit as st
import os
import sys

# ---------------------------------------------------------------------------
# Ensure the project root is in the Python path
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ---------------------------------------------------------------------------
# Page configuration — MUST be the first Streamlit command
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Data Pilot",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Data Pilot — A professional data cleaning & analysis tool.",
    },
)

# ---------------------------------------------------------------------------
# Import helpers and page modules
# ---------------------------------------------------------------------------
from utils.helpers import initialize_session_state
from pages.Dashboard import render_dashboard
from pages.Upload import render_upload
from pages.Analysis import render_analysis
from pages.Cleaning import render_cleaning
from pages.BeforeAfter import render_before_after
from pages.Reports import render_reports
from pages.Download import render_download
from pages.Settings import render_settings

# ---------------------------------------------------------------------------
# Initialize session state
# ---------------------------------------------------------------------------
initialize_session_state()


# =============================================================================
# CSS Injection
# =============================================================================

def load_custom_css():
    """Load the custom CSS stylesheet and inject into the app."""
    css_path = os.path.join(PROJECT_ROOT, "assets", "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


load_custom_css()


# =============================================================================
# Sidebar Navigation
# =============================================================================

# Navigation structure: label → (icon, page_key)
NAV_ITEMS = {
    "main": [
        ("🏠  Dashboard",       "Dashboard"),
        ("📂  Upload Dataset",  "Upload"),
        ("🧹  Clean Dataset",   "Cleaning"),
        ("📊  Data Analysis",   "Analysis"),
        ("🔄  Before vs After", "BeforeAfter"),
    ],
    "output": [
        ("📄  Reports",         "Reports"),
        ("⬇️  Download",        "Download"),
    ],
    "system": [
        ("⚙️  Settings",        "Settings"),
    ],
}


def render_sidebar():
    """Build the dark sidebar with branding, navigation, and dataset status."""
    with st.sidebar:
        # ---- Brand Header ----
        st.markdown(
            """
            <div style="text-align:center; padding: 0.5rem 0 0.8rem 0;">
                <div style="font-size: 2.2rem; margin-bottom: 0.1rem;">🧹</div>
                <div style="
                    font-size: 1.2rem;
                    font-weight: 700;
                    color: #F8FAFC;
                    letter-spacing: -0.02em;
                ">Data Pilot</div>
                <div style="
                    font-size: 0.7rem;
                    color: #64748B;
                    margin-top: 0.15rem;
                    letter-spacing: 0.06em;
                    text-transform: uppercase;
                ">Professional Data Toolkit</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # ---- Build flat list of labels for the radio widget ----
        all_labels = []
        label_to_page = {}

        # Section: Main
        st.markdown("### Navigation")
        for label, page_key in NAV_ITEMS["main"]:
            all_labels.append(label)
            label_to_page[label] = page_key

        # Section: Output
        for label, page_key in NAV_ITEMS["output"]:
            all_labels.append(label)
            label_to_page[label] = page_key

        # Section: System
        for label, page_key in NAV_ITEMS["system"]:
            all_labels.append(label)
            label_to_page[label] = page_key

        # Determine current index
        current_page = st.session_state.get("current_page", "Dashboard")
        page_to_label = {v: k for k, v in label_to_page.items()}
        current_label = page_to_label.get(current_page, all_labels[0])
        current_index = all_labels.index(current_label) if current_label in all_labels else 0

        # Define callback to update state immediately before the next rerun
        def on_nav_change():
            selected = st.session_state["nav_radio"]
            st.session_state["current_page"] = label_to_page[selected]

        # Radio navigation
        st.radio(
            "Navigate",
            options=all_labels,
            index=current_index,
            key="nav_radio",
            on_change=on_nav_change,
            label_visibility="collapsed",
        )

        st.markdown("---")

        # ---- Dataset Status Indicator ----
        st.markdown("### Dataset Status")
        if st.session_state.get("original_df") is not None:
            df = st.session_state["original_df"]
            file_name = st.session_state.get("file_name", "Unknown")
            st.markdown(
                f"""
                <div style="
                    background: rgba(16, 185, 129, 0.1);
                    border: 1px solid rgba(16, 185, 129, 0.25);
                    border-radius: 8px;
                    padding: 0.75rem 0.9rem;
                    margin-top: 0.3rem;
                ">
                    <div style="
                        display: flex;
                        align-items: center;
                        gap: 0.4rem;
                        margin-bottom: 0.45rem;
                    ">
                        <span style="
                            width: 8px; height: 8px;
                            background: #10B981;
                            border-radius: 50%;
                            display: inline-block;
                            box-shadow: 0 0 6px rgba(16,185,129,0.5);
                        "></span>
                        <span style="
                            font-size: 0.75rem;
                            font-weight: 600;
                            color: #10B981;
                            text-transform: uppercase;
                            letter-spacing: 0.04em;
                        ">Loaded</span>
                    </div>
                    <div style="
                        font-size: 0.82rem;
                        color: #E2E8F0;
                        font-weight: 500;
                        word-break: break-all;
                    ">{file_name}</div>
                    <div style="
                        font-size: 0.72rem;
                        color: #94A3B8;
                        margin-top: 0.3rem;
                        line-height: 1.5;
                    ">
                        {df.shape[0]:,} rows &nbsp;·&nbsp; {df.shape[1]:,} columns
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div style="
                    background: rgba(100, 116, 139, 0.1);
                    border: 1px solid rgba(100, 116, 139, 0.2);
                    border-radius: 8px;
                    padding: 0.75rem 0.9rem;
                    margin-top: 0.3rem;
                    text-align: center;
                ">
                    <div style="font-size: 1.5rem; margin-bottom: 0.3rem; opacity: 0.4;">📁</div>
                    <div style="
                        font-size: 0.78rem;
                        color: #94A3B8;
                        line-height: 1.5;
                    ">No dataset loaded.<br>Upload a file to begin.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ---- Footer ----
        st.markdown(
            """
            <div style="
                position: fixed;
                bottom: 0;
                padding: 0.8rem 1rem;
                font-size: 0.65rem;
                color: #475569;
                letter-spacing: 0.02em;
                line-height: 1.5;
            ">
                Data Pilot v1.0<br>
                Built for Portfolio · 2025
            </div>
            """,
            unsafe_allow_html=True,
        )


# =============================================================================
# Page Router
# =============================================================================

PAGE_MAP = {
    "Dashboard":   render_dashboard,
    "Upload":      render_upload,
    "Analysis":    render_analysis,
    "Cleaning":    render_cleaning,
    "BeforeAfter": render_before_after,
    "Reports":     render_reports,
    "Download":    render_download,
    "Settings":    render_settings,
}


def main():
    """Main application entry point — renders sidebar and routes to the active page."""
    render_sidebar()

    current_page = st.session_state.get("current_page", "Dashboard")
    page_renderer = PAGE_MAP.get(current_page)

    if page_renderer:
        page_renderer()
    else:
        st.error(f"Page '{current_page}' not found.")


# =============================================================================
# Run
# =============================================================================

if __name__ == "__main__":
    main()
