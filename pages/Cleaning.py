"""
Data Cleaning Page
==================
Interactive data cleaning operations with preview-before-apply.
"""

import streamlit as st


def render_cleaning():
    """Render the Clean Dataset page."""
    st.markdown(
        """
        <div class="top-header">
            <h2>🧹 Clean Dataset</h2>
            <p>Select and apply cleaning operations with live preview.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.session_state.get("original_df") is None:
        st.warning("⚠️ Please upload a dataset first.")
    else:
        st.info("🧹 Cleaning operations will be implemented in the next step.")
