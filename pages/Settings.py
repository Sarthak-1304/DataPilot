"""
Settings Page
=============
App configuration, theme toggle, and about section.
"""

import streamlit as st


def render_settings():
    """Render the Settings & About page."""
    st.markdown(
        """
        <div class="top-header">
            <h2>⚙️ Settings</h2>
            <p>Configure application preferences and view project information.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            <div class="content-card">
                <h3>🎨 Theme</h3>
                <p style="font-size: 0.85rem; color: #64748B;">
                    Theme settings will be implemented in a later step.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="content-card">
                <h3>❓ About</h3>
                <p style="font-size: 0.85rem; color: #64748B; line-height: 1.7;">
                    <strong>Data Cleaning Studio</strong> is a professional data cleaning
                    and analysis tool built with Streamlit, Pandas, and Plotly.<br><br>
                    Designed for data analysts who need a fast, visual, and reliable
                    way to clean and prepare datasets for analysis.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
