"""
Before vs After Page
====================
Side-by-side comparison of original and cleaned datasets.
"""

import streamlit as st


def render_before_after():
    """Render the Before vs After comparison page."""
    st.markdown(
        """
        <div class="top-header">
            <h2>🔄 Before vs After</h2>
            <p>Compare your original and cleaned datasets side by side.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.session_state.get("original_df") is None:
        st.warning("⚠️ Please upload a dataset first.")
    else:
        st.info("🔄 Comparison view will be implemented in the next step.")
