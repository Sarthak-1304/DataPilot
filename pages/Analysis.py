"""
Data Analysis Page
==================
Automatic dataset profiling with interactive Plotly visualizations.
"""

import streamlit as st


def render_analysis():
    """Render the Data Analysis page."""
    st.markdown(
        """
        <div class="top-header">
            <h2>📊 Data Analysis</h2>
            <p>Explore your dataset with automated profiling and interactive charts.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.session_state.get("original_df") is None:
        st.warning("⚠️ Please upload a dataset first.")
    else:
        st.info("📊 Analysis features will be implemented in the next step.")
