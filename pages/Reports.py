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
        st.warning("⚠️ Please upload a dataset first.")
    else:
        st.info("📄 Report generation will be implemented in the next step.")
