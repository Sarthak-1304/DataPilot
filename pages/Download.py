"""
Download Page
=============
Export cleaned datasets and quick report files.
"""

import streamlit as st
import pandas as pd
import io

def render_download():
    """Render the Download page."""
    st.markdown(
        """
        <div class="top-header">
            <h2>⬇️ Download Center</h2>
            <p>Export your cleaned dataset and access executive report generation.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    orig_df = st.session_state.get("original_df")
    cleaned_df = st.session_state.get("cleaned_df")
    working_df = cleaned_df if cleaned_df is not None else orig_df

    if working_df is None:
        st.markdown(
            """
            <div class="content-card animate-in">
                <div class="empty-state" style="text-align: center; padding: 3rem 1.5rem;">
                    <div style="font-size: 3rem; margin-bottom: 0.6rem; opacity: 0.4;">⬇️</div>
                    <h3 style="border:none; padding:0; margin-bottom:0.4rem;">No Dataset Loaded</h3>
                    <p style="color:var(--text-secondary); font-size:0.9rem; max-width:420px; margin:0 auto; line-height:1.6;">
                        Upload a CSV or Excel file first to download cleaned dataset files and reports here.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    file_name = st.session_state.get("file_name", "dataset")
    base_name = file_name.rsplit(".", 1)[0].lower().replace(" ", "_")

    st.markdown("### 💾 Dataset Export Options")
    st.caption("Download your processed dataset in standard data engineering formats.")

    c1, c2, c3, c4 = st.columns(4)

    # 1. CSV
    with c1:
        st.markdown("""
            <div class="content-card" style="text-align:center;">
                <div style="font-size:2rem; margin-bottom:0.3rem;">📄</div>
                <div style="font-weight:700; font-size:0.9rem;">CSV File</div>
                <div style="font-size:0.72rem; color:var(--text-muted); margin-bottom:0.8rem;">Comma Separated Values</div>
            </div>
        """, unsafe_allow_html=True)
        csv_bytes = working_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download CSV",
            data=csv_bytes,
            file_name=f"{base_name}_cleaned.csv",
            mime="text/csv",
            use_container_width=True,
            type="primary"
        )

    # 2. Excel
    with c2:
        st.markdown("""
            <div class="content-card" style="text-align:center;">
                <div style="font-size:2rem; margin-bottom:0.3rem;">📊</div>
                <div style="font-weight:700; font-size:0.9rem;">Excel Sheet</div>
                <div style="font-size:0.72rem; color:var(--text-muted); margin-bottom:0.8rem;">Microsoft Excel (.xlsx)</div>
            </div>
        """, unsafe_allow_html=True)
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            working_df.to_excel(writer, index=False, sheet_name="Cleaned Data")
        st.download_button(
            label="📥 Download Excel",
            data=excel_buffer.getvalue(),
            file_name=f"{base_name}_cleaned.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    # 3. Parquet
    with c3:
        st.markdown("""
            <div class="content-card" style="text-align:center;">
                <div style="font-size:2rem; margin-bottom:0.3rem;">⚡</div>
                <div style="font-weight:700; font-size:0.9rem;">Parquet File</div>
                <div style="font-size:0.72rem; color:var(--text-muted); margin-bottom:0.8rem;">Compressed Columnar Format</div>
            </div>
        """, unsafe_allow_html=True)
        pq_buffer = io.BytesIO()
        working_df.to_parquet(pq_buffer, index=False)
        st.download_button(
            label="📥 Download Parquet",
            data=pq_buffer.getvalue(),
            file_name=f"{base_name}_cleaned.parquet",
            mime="application/octet-stream",
            use_container_width=True
        )

    # 4. JSON
    with c4:
        st.markdown("""
            <div class="content-card" style="text-align:center;">
                <div style="font-size:2rem; margin-bottom:0.3rem;">⚙️</div>
                <div style="font-weight:700; font-size:0.9rem;">JSON Array</div>
                <div style="font-size:0.72rem; color:var(--text-muted); margin-bottom:0.8rem;">Web Data Payload</div>
            </div>
        """, unsafe_allow_html=True)
        json_bytes = working_df.to_json(orient="records", indent=2).encode('utf-8')
        st.download_button(
            label="📥 Download JSON",
            data=json_bytes,
            file_name=f"{base_name}_cleaned.json",
            mime="application/json",
            use_container_width=True
        )

    st.markdown("<br><hr style='border: 0.5px solid var(--border-color);'><br>", unsafe_allow_html=True)
    st.markdown("### 📑 Looking for Executive Business Reports?")
    
    rc1, rc2 = st.columns([3, 1])
    with rc1:
        st.markdown("""
            Generate PDF, HTML, Word, PowerPoint, and Excel executive report packages with live customizable previews, branding, and section builder on the Reports page.
        """)
    with rc2:
        if st.button("📑 Open Report Builder", type="primary", use_container_width=True):
            st.session_state["current_page"] = "Reports"
            st.rerun()
