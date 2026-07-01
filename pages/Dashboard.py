"""
Dashboard Page
==============
Home page displaying key metrics, recent activity, and dataset overview.
"""

import streamlit as st


def render_dashboard():
    """Render the Dashboard home page."""
    st.markdown(
        """
        <div class="top-header">
            <h2>🏠 Dashboard</h2>
            <p>Welcome to Data Cleaning Studio — your overview at a glance.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Placeholder — will be fully implemented in the next step
    if st.session_state.get("original_df") is None:
        st.markdown(
            """
            <div class="content-card">
                <div class="empty-state">
                    <div class="empty-icon">📊</div>
                    <h3>No Dataset Loaded</h3>
                    <p>Upload a CSV or Excel file to see your dashboard metrics, activity log, and data quality score.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("📊 Dashboard content will be implemented in the next step.")
