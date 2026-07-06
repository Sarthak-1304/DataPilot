"""
Reports Page
============
Generate and preview professional PDF cleaning reports.
"""

import streamlit as st


def render_reports():
    """Render the Reports page."""
    st.markdown(
        """
        <div class="top-header">
            <h2>📄 Reports</h2>
            <p>Generate professional PDF reports of your cleaning process.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.session_state.get("original_df") is None:
        st.markdown(
            """
            <div class="content-card animate-in">
                <div class="empty-state">
                    <div class="empty-icon">📄</div>
                    <h3>No Dataset Loaded</h3>
                    <p>Upload a CSV or Excel file first to generate data reports here.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("📄 Report generation will be implemented in the next step.")
