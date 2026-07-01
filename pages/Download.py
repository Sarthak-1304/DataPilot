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
        st.warning("⚠️ Please upload a dataset first.")
    else:
        st.info("⬇️ Download options will be implemented in the next step.")
