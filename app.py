import streamlit as st
import os
import sys
import textwrap

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
import importlib
from utils.helpers import initialize_session_state

import pages.Dashboard as p_dashboard
import pages.Upload as p_upload
import pages.Analysis as p_analysis
import pages.Cleaning as p_cleaning
import pages.BeforeAfter as p_beforeafter
import pages.Reports as p_reports
import pages.Download as p_download
import pages.Settings as p_settings

# Force reload modules so editing pages takes effect immediately
importlib.reload(p_dashboard)
importlib.reload(p_upload)
importlib.reload(p_analysis)
importlib.reload(p_cleaning)
importlib.reload(p_beforeafter)
importlib.reload(p_reports)
importlib.reload(p_download)
importlib.reload(p_settings)

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
# Landing Page (shown when no dataset is loaded)
# =============================================================================

def render_html(html_str):
    """Renders HTML by stripping blank lines to prevent Streamlit Markdown splitting."""
    import textwrap
    import streamlit as st
    dedented = textwrap.dedent(html_str)
    cleaned = "\n".join([line for line in dedented.splitlines() if line.strip()])
    st.markdown(cleaned, unsafe_allow_html=True)


def render_landing_page():
    """Centered branding with upload functionality — the first thing users see."""
    import streamlit as st
    # Custom fonts and premium style sheets
    current_theme = st.session_state.get("theme", "dark")
    if current_theme == "dark":
        theme_css = """
        :root {
            --app-bg: #0B0A14;
            --app-bg-image: radial-gradient(circle at 80% 20%, rgba(99, 102, 241, 0.12) 0%, rgba(139, 92, 246, 0.12) 30%, transparent 70%),
                            radial-gradient(circle at 10% 80%, rgba(139, 92, 246, 0.08) 0%, rgba(99, 102, 241, 0.08) 40%, transparent 70%);
            --text-primary: #FFFFFF;
            --text-secondary: #94A3B8;
            --text-muted: #64748B;
            --card-bg: #161525;
            --card-border: #252438;
            --card-border-dashed: #3D3C57;
            --mockup-card-bg: #0F0E1C;
        }
        h1, h2, h3, h4, h5, h6, .feature-card div, .dropbtn {
            color: #FFFFFF !important;
        }
        p, .feature-card span {
            color: #94A3B8 !important;
        }
        .modal-content {
            background-color: #161525 !important;
            border: 1px solid #252438 !important;
            color: #FFFFFF !important;
        }
        .modal-content h3 {
            color: #FFFFFF !important;
        }
        .modal-content p {
            color: #94A3B8 !important;
        }
        """
    else:
        theme_css = """
        :root {
            --app-bg: #FAF9FD;
            --app-bg-image: radial-gradient(circle at 80% 20%, rgba(219, 234, 254, 0.45) 0%, rgba(243, 232, 255, 0.45) 30%, transparent 70%),
                            radial-gradient(circle at 10% 80%, rgba(243, 232, 255, 0.35) 0%, rgba(238, 242, 255, 0.35) 40%, transparent 70%);
            --text-primary: #0F172A;
            --text-secondary: #475569;
            --text-muted: #64748B;
            --card-bg: #FFFFFF;
            --card-border: #E2E8F0;
            --card-border-dashed: #CBD5E1;
            --mockup-card-bg: #FAF9FD;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #0F172A !important;
        }
        p {
            color: #475569 !important;
        }
        .modal-content {
            background-color: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            color: #0F172A !important;
        }
        .modal-content h3 {
            color: #0F172A !important;
        }
        .modal-content p {
            color: #475569 !important;
        }
        """

    render_html("""
        <div>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
        /* Reset and global overrides for landing page */
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
        [data-testid="stHeader"] { display: none !important; }
        [data-testid="stAppViewContainer"] {
            background-color: var(--app-bg) !important;
            background-image: var(--app-bg-image) !important;
        }
        .block-container {
            max-width: 1200px !important;
            padding-top: 5rem !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
        }
        /*THEME_CSS_PLACEHOLDER*/

        /* Hide default streamlit file uploader details and make it invisible-clickable */
        div[data-testid="stFileUploader"] {
            opacity: 0 !important;
            position: relative !important;
            z-index: 10 !important;
            height: 110px !important;
            cursor: pointer !important;
        }
        div[data-testid="stFileUploader"] * {
            cursor: pointer !important;
        }
        div[data-testid="stFileUploader"] > section {
            padding: 0 !important;
            height: 110px !important;
            min-height: 110px !important;
        }

        /* Custom upload card design (sits behind the invisible uploader) */
        .custom-upload-card {
            position: absolute !important;
            margin-top: -126px !important;
            left: 0 !important;
            right: 0 !important;
            height: 110px !important;
            background: var(--card-bg) !important;
            border: 2px dashed var(--card-border-dashed) !important;
            border-radius: 16px !important;
            padding: 1.5rem 2rem !important;
            display: flex !important;
            align-items: center !important;
            justify-content: space-between !important;
            pointer-events: none !important;
            z-index: 1 !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05) !important;
            transition: all 0.3s ease !important;
        }

        /* Hover state triggered by the invisible uploader */
        div.element-container:has(div[data-testid="stFileUploader"]):hover + div.element-container .custom-upload-card {
            border-color: #6366F1 !important;
            box-shadow: 0 12px 30px rgba(99, 102, 241, 0.2) !important;
            background-color: var(--card-bg) !important;
            filter: brightness(1.05);
        }

        /* Feature card styles */
        .feature-card {
            background: var(--card-bg) !important;
            border: 1px solid var(--card-border) !important;
            border-radius: 16px !important;
            padding: 1.5rem !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05) !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            position: relative !important;
            overflow: hidden !important;
            height: 100% !important;
            min-height: 150px !important;
        }
        .feature-card:hover {
            transform: translateY(-5px) !important;
            box-shadow: 0 12px 30px rgba(99, 102, 241, 0.15) !important;
        }
        .feature-card .arrow-indicator {
            position: absolute;
            bottom: 1.2rem;
            right: 1.2rem;
            font-size: 1.2rem;
            transition: transform 0.3s ease;
        }
        .feature-card:hover .arrow-indicator {
            transform: translateX(4px);
        }

                /* Clean typography */
        h1, h2, h3, p {
            font-family: 'Plus Jakarta Sans', sans-serif !important;
        }

        /* Modals style */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.6);
            backdrop-filter: blur(4px);
            z-index: 99999;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .modal-overlay:target {
            opacity: 1;
            visibility: visible;
        }
        .modal-content {
            background: white;
            padding: 2rem;
            border-radius: 16px;
            max-width: 500px;
            width: 90%;
            position: relative;
            box-shadow: 0 20px 40px rgba(0,0,0,0.15);
            font-family: 'Plus Jakarta Sans', sans-serif;
        }
        .modal-close {
            position: absolute;
            top: 1rem;
            right: 1rem;
            font-size: 1.5rem;
            text-decoration: none;
            color: var(--text-muted) !important;
        }
        .modal-close:hover {
            color: var(--text-primary) !important;
        }

        /* Dropdown menu for top bar (click-based using <details> / <summary>) */
        details.dropdown {
            position: relative;
            display: inline-block;
        }
        details.dropdown summary::-webkit-details-marker {
            display: none !important;
        }
        details.dropdown summary {
            list-style: none !important;
            outline: none !important;
        }
        .dropbtn {
            background: #1E1C30 !important;
            border: 1px solid #32304C !important;
            color: #CBD5E1 !important;
            font-size: 1.05rem !important;
            font-weight: 700 !important;
            cursor: pointer !important;
            padding: 0.35rem 0.85rem !important;
            border-radius: 8px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            transition: all 0.2s ease !important;
            user-select: none !important;
        }
        .dropbtn:hover {
            color: white !important;
            background: #2B2945 !important;
            border-color: #434164 !important;
        }
        .dropdown-content {
            position: absolute;
            right: 0;
            background-color: #11101D;
            min-width: 175px;
            box-shadow: 0px 8px 24px rgba(0, 0, 0, 0.55);
            z-index: 10000;
            border-radius: 8px;
            border: 1px solid #2D2C3F;
            margin-top: 0.5rem;
        }
        .dropdown-content a {
            color: #CBD5E1;
            padding: 10px 16px;
            text-decoration: none;
            display: block;
            font-size: 0.8rem;
            font-family: 'Plus Jakarta Sans', sans-serif;
            text-align: left;
            transition: background 0.2s ease;
        }
        .dropdown-content a:hover {
            background-color: #1F1E2E;
            color: white;
            border-radius: 8px;
        }
        </style>
        </div>
    """.replace("/*THEME_CSS_PLACEHOLDER*/", theme_css))

    # ── 1. NAVBAR (Top) ──
    render_html("""
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: #0B0A14;
            padding: 0.6rem 2.5rem;
            width: 100%;
            position: fixed;
            top: 0;
            left: 0;
            z-index: 9999;
            border-bottom: 1px solid #1F1E2E;
        ">
            <a href="/?action=reset" target="_self" style="display: flex; align-items: center; gap: 0.6rem; text-decoration: none;">
                <div style="
                    background: linear-gradient(135deg, #6366F1, #8B5CF6);
                    border-radius: 6px;
                    width: 28px;
                    height: 28px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                    font-size: 0.95rem;
                ">📊</div>
                <span style="color: white; font-weight: 700; font-size: 1.1rem; letter-spacing: -0.02em;">Data Pilot</span>
            </a>
            <div style="display: flex; align-items: center; gap: 1.2rem;">
                <details class="dropdown">
                    <summary class="dropbtn">⋮ Menu</summary>
                    <div class="dropdown-content">
                        <a href="/?action=reset" target="_self">🏠 Home / Reset</a>
                        <a href="#about-modal">ℹ️ About</a>
                    </div>
                </details>
            </div>
        </div>
    """)

    # ── 2. HERO AREA (Two Columns Grid) ──
    col_left, col_right = st.columns([1.1, 0.9], gap="large")

    with col_left:
        # Tag pill
        render_html("""
            <div style="
                display: inline-flex;
                align-items: center;
                background: #EEF2FF;
                color: #6366F1;
                font-size: 0.78rem;
                font-weight: 600;
                padding: 0.3rem 0.8rem;
                border-radius: 100px;
                margin-bottom: 1.2rem;
                gap: 0.3rem;
            ">
                <span>✨</span> Your Professional Data Partner
            </div>
        """)

        # Heading and Paragraph
        render_html("""
            <h1 style="font-size: 2.8rem; font-weight: 800; color: var(--text-primary); margin: 0; line-height: 1.15; letter-spacing: -0.03em;">
            Clean. Analyze.<br>Discover. <span style="background: linear-gradient(135deg, #6366F1, #8B5CF6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">Decide.</span>
            </h1>
            <p style="font-size: 0.95rem; color: var(--text-secondary); margin: 1.2rem 0 1.5rem 0; line-height: 1.6;">
            Data Pilot is your all-in-one toolkit for data cleaning, analysis, visualization, and actionable insights — built for data professionals who want accuracy, speed, and clarity.
            </p>
        """)

        # Core Tags
        render_html("""
            <div style="display: flex; gap: 0.6rem; margin-bottom: 2rem; flex-wrap: wrap;">
                <span style="background: var(--card-bg); border: 1px solid var(--card-border); padding: 0.4rem 0.8rem; border-radius: 8px; font-size: 0.82rem; font-weight: 500; color: var(--text-secondary); display: flex; align-items: center; gap: 0.3rem; box-shadow: 0 2px 4px rgba(0,0,0,0.01);">
                    🧹 Smart Cleaning
                </span>
                <span style="background: var(--card-bg); border: 1px solid var(--card-border); padding: 0.4rem 0.8rem; border-radius: 8px; font-size: 0.82rem; font-weight: 500; color: var(--text-secondary); display: flex; align-items: center; gap: 0.3rem; box-shadow: 0 2px 4px rgba(0,0,0,0.01);">
                    📈 Deep Analysis
                </span>
                <span style="background: var(--card-bg); border: 1px solid var(--card-border); padding: 0.4rem 0.8rem; border-radius: 8px; font-size: 0.82rem; font-weight: 500; color: var(--text-secondary); display: flex; align-items: center; gap: 0.3rem; box-shadow: 0 2px 4px rgba(0,0,0,0.01);">
                    💡 Actionable Insights
                </span>
            </div>
        """)

        # Metric Pills
        render_html("""
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; max-width: 420px; margin-bottom: 1.5rem;">
                <div style="display: flex; align-items: center; gap: 0.6rem;">
                    <span style="font-size: 1.3rem;">🗄️</span>
                    <div>
                        <div style="font-weight: 700; font-size: 0.95rem; color: var(--text-primary);">10+</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">Data Formats</div>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 0.6rem;">
                    <span style="font-size: 1.3rem;">🛡️</span>
                    <div>
                        <div style="font-weight: 700; font-size: 0.95rem; color: var(--text-primary);">100%</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">Secure & Private</div>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 0.6rem;">
                    <span style="font-size: 1.3rem;">⚡</span>
                    <div>
                        <div style="font-weight: 700; font-size: 0.95rem; color: var(--text-primary);">Fast</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">Processing</div>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 0.6rem;">
                    <span style="font-size: 1.3rem;">🎯</span>
                    <div>
                        <div style="font-weight: 700; font-size: 0.95rem; color: var(--text-primary);">Accurate</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">Results</div>
                    </div>
                </div>
            </div>
        """)

    with col_right:
        # Live CSS/SVG Mockup of Data Pilot Dashboard
        render_html("""
            <div style="
                background: var(--card-bg);
                border-radius: 16px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.08);
                border: 1px solid var(--card-border);
                display: flex;
                overflow: hidden;
                height: 310px;
                width: 100%;
                margin-top: 1rem;
            ">
                <!-- Mockup Sidebar -->
                <div style="
                    background: #0B0A14;
                    width: 48px;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    padding-top: 1.2rem;
                    gap: 1.1rem;
                ">
                    <div style="width: 18px; height: 18px; border-radius: 5px; background: rgba(99, 102, 241, 0.2); display: flex; align-items: center; justify-content: center; font-size: 0.6rem;">📋</div>
                    <div style="width: 18px; height: 18px; border-radius: 5px; background: rgba(255,255,255,0.05); display: flex; align-items: center; justify-content: center; font-size: 0.6rem;">🧹</div>
                    <div style="width: 18px; height: 18px; border-radius: 5px; background: rgba(255,255,255,0.05); display: flex; align-items: center; justify-content: center; font-size: 0.6rem;">⚖️</div>
                    <div style="width: 18px; height: 18px; border-radius: 5px; background: rgba(255,255,255,0.05); display: flex; align-items: center; justify-content: center; font-size: 0.6rem;">📊</div>
                    <div style="width: 18px; height: 18px; border-radius: 5px; background: rgba(255,255,255,0.05); display: flex; align-items: center; justify-content: center; font-size: 0.6rem;">📑</div>
                </div>
                <!-- Mockup Content Area -->
                <div style="flex: 1; padding: 1.2rem; display: grid; grid-template-columns: 1.3fr 1fr; grid-template-rows: 1fr 1fr; gap: 0.8rem; background: var(--app-bg); align-items: stretch;">
                    <!-- Data Overview Card -->
                    <div style="background: var(--card-bg); border-radius: 10px; padding: 0.8rem; border: 1px solid var(--card-border); display: flex; flex-direction: column; justify-content: space-between;">
                        <div style="font-size: 0.72rem; font-weight: 700; color: var(--text-secondary); margin-bottom: 0.4rem;">Data Overview</div>
                        <div style="height: 55px; display: flex; align-items: flex-end; gap: 5px; padding-bottom: 2px;">
                            <div style="flex: 1; height: 35%; background: #E2E8F0; border-radius: 3px;"></div>
                            <div style="flex: 1; height: 60%; background: #CBD5E1; border-radius: 3px;"></div>
                            <div style="flex: 1; height: 45%; background: #94A3B8; border-radius: 3px;"></div>
                            <div style="flex: 1; height: 80%; background: #8B5CF6; border-radius: 3px;"></div>
                            <div style="flex: 1; height: 65%; background: #6366F1; border-radius: 3px;"></div>
                            <div style="flex: 1; height: 95%; background: #EC4899; border-radius: 3px;"></div>
                        </div>
                    </div>
                    <!-- Quality Score Card -->
                    <div style="background: var(--card-bg); border-radius: 10px; padding: 0.8rem; border: 1px solid var(--card-border); display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative;">
                        <div style="font-size: 0.72rem; font-weight: 700; color: var(--text-secondary); align-self: flex-start; margin-bottom: 2px;">Quality Score</div>
                        <!-- Circular Progress Dial -->
                        <svg width="65" height="65" viewBox="0 0 36 36" style="transform: rotate(-90deg); margin: 0.2rem 0;">
                            <path stroke="var(--card-border-dashed)" stroke-width="3.5" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                            <path stroke="#8B5CF6" stroke-dasharray="92, 100" stroke-width="3.5" stroke-linecap="round" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                        </svg>
                        <div style="position: absolute; font-size: 0.9rem; font-weight: 800; color: var(--text-primary); top: 54%; transform: translateY(-50%);">92%</div>
                        <div style="font-size: 0.55rem; color: #10B981; font-weight: 700; margin-top: 1px;">Excellent</div>
                    </div>
                    <!-- Insights Card -->
                    <div style="background: var(--card-bg); border-radius: 10px; padding: 0.8rem; border: 1px solid var(--card-border); display: flex; flex-direction: column; justify-content: space-between;">
                        <div style="font-size: 0.72rem; font-weight: 700; color: var(--text-secondary); margin-bottom: 0.4rem;">Insights</div>
                        <div style="display: flex; flex-direction: column; gap: 6px; flex: 1; justify-content: center;">
                            <div style="height: 6px; background: #EEF2FF; border-radius: 3px; width: 100%; display: flex; gap: 4px; align-items: center;">
                                <div style="width: 4px; height: 4px; border-radius: 50%; background: #6366F1;"></div>
                                <div style="flex:1; height: 4px; background: #E2E8F0; border-radius: 2px;"></div>
                            </div>
                            <div style="height: 6px; background: #EEF2FF; border-radius: 3px; width: 85%; display: flex; gap: 4px; align-items: center;">
                                <div style="width: 4px; height: 4px; border-radius: 50%; background: #6366F1;"></div>
                                <div style="flex:1; height: 4px; background: #E2E8F0; border-radius: 2px;"></div>
                            </div>
                            <div style="height: 6px; background: #EEF2FF; border-radius: 3px; width: 90%; display: flex; gap: 4px; align-items: center;">
                                <div style="width: 4px; height: 4px; border-radius: 50%; background: #6366F1;"></div>
                                <div style="flex:1; height: 4px; background: #E2E8F0; border-radius: 2px;"></div>
                            </div>
                        </div>
                    </div>
                    <!-- Top Categories Card -->
                    <div style="background: var(--card-bg); border-radius: 10px; padding: 0.8rem; border: 1px solid var(--card-border); display: flex; flex-direction: column; justify-content: space-between; align-items: center;">
                        <div style="font-size: 0.72rem; font-weight: 700; color: var(--text-secondary); align-self: flex-start; margin-bottom: 0.2rem;">Top Categories</div>
                        <!-- Donut Chart representation -->
                        <div style="
                            width: 45px;
                            height: 45px;
                            border-radius: 50%;
                            background: conic-gradient(#8B5CF6 0% 45%, #EC4899 45% 75%, #3B82F6 75% 100%);
                            display: flex;
                            align-items: center;
                            justify-content: center;
                        ">
                            <div style="width: 25px; height: 25px; border-radius: 50%; background: var(--card-bg);"></div>
                        </div>
                        <div style="display: flex; gap: 6px; margin-top: 0.2rem; font-size: 0.5rem; font-weight: 600; color: var(--text-muted);">
                            <span>● A</span>
                            <span>● B</span>
                            <span>● C</span>
                        </div>
                    </div>
                </div>
            </div>
        """)

    # ── 3. UPLOAD YOUR DATASET SECTION ──
    # Render file uploader FIRST (occupies layout height)
    uploaded_file = st.file_uploader(
        "Upload CSV or Excel",
        type=["csv", "xlsx", "xls"],
        label_visibility="collapsed",
        key="landing_uploader",
    )

    # Render custom card SECOND (absolutely positioned behind the uploader using -126px top margin)
    render_html("""
        <div class="custom-upload-card">
            <div style="display: flex; align-items: center; gap: 1.5rem;">
                <div style="
                    background: #EEF2FF;
                    border-radius: 12px;
                    width: 48px;
                    height: 48px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #6366F1;
                    font-size: 1.5rem;
                ">☁️</div>
                <div>
                    <h3 style="margin: 0; font-size: 1.15rem; font-weight: 700; color: var(--text-primary); border: none; padding: 0;">Upload Your Dataset</h3>
                    <p style="margin: 0.15rem 0 0 0; font-size: 0.85rem; color: var(--text-muted);">Drop a CSV or Excel file to get started with analysis, cleaning, and insights.</p>
                    <p style="margin: 0.35rem 0 0 0; font-size: 0.72rem; color: #94A3B8;">Supports: CSV, XLSX, XLS &nbsp;•&nbsp; Max file size: 200MB</p>
                </div>
            </div>
            <div style="
                background: #6366F1;
                color: white;
                font-size: 0.85rem;
                font-weight: 600;
                padding: 0.6rem 1.2rem;
                border-radius: 8px;
                display: flex;
                align-items: center;
                gap: 0.4rem;
            ">📁 Browse Files</div>
        </div>
    """)

    if uploaded_file is not None:
        import pandas as pd
        from utils.helpers import add_activity

        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            st.session_state["original_df"] = df
            st.session_state["cleaned_df"] = None
            st.session_state["file_name"] = uploaded_file.name
            st.session_state["file_size"] = uploaded_file.size
            st.session_state["cleaning_steps"] = []
            st.session_state["cleaning_history"] = []
            st.session_state["current_page"] = "Dashboard"

            add_activity("Dataset Uploaded", f"{uploaded_file.name} ({df.shape[0]} rows × {df.shape[1]} cols)")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Failed to read file: {e}")

    # ── 4. FEATURE CARDS (4 Column Row) ──
    feat_cols = st.columns(4, gap="medium")
    features = [
        ("📋", "Dashboard", "At-a-glance overview of your data with key metrics and quality score.", "#8B5CF6"),
        ("🧹", "Smart Cleaning", "One-click cleaning: handle missing values, duplicates, outliers, and more.", "#F97316"),
        ("⚖️", "Before vs After", "Side-by-side comparison of every cleaning step and its impact.", "#10B981"),
        ("📊", "Analysis", "Interactive charts, correlations, distributions, and deep insights.", "#3B82F6"),
    ]
    for col, (icon, title, desc, accent) in zip(feat_cols, features):
        with col:
            render_html(f"""
                <div class="feature-card">
                    <div style="
                        background: {accent}15;
                        border-radius: 10px;
                        width: 38px;
                        height: 38px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 1.25rem;
                        margin-bottom: 0.8rem;
                    ">{icon}</div>
                    <div style="font-weight: 700; font-size: 0.95rem; color: var(--text-primary); margin-bottom: 0.3rem;">{title}</div>
                    <div style="font-size: 0.78rem; color: var(--text-muted); line-height: 1.5; margin-bottom: 1.5rem;">{desc}</div>
                    <span class="arrow-indicator" style="color: {accent};">→</span>
                </div>
            """)

    render_html("<div style='height:2.5rem;'></div>")

    # ── 5. BOTTOM GRID (Why Data Pilot? vs Your Data Journey) ──
    col_bottom_left, col_bottom_right = st.columns([1, 1.1], gap="large")

    with col_bottom_left:
        render_html("""
            <div style="
                background: var(--card-bg);
                border: 1px solid var(--card-border);
                border-radius: 16px;
                padding: 1.8rem;
                color: var(--text-primary);
                height: 100%;
            ">
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.4rem;">
                    <span style="color: #6366F1; font-size: 1.1rem;">★</span>
                    <h3 style="margin: 0; font-size: 1.15rem; font-weight: 700; color: var(--text-primary); border: none; padding: 0;">Why Data Pilot?</h3>
                </div>
                <p style="font-size: 0.82rem; color: var(--text-secondary); margin: 0 0 1.5rem 0;">Powerful features to make your data workflow effortless.</p>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.2rem;">
                    <div>
                        <div style="display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.25rem;">
                            <span style="font-size: 1rem; color: #6366F1;">🛡️</span>
                            <span style="font-weight: 600; font-size: 0.82rem; color: var(--text-primary);">Data Quality Score</span>
                        </div>
                        <p style="font-size: 0.72rem; color: #94A3B8; margin: 0; line-height: 1.4;">Measure and improve data quality.</p>
                    </div>
                    <div>
                        <div style="display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.25rem;">
                            <span style="font-size: 1rem; color: #8B5CF6;">🧠</span>
                            <span style="font-weight: 600; font-size: 0.82rem; color: var(--text-primary);">Smart Data Insights</span>
                        </div>
                        <p style="font-size: 0.72rem; color: #94A3B8; margin: 0; line-height: 1.4;">Get suggestions & patterns.</p>
                    </div>
                    <div>
                        <div style="display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.25rem;">
                            <span style="font-size: 1rem; color: #10B981;">📝</span>
                            <span style="font-weight: 600; font-size: 0.82rem; color: var(--text-primary);">Export Reports</span>
                        </div>
                        <p style="font-size: 0.72rem; color: #94A3B8; margin: 0; line-height: 1.4;">Download multiple formats.</p>
                    </div>
                    <div>
                        <div style="display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.25rem;">
                            <span style="font-size: 1rem; color: #0EA5E9;">🔒</span>
                            <span style="font-weight: 600; font-size: 0.82rem; color: var(--text-primary);">Secure & Private</span>
                        </div>
                        <p style="font-size: 0.72rem; color: #94A3B8; margin: 0; line-height: 1.4;">Your data is completely safe.</p>
                    </div>
                    <div>
                        <div style="display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.25rem;">
                            <span style="font-size: 1rem; color: #F59E0B;">😊</span>
                            <span style="font-weight: 600; font-size: 0.82rem; color: var(--text-primary);">Easy to Use</span>
                        </div>
                        <p style="font-size: 0.72rem; color: #94A3B8; margin: 0; line-height: 1.4;">Intuitive UI for everyone.</p>
                    </div>
                    <div>
                        <div style="display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.25rem;">
                            <span style="font-size: 1rem; color: #EF4444;">🕒</span>
                            <span style="font-weight: 600; font-size: 0.82rem; color: var(--text-primary);">Time Saving</span>
                        </div>
                        <p style="font-size: 0.72rem; color: #94A3B8; margin: 0; line-height: 1.4;">Automate repetitive tasks.</p>
                    </div>
                </div>
            </div>
        """)

    with col_bottom_right:
        render_html("""
            <div style="
                background: var(--card-bg);
                border: 1px solid var(--card-border);
                border-radius: 16px;
                padding: 1.8rem;
                height: 100%;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
            ">
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.4rem;">
                    <span style="color: #6366F1; font-size: 1.1rem;">📖</span>
                    <h3 style="margin: 0; font-size: 1.15rem; font-weight: 700; color: var(--text-primary); border: none; padding: 0;">Your Data Journey</h3>
                </div>
                <p style="font-size: 0.82rem; color: var(--text-secondary); margin: 0 0 2rem 0;">From raw data to actionable insights in 4 simple steps.</p>
                
                <div style="display: flex; align-items: flex-start; justify-content: space-between; position: relative;">
                    <!-- Connector line -->
                    <div style="
                        position: absolute;
                        top: 20px;
                        left: 30px;
                        right: 30px;
                        height: 2px;
                        background: repeating-linear-gradient(to right, var(--card-border-dashed) 0px, var(--card-border-dashed) 4px, transparent 4px, transparent 8px);
                        z-index: 1;
                    "></div>
                    
                    <div style="text-align: center; width: 75px; z-index: 2;">
                        <div style="
                            width: 40px;
                            height: 40px;
                            border-radius: 50%;
                            background: #EEF2FF;
                            border: 2px solid #6366F1;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-size: 1.1rem;
                            margin: 0 auto 0.6rem auto;
                        ">📥</div>
                        <div style="font-weight: 700; font-size: 0.78rem; color: var(--text-primary);">1 Upload</div>
                        <div style="font-size: 0.65rem; color: var(--text-muted); margin-top: 0.15rem; line-height: 1.3;">Import dataset.</div>
                    </div>
                    
                    <div style="text-align: center; width: 75px; z-index: 2;">
                        <div style="
                            width: 40px;
                            height: 40px;
                            border-radius: 50%;
                            background: #FFF7ED;
                            border: 2px solid #F97316;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-size: 1.1rem;
                            margin: 0 auto 0.6rem auto;
                        ">🧼</div>
                        <div style="font-weight: 700; font-size: 0.78rem; color: var(--text-primary);">2 Clean</div>
                        <div style="font-size: 0.65rem; color: var(--text-muted); margin-top: 0.15rem; line-height: 1.3;">Auto clean.</div>
                    </div>
                    
                    <div style="text-align: center; width: 75px; z-index: 2;">
                        <div style="
                            width: 40px;
                            height: 40px;
                            border-radius: 50%;
                            background: #ECFDF5;
                            border: 2px solid #10B981;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-size: 1.1rem;
                            margin: 0 auto 0.6rem auto;
                        ">📈</div>
                        <div style="font-weight: 700; font-size: 0.78rem; color: var(--text-primary);">3 Analyze</div>
                        <div style="font-size: 0.65rem; color: var(--text-muted); margin-top: 0.15rem; line-height: 1.3;">Explore trends.</div>
                    </div>
                    
                    <div style="text-align: center; width: 75px; z-index: 2;">
                        <div style="
                            width: 40px;
                            height: 40px;
                            border-radius: 50%;
                            background: #EFF6FF;
                            border: 2px solid #3B82F6;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-size: 1.1rem;
                            margin: 0 auto 0.6rem auto;
                        ">💡</div>
                        <div style="font-weight: 700; font-size: 0.78rem; color: var(--text-primary);">4 Discover</div>
                        <div style="font-size: 0.65rem; color: var(--text-muted); margin-top: 0.15rem; line-height: 1.3;">Get insights.</div>
                    </div>
                </div>
            </div>
        """)

    # ── 6. FOOTER ──
    render_html("<div style='height:3rem;'></div>")
    render_html("""
        <div style="text-align: center; padding: 1.5rem 0; border-top: 1px solid var(--card-border); margin-top: 1rem;">
            <p style="font-size: 0.82rem; color: #8B5CF6; font-weight: 600; margin: 0;">
                Data Pilot — Clean Data. Clear Insights. Confident Decisions. 🚀
            </p>
        </div>





        <!-- About Modal -->
        <div id="about-modal" class="modal-overlay">
            <div class="modal-content" style="text-align: center;">
                <a href="#" class="modal-close">&times;</a>
                <div style="font-size: 3rem; margin-bottom: 0.5rem;">📊</div>
                <h3 style="margin-top: 0; color: var(--text-primary); font-weight: 800;">Data Pilot</h3>
                <p style="color: #64748B; font-size: 0.82rem; margin-bottom: 1.5rem;">Version 1.0.0 (Release Build)</p>
                <p style="color: var(--text-secondary); font-size: 0.88rem; line-height: 1.6;">
                    Data Pilot is a professional dataset cleaning and analysis assistant built to help analysts import, clean, visualize, compare, and report data insights.
                </p>
                <div style="margin-top: 2rem; border-top: 1px solid var(--card-border); padding-top: 1rem; font-size: 0.78rem; color: #94A3B8;">
                    © 2026 Data Pilot Project. All rights reserved.
                </div>
            </div>
        </div>
    """)
# Sidebar Navigation (only shown after dataset is loaded)
# =============================================================================

NAV_ITEMS = [
    ("📋  Dataset Overview",     "Dashboard"),
    ("🧹  Data Cleaning",        "Cleaning"),
    ("📊  Before vs After",      "BeforeAfter"),
    ("📈  Analysis",             "Analysis"),
    ("📑  Reports",              "Reports"),
]


def render_sidebar():
    """Build the dark sidebar with branding, navigation, and dataset status."""
    with st.sidebar:


        # ---- Build flat list of labels for the radio widget ----
        all_labels = []
        label_to_page = {}

        st.markdown("### Navigation")
        for label, page_key in NAV_ITEMS:
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

        # ---- Theme Toggle ----
        st.markdown("### Appearance")
        current_theme = st.session_state.get("theme", "dark")
        theme_options = ["🌙 Dark", "☀️ Light"]
        theme_index = 0 if current_theme == "dark" else 1

        def on_theme_change():
            selected = st.session_state["theme_toggle"]
            st.session_state["theme"] = "dark" if "Dark" in selected else "light"

        st.markdown("""
            <style>
            [data-testid="stSidebar"] div[data-testid="stRadio"][aria-label="Theme"] label p,
            [data-testid="stSidebar"] div[data-testid="stRadio"][aria-label="Theme"] label span {
                font-size: 0.72rem !important;
            }
            </style>
        """, unsafe_allow_html=True)
        st.radio(
            "Theme",
            options=theme_options,
            index=theme_index,
            key="theme_toggle",
            on_change=on_theme_change,
            label_visibility="collapsed",
            horizontal=True,
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
                left: 0;
                width: var(--sidebar-width, 245px);
                padding: 0.6rem 1rem;
                font-size: 0.65rem;
                color: var(--text-muted);
                letter-spacing: 0.02em;
            ">
                Data Pilot v1.0
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
    # Check for reload/reset query parameters to go home
    try:
        action = st.query_params.get("action")
        theme = st.query_params.get("theme")
    except AttributeError:
        # Fallback for older Streamlit versions
        qp = st.experimental_get_query_params()
        action = qp.get("action", [None])[0]
        theme = qp.get("theme", [None])[0]

    if theme in ["light", "dark"]:
        st.session_state["theme"] = theme
        try:
            del st.query_params["theme"]
        except Exception:
            pass

    if action == "reset":
        st.session_state["original_df"] = None
        st.session_state["cleaned_df"] = None
        st.session_state["file_name"] = None
        st.session_state["file_size"] = None
        st.session_state["cleaning_steps"] = []
        st.session_state["cleaning_history"] = []
        # Keep the selected theme or default to dark
        st.session_state["theme"] = st.session_state.get("theme", "dark")
        if "landing_uploader" in st.session_state:
            del st.session_state["landing_uploader"]
        
        try:
            st.query_params.clear()
        except AttributeError:
            st.experimental_set_query_params()
        st.rerun()

    # Dynamic theme variables configuration
    current_theme = st.session_state.get("theme", "dark")
    if current_theme == "dark":
        theme_vars = """
        :root {
            --app-bg: #0B0A14;
            --app-bg-image: radial-gradient(circle at 80% 20%, rgba(99, 102, 241, 0.12) 0%, rgba(139, 92, 246, 0.12) 30%, transparent 70%),
                            radial-gradient(circle at 10% 80%, rgba(139, 92, 246, 0.08) 0%, rgba(99, 102, 241, 0.08) 40%, transparent 70%);
            --text-primary: #FFFFFF;
            --text-secondary: #94A3B8;
            --text-muted: #64748B;
            --card-bg: #161525;
            --card-border: #252438;
            --card-border-dashed: #3D3C57;
            --mockup-card-bg: #0F0E1C;

            /* Override styles.css variables for dark theme */
            --bg-body: #0B0A14 !important;
            --bg-card: #161525 !important;
            --border-color: #252438 !important;
            --text-primary: #FFFFFF !important;
            --text-secondary: #94A3B8 !important;
            --text-muted: #64748B !important;

            /* Sidebar custom variables */
            --bg-dark: #0B0A14 !important;
            --bg-sidebar: #161525 !important;
            --text-sidebar: #94A3B8 !important;
            --text-white: #FFFFFF !important;
        }
        .modal-content {
            background-color: #161525 !important;
            border: 1px solid #252438 !important;
            color: #FFFFFF !important;
        }
        .modal-content h3 {
            color: #FFFFFF !important;
        }
        .modal-content p {
            color: #94A3B8 !important;
        }
        """
    else:
        theme_vars = """
        :root {
            --app-bg: #FAF9FD;
            --app-bg-image: radial-gradient(circle at 80% 20%, rgba(219, 234, 254, 0.45) 0%, rgba(243, 232, 255, 0.45) 30%, transparent 70%),
                            radial-gradient(circle at 10% 80%, rgba(243, 232, 255, 0.35) 0%, rgba(238, 242, 255, 0.35) 40%, transparent 70%);
            --text-primary: #0F172A;
            --text-secondary: #475569;
            --text-muted: #64748B;
            --card-bg: #FFFFFF;
            --card-border: #E2E8F0;
            --card-border-dashed: #CBD5E1;
            --mockup-card-bg: #FAF9FD;

            /* Override styles.css variables for light theme */
            --bg-body: #FAF9FD !important;
            --bg-card: #FFFFFF !important;
            --border-color: #E2E8F0 !important;
            --text-primary: #0F172A !important;
            --text-secondary: #475569 !important;
            --text-muted: #64748B !important;

            /* Sidebar custom variables */
            --bg-dark: #FAF9FD !important;
            --bg-sidebar: #FFFFFF !important;
            --text-sidebar: #475569 !important;
            --text-white: #0F172A !important;
        }
        .modal-content {
            background-color: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            color: #0F172A !important;
        }
        .modal-content h3 {
            color: #0F172A !important;
        }
        .modal-content p {
            color: #475569 !important;
        }
        """

    # Inject global styles and variables
    st.markdown(f"""
        <style>
        {theme_vars}
        
        /* Layout resets */
        [data-testid="stHeader"] {{ display: none !important; }}
        
        /* Offset main content container by header height */
        .block-container {{
            max-width: 1200px !important;
            padding-top: 5.2rem !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
        }}
        
        /* Offset sidebar by header height */
        [data-testid="stSidebar"] {{
            margin-top: 52px !important;
        }}
        
        /* Unified Global Text Accessibility rules */
        [data-testid="stMain"],
        [data-testid="stMain"] p,
        [data-testid="stMain"] span:not(.badge):not([style*="color"]),
        [data-testid="stMain"] h1,
        [data-testid="stMain"] h2,
        [data-testid="stMain"] h3,
        [data-testid="stMain"] h4,
        [data-testid="stMain"] h5,
        [data-testid="stMain"] h6,
        [data-testid="stMain"] label,
        [data-testid="stMain"] [data-testid="stWidgetLabel"],
        [data-testid="stMain"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stMain"] .streamlit-expanderHeader,
        [data-testid="stMain"] .streamlit-expanderHeader p,
        [data-testid="stMain"] .streamlit-expanderHeader span,
        [data-testid="stMain"] button[data-baseweb="tab"] *,
        [data-testid="stMain"] button[data-baseweb="tab"] p,
        [data-testid="stMain"] button[data-baseweb="tab"] span {{
            color: var(--text-primary) !important;
        }}
        
        [data-testid="stMain"] div[data-baseweb="select"] *,
        [data-testid="stMain"] input {{
            color: var(--text-primary) !important;
        }}
        
        /* Hide Sidebar Toggle Arrows (Collapsed & Expanded) */
        [data-testid="collapsedControl"] {{
            display: none !important;
        }}
        [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] {{
            display: none !important;
        }}
        
        /* Dropdown menu for top bar */
        details.dropdown {{
            position: relative;
            display: inline-block;
        }}
        details.dropdown summary::-webkit-details-marker {{
            display: none !important;
        }}
        details.dropdown summary {{
            list-style: none !important;
            outline: none !important;
        }}
        .dropbtn {{
            background: #1E1C30 !important;
            border: 1px solid #32304C !important;
            color: #CBD5E1 !important;
            font-size: 1.05rem !important;
            font-weight: 700 !important;
            cursor: pointer !important;
            padding: 0.35rem 0.85rem !important;
            border-radius: 8px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            transition: all 0.2s ease !important;
            user-select: none !important;
        }}
        .dropbtn:hover {{
            color: white !important;
            background: #2B2945 !important;
            border-color: #434164 !important;
        }}
        .dropdown-content {{
            position: absolute;
            right: 0;
            background-color: #11101D;
            min-width: 175px;
            box-shadow: 0px 8px 24px rgba(0, 0, 0, 0.55);
            z-index: 10000;
            border-radius: 8px;
            border: 1px solid #2D2C3F;
            margin-top: 0.5rem;
        }}
        .dropdown-content a {{
            color: #CBD5E1;
            padding: 10px 16px;
            text-decoration: none;
            display: block;
            font-size: 0.8rem;
            font-family: 'Plus Jakarta Sans', sans-serif;
            text-align: left;
            transition: background 0.2s ease;
        }}
        .dropdown-content a:hover {{
            background-color: #1F1E2E;
            color: white;
            border-radius: 8px;
        }}

        /* Modals style */
        .modal-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(4px);
            z-index: 99999;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .modal-overlay:target {{
            opacity: 1;
            visibility: visible;
        }}
        .modal-content {{
            padding: 2rem;
            border-radius: 16px;
            max-width: 500px;
            width: 90%;
            position: relative;
            box-shadow: 0 20px 40px rgba(0,0,0,0.4);
            font-family: 'Plus Jakarta Sans', sans-serif;
        }}
        .modal-close {{
            position: absolute;
            top: 1rem;
            right: 1rem;
            font-size: 1.5rem;
            text-decoration: none;
        }}
        .modal-close:hover {{
            color: var(--text-primary) !important;
        }}
        </style>
    """, unsafe_allow_html=True)

    # Render global top bar (constant navbar)
    st.markdown("""
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: #0B0A14;
            padding: 0.6rem 2.5rem 0.6rem 3.6rem;
            width: 100%;
            position: fixed;
            top: 0;
            left: 0;
            z-index: 9999;
            border-bottom: 1px solid #1F1E2E;
        ">
            <a href="/?action=reset" target="_self" style="display: flex; align-items: center; gap: 0.6rem; text-decoration: none;">
                <div style="
                    background: linear-gradient(135deg, #6366F1, #8B5CF6);
                    border-radius: 6px;
                    width: 28px;
                    height: 28px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                    font-size: 0.95rem;
                ">📊</div>
                <span style="color: white; font-weight: 700; font-size: 1.1rem; letter-spacing: -0.02em;">Data Pilot</span>
            </a>
            <div style="display: flex; align-items: center; gap: 1.2rem;">
                <details class="dropdown">
                    <summary class="dropbtn">&#8942; Menu</summary>
                    <div class="dropdown-content">
                        <a href="/?action=reset" target="_self">&#127968; Home / Reset</a>
                        <a href="#about-modal">&#8505;&#65039; About</a>
                    </div>
                </details>
            </div>
        </div>

        <!-- About Modal -->
        <div id="about-modal" class="modal-overlay">
            <div class="modal-content" style="text-align: center;">
                <a href="#" class="modal-close">&times;</a>
                <div style="font-size: 3rem; margin-bottom: 0.5rem;">📊</div>
                <h3 style="margin-top: 0; font-weight: 800;">Data Pilot</h3>
                <p style="color: #64748B; font-size: 0.82rem; margin-bottom: 1.5rem;">Version 1.0.0 (Release Build)</p>
                <p style="font-size: 0.88rem; line-height: 1.6;">
                    Data Pilot is a professional dataset cleaning and analysis assistant built to help analysts import, clean, visualize, compare, and report data insights.
                </p>
                <div style="margin-top: 2rem; border-top: 1px solid var(--card-border); padding-top: 1rem; font-size: 0.78rem; color: #94A3B8;">
                    © 2026 Data Pilot Project. All rights reserved.
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # If no dataset is loaded, show the landing page
    if st.session_state.get("original_df") is None:
        render_landing_page()
        return

    # Dataset is loaded — inject page compactness styles and show sidebar + routed page
    st.markdown("""
        <style>
        /* Unified compact font-size scaling for loaded workspace pages */
        .block-container p,
        .block-container span:not(.badge):not([style*="color"]),
        .block-container li,
        .block-container label,
        .block-container button,
        .block-container input,
        .block-container select,
        .block-container textarea,
        .block-container div[data-baseweb="select"] *,
        .block-container [data-testid="stWidgetLabel"],
        .block-container [data-testid="stWidgetLabel"] p,
        .block-container [data-testid="stWidgetLabel"] span,
        .block-container .stRadio [role="radiogroup"] label,
        .block-container .stRadio [role="radiogroup"] label p,
        .block-container .stRadio [role="radiogroup"] label span,
        .block-container button[data-baseweb="tab"] *,
        .block-container button[data-baseweb="tab"] p,
        .block-container button[data-baseweb="tab"] span,
        .block-container .streamlit-expanderHeader,
        .block-container .streamlit-expanderHeader p,
        .block-container .streamlit-expanderHeader span,
        .block-container [data-testid="stMetricLabel"] *,
        .block-container [data-testid="stMetricValue"],
        .block-container .stTable td,
        .block-container .stTable th,
        .block-container div[data-testid="stDataFrame"] * {
            font-size: 0.8rem !important;
        }
        .block-container h1 {
            font-size: 1.4rem !important;
        }
        .block-container h2 {
            font-size: 1.15rem !important;
        }
        .block-container h3 {
            font-size: 0.95rem !important;
        }
        .block-container h4,
        .block-container h5,
        .block-container h6 {
            font-size: 0.85rem !important;
        }
        </style>
    """, unsafe_allow_html=True)

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
