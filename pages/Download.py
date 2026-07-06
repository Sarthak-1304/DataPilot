"""
Download Page
=============
Export cleaned datasets and reports in multiple formats.
"""

import streamlit as st


def render_download():
    """Render the Download page."""
    st.markdown(
        """
        <div class="top-header">
            <h2>⬇️ Download</h2>
            <p>Download your cleaned dataset and reports.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.session_state.get("original_df") is None:
        st.markdown(
            """
            <div class="content-card animate-in">
                <div class="empty-state">
                    <div class="empty-icon">⬇️</div>
                    <h3>No Dataset Loaded</h3>
                    <p>Upload a CSV or Excel file first to download cleaned files here.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("⬇️ Download options will be implemented in the next step.")
