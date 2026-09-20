"""
Reports & Report Builder Page
==============================
Executive Report Builder providing live customizable previews, multi-theme branding,
section toggling, automatic versioning, report quality scoring, multi-format exports,
and SQLite history persistence.
"""

import streamlit as st
import pandas as pd
import numpy as np
import datetime
import json
import os
import textwrap
import plotly.graph_objects as go
from typing import Dict, Any, List

from utils.report_builder import (
    collect_report_data,
    calculate_report_quality_score,
)
from utils.report_exporter import (
    export_html_report,
    export_markdown_report,
    export_excel_summary,
    export_csv_summary,
    export_json_report,
    export_pdf_report,
    export_docx_report,
    export_pptx_report,
)
import importlib
import utils.sync_manager
importlib.reload(utils.sync_manager)
from utils.sync_manager import (
    save_report_meta,
    list_reports,
    delete_report,
    get_next_report_version,
)


# ─── Helper HTML Dedent Renderer ──────────────────────────────────────
def render_html(html_str: str):
    """Renders HTML by stripping blank lines and dedenting to prevent Streamlit Markdown code block parsing."""
    dedented = textwrap.dedent(html_str)
    cleaned = "\n".join([line for line in dedented.splitlines() if line.strip()])
    st.markdown(cleaned, unsafe_allow_html=True)


def _alert(text: str, level: str = "success"):
    """Render a clean custom alert banner."""
    bg = "rgba(16, 185, 129, 0.08)" if level == "success" else "rgba(239, 68, 68, 0.08)"
    border = "#10B981" if level == "success" else "#EF4444"
    icon = "✅" if level == "success" else "❌"
    st.markdown(f"""
    <div style="background-color: {bg}; border: 1px solid {border}; padding: 0.65rem 0.95rem; border-radius: 8px; font-size: 0.85rem; margin-bottom: 1rem; font-weight: 500; display: flex; align-items: center; gap: 0.5rem; width: 100%;">
        <span style="font-size: 1.1rem; line-height: 1;">{icon}</span>
        <span style="color: var(--text-primary);">{text}</span>
    </div>
    """, unsafe_allow_html=True)


# ─── Circular Gauge Helper ──────────────────────────────────────────
def draw_report_score_gauge(score: int, status_text: str) -> go.Figure:
    """Create a semi-circular gauge indicator for Report Quality Score."""
    color = "#10B981" if score >= 80 else "#3B82F6" if score >= 60 else "#F59E0B"
    current_theme = st.session_state.get("theme", "dark")
    text_primary = "#FFFFFF" if current_theme == "dark" else "#0F172A"
    border_color = "#252438" if current_theme == "dark" else "#E2E8F0"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={'font': {'size': 36, 'color': color, 'family': 'Inter'}, 'suffix': "%"},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': '#64748B'},
            'bar': {'color': color},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 1,
            'bordercolor': border_color,
            'steps': [
                {'range': [0, 50], 'color': 'rgba(239, 68, 68, 0.08)'},
                {'range': [50, 80], 'color': 'rgba(245, 158, 11, 0.08)'},
                {'range': [80, 100], 'color': 'rgba(16, 185, 129, 0.08)'}
            ],
        }
    ))
    fig.update_layout(
        height=150,
        margin=dict(l=30, r=30, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# =============================================================================
# Main Page Renderer
# =============================================================================

def render_reports():
    """Render the full Reports & Report Builder page."""
    # Top Header
    render_html("""
        <div class="top-header">
            <h2>📑 Executive Reports & Builder</h2>
            <p>Generate, customize, preview, version, and export enterprise-grade reports from your data pipeline.</p>
        </div>
    """)

    # Check if dataset loaded
    if st.session_state.get("original_df") is None:
        render_html("""
            <div class="content-card animate-in">
                <div class="empty-state" style="text-align: center; padding: 3rem 1.5rem;">
                    <div style="font-size: 3rem; margin-bottom: 0.6rem; opacity: 0.4;">📄</div>
                    <h3 style="border:none; padding:0; margin-bottom:0.4rem;">No Dataset Loaded</h3>
                    <p style="color:var(--text-secondary); font-size:0.9rem; max-width:420px; margin:0 auto; line-height:1.6;">
                        Upload a CSV or Excel file or load a project first to build and export executive business reports.
                    </p>
                </div>
            </div>
        """)
        return

    # Collect report data
    report_data = collect_report_data()
    if not report_data:
        st.error("Failed to load dataset metadata.")
        return

    file_name = report_data.get("file_name", "Dataset")
    project_id = report_data.get("project_id", "default_project")
    project_name = report_data.get("project_name", file_name)
    next_ver = get_next_report_version(project_id)

    # ── Top Hero Metadata Bar ──
    render_html(f"""
        <div style="background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 1rem 1.4rem; margin-bottom: 1.5rem; display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 1rem;">
            <div>
                <div style="font-size: 0.72rem; color: var(--text-muted); font-weight: 700; text-transform: uppercase;">Active Project</div>
                <div style="font-size: 1.1rem; font-weight: 800; color: var(--text-primary); margin-top: 0.15rem;">📁 {project_name}</div>
            </div>
            <div>
                <div style="font-size: 0.72rem; color: var(--text-muted); font-weight: 700; text-transform: uppercase;">Dataset</div>
                <div style="font-size: 0.9rem; font-weight: 700; color: var(--text-primary); margin-top: 0.15rem;">{file_name}</div>
            </div>
            <div>
                <div style="font-size: 0.72rem; color: var(--text-muted); font-weight: 700; text-transform: uppercase;">Report Version</div>
                <div style="font-size: 0.9rem; font-weight: 700; color: #8B5CF6; margin-top: 0.15rem;">v{next_ver}.0 Draft</div>
            </div>
            <div>
                <div style="font-size: 0.72rem; color: var(--text-muted); font-weight: 700; text-transform: uppercase;">Workflow Status</div>
                <div style="display: flex; gap: 0.3rem; margin-top: 0.2rem;">
                    <span style="font-size: 0.68rem; padding: 0.1rem 0.4rem; background: rgba(16,185,129,0.15); color: #10B981; border-radius: 4px; font-weight: 700;">Dataset ✔</span>
                    <span style="font-size: 0.68rem; padding: 0.1rem 0.4rem; background: rgba(16,185,129,0.15); color: #10B981; border-radius: 4px; font-weight: 700;">Cleaning ✔</span>
                    <span style="font-size: 0.68rem; padding: 0.1rem 0.4rem; background: rgba(16,185,129,0.15); color: #10B981; border-radius: 4px; font-weight: 700;">Analysis ✔</span>
                    <span style="font-size: 0.68rem; padding: 0.1rem 0.4rem; background: rgba(99,102,241,0.15); color: #6366F1; border-radius: 4px; font-weight: 700;">Report Ready</span>
                </div>
            </div>
        </div>
    """)

    # ── Report Preset Templates Row ──
    st.markdown("#### ⚡ Quick Report Preset Templates")
    preset_cols = st.columns(6)
    
    all_possible_sections = [
        "Executive Summary",
        "Dataset Overview",
        "Data Cleaning Report",
        "Before vs After",
        "Analysis Summary",
        "Dashboard KPIs",
        "Business Insights",
        "Recommendations",
        "Appendix"
    ]

    preset_templates = {
        "Executive Summary": ["Executive Summary", "Dataset Overview", "Business Insights", "Recommendations"],
        "Full Business Report": ["Executive Summary", "Dataset Overview", "Data Cleaning Report", "Before vs After", "Analysis Summary", "Dashboard KPIs", "Business Insights", "Recommendations", "Appendix"],
        "Data Quality Audit": ["Dataset Overview", "Data Cleaning Report", "Before vs After", "Recommendations", "Appendix"],
        "Sales & Revenue": ["Executive Summary", "Dashboard KPIs", "Business Insights", "Recommendations"],
        "Technical Analytics": ["Dataset Overview", "Analysis Summary", "Appendix"],
        "Minimal Brief": ["Executive Summary", "Business Insights"]
    }

    selected_preset = st.session_state.get("report_preset", "Full Business Report")

    for i, (name, sections) in enumerate(preset_templates.items()):
        col = preset_cols[i]
        with col:
            btn_type = "primary" if name == selected_preset else "secondary"
            if st.button(name, key=f"preset_{i}", use_container_width=True, type=btn_type):
                st.session_state["report_preset"] = name
                st.session_state["report_sections"] = sections
                # Sync individual checkbox widget keys so Streamlit picks up
                # the new values on rerun (it ignores `value=` when the key
                # already exists in session_state).
                for sec in all_possible_sections:
                    st.session_state[f"sec_chk_{sec}"] = (sec in sections)
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # =============================================================================
    # TWO-COLUMN REPORT BUILDER LAYOUT
    # =============================================================================
    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.markdown("### 🛠️ Report Properties & Customization")

        # Branding & Meta Form
        with st.expander("🏢 Branding & Header Information", expanded=True):
            rep_title = st.text_input("Report Title", value=st.session_state.get("rep_title", f"Executive Data Report: {project_name}"), key="rep_title")
            rep_company = st.text_input("Company / Organization", value=st.session_state.get("rep_company", "Data Pilot Enterprise"), key="rep_company")
            rep_author = st.text_input("Author Name", value=st.session_state.get("rep_author", "Lead Data Analyst"), key="rep_author")
            rep_dept = st.text_input("Department / Unit", value=st.session_state.get("rep_dept", "Analytics & Insights Division"), key="rep_dept")
            rep_watermark = st.selectbox("Document Classification", options=["None", "CONFIDENTIAL", "INTERNAL USE ONLY", "DRAFT"], index=0, key="rep_watermark")

        # Theme & Styling
        with st.expander("🎨 Report Theme & Styling", expanded=True):
            theme_choice = st.selectbox("Report Styling Theme", options=["Corporate", "Modern", "Minimal", "Dark"], index=0, key="rep_theme")

        # Section Selector

        if "report_sections" not in st.session_state:
            st.session_state["report_sections"] = preset_templates["Full Business Report"]

        with st.expander("📋 Include Sections", expanded=True):
            st.markdown("<div style='font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.6rem;'>Check sections to include in your report:</div>", unsafe_allow_html=True)
            active_sections = []
            for sec in all_possible_sections:
                is_chk = st.checkbox(sec, value=(sec in st.session_state["report_sections"]), key=f"sec_chk_{sec}")
                if is_chk:
                    active_sections.append(sec)
            st.session_state["report_sections"] = active_sections

        # Report Configuration Dict
        config = {
            "title": rep_title,
            "company_name": rep_company,
            "author": rep_author,
            "department": rep_dept,
            "theme": theme_choice,
            "watermark": rep_watermark,
            "sections": active_sections
        }

    with col_right:
        # Report Quality Score Gauge
        quality_assessment = calculate_report_quality_score(config, report_data)
        rep_score = quality_assessment["score"]
        rep_status = quality_assessment["status"]

        score_c1, score_c2 = st.columns([1, 1])
        with score_c1:
            st.plotly_chart(draw_report_score_gauge(rep_score, rep_status), use_container_width=True)
        with score_c2:
            render_html(f"""
                <div class="content-card" style="margin-top: 0.5rem;">
                    <div style="font-size: 0.72rem; color: var(--text-muted); font-weight: 700; text-transform: uppercase;">Report Readiness Grade</div>
                    <div style="font-size: 1.2rem; font-weight: 800; color: #10B981; margin: 0.2rem 0 0.4rem 0;">{rep_status} ({rep_score}/100)</div>
                    <div style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.4;">
                        Includes <b>{len(active_sections)} sections</b>, <b>{len(report_data.get('business_insights', []))} insights</b>, and executive branding.
                    </div>
                </div>
            """)

        # AI Attribution & Confidence Badge
        ai_conf = report_data.get("ai_confidence", {})
        conf_score = ai_conf.get("score", 95)
        conf_level = ai_conf.get("level", "High")
        conf_reason = ai_conf.get("reason", "Generated from complete dataset statistical profiling.")
        is_ai = report_data.get("is_ai_generated", False)

        ai_badge_text = "✨ Generated using Data Pilot AI" if is_ai else "🤖 Data Pilot Analytical Engine"
        conf_color = "#10B981" if conf_score >= 85 else "#3B82F6" if conf_score >= 70 else "#F59E0B"

        header_btn_c1, header_btn_c2 = st.columns([3, 1])
        with header_btn_c1:
            st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 0.8rem; margin-bottom: 0.8rem;">
                    <span style="font-size: 0.78rem; font-weight: 700; color: #8B5CF6; background: rgba(139,92,246,0.12); padding: 0.2rem 0.6rem; border-radius: 100px;">{ai_badge_text}</span>
                    <span style="font-size: 0.75rem; color: var(--text-secondary);">Confidence: <b style="color: {conf_color};">{conf_score}% {conf_level}</b> ({conf_reason})</span>
                </div>
            """, unsafe_allow_html=True)
        with header_btn_c2:
            if st.button("🔄 Regenerate AI Content", key="btn_regen_ai_report", use_container_width=True):
                st.session_state["report_data_cache"] = collect_report_data(force_regenerate=True)
                _alert("AI Report content regenerated successfully!", "success")
                st.rerun()

        st.markdown("### 👁️ Live Report Preview")
        st.caption("This preview reflects your chosen theme, branding, enabled sections, and AI intelligence dynamically.")

        # Container for Preview Sheet
        preview_bg = "#1E293B" if theme_choice == "Dark" else "#FFFFFF"
        preview_text = "#F8FAFC" if theme_choice == "Dark" else "#0F172A"
        preview_border = "#334155" if theme_choice == "Dark" else "#E2E8F0"

        # Watermark banner
        watermark_html = f'<div style="text-align: center; color: #EF4444; font-weight: 800; font-size: 0.75rem; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.8rem;">⚠️ {rep_watermark}</div>' if rep_watermark != "None" else ""

        render_html(f"""
            <div style="background: {preview_bg}; color: {preview_text}; border: 1px solid {preview_border}; border-radius: 12px; padding: 2rem; box-shadow: var(--shadow-lg);">
                {watermark_html}
                <!-- Cover Header -->
                <div style="border-bottom: 2px solid #6366F1; padding-bottom: 1.2rem; margin-bottom: 1.6rem;">
                    <div style="font-size: 1.6rem; font-weight: 800; margin-bottom: 0.3rem;">{rep_title}</div>
                    <div style="font-size: 0.88rem; color: var(--text-secondary);">{rep_company} — {rep_dept}</div>
                    <div style="display: flex; gap: 1.5rem; font-size: 0.75rem; color: var(--text-muted); margin-top: 0.8rem;">
                        <span>Dataset: <b>{file_name}</b></span>
                        <span>Author: <b>{rep_author}</b></span>
                        <span>Date: <b>{report_data.get('report_date', '')}</b></span>
                    </div>
                </div>
        """)

        # Render sections dynamically based on active_sections
        if "Executive Summary" in active_sections:
            render_html(f"""
                <div style="margin-bottom: 1.8rem;">
                    <h4 style="color: #6366F1; margin-top: 0; margin-bottom: 0.6rem; font-size: 1.05rem;">📝 Executive Summary</h4>
                    <div style="font-size: 0.88rem; line-height: 1.65; color: var(--text-secondary); background: rgba(99,102,241,0.03); padding: 1rem; border-left: 3px solid #6366F1; border-radius: 4px;">
                        {report_data.get('executive_summary_text', '')}
                    </div>
                </div>
            """)

        if "Dataset Overview" in active_sections:
            render_html(f"""
                <div style="margin-bottom: 1.8rem;">
                    <h4 style="color: #6366F1; margin-top: 0; margin-bottom: 0.6rem; font-size: 1.05rem;">📊 Dataset Overview & Health Metrics</h4>
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.6rem; text-align: center;">
                        <div style="background: rgba(255,255,255,0.03); border: 1px solid {preview_border}; padding: 0.75rem; border-radius: 8px;">
                            <div style="font-size: 1.2rem; font-weight: 800; color: #3B82F6;">{report_data.get('rows_curr', 0):,}</div>
                            <div style="font-size: 0.7rem; color: var(--text-muted);">Rows</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.03); border: 1px solid {preview_border}; padding: 0.75rem; border-radius: 8px;">
                            <div style="font-size: 1.2rem; font-weight: 800; color: #8B5CF6;">{report_data.get('cols_curr', 0)}</div>
                            <div style="font-size: 0.7rem; color: var(--text-muted);">Columns</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.03); border: 1px solid {preview_border}; padding: 0.75rem; border-radius: 8px;">
                            <div style="font-size: 1.2rem; font-weight: 800; color: #F59E0B;">{report_data.get('missing_curr', 0):,}</div>
                            <div style="font-size: 0.7rem; color: var(--text-muted);">Missing Cells</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.03); border: 1px solid {preview_border}; padding: 0.75rem; border-radius: 8px;">
                            <div style="font-size: 1.2rem; font-weight: 800; color: #10B981;">{report_data.get('quality_curr', 50)}%</div>
                            <div style="font-size: 0.7rem; color: var(--text-muted);">Quality Score</div>
                        </div>
                    </div>
                </div>
            """)

        if "Data Cleaning Report" in active_sections:
            clean_steps = report_data.get("cleaning_steps", [])
            steps_html = "".join([f'<li style="font-size:0.82rem; margin-bottom:0.3rem;"><b>{s.get("operation","Step")}</b>: {s.get("details","Applied cleaning")} ({s.get("timestamp","")})</li>' for s in clean_steps[:5]]) if clean_steps else '<div style="font-size:0.82rem; color:var(--text-muted);">No automated cleaning operations logged yet.</div>'
            render_html(f"""
                <div style="margin-bottom: 1.8rem;">
                    <h4 style="color: #6366F1; margin-top: 0; margin-bottom: 0.6rem; font-size: 1.05rem;">🧹 Data Cleaning Audit Log</h4>
                    <ul style="margin: 0; padding-left: 1.2rem; color: var(--text-secondary);">
                        {steps_html}
                    </ul>
                </div>
            """)

        if "Before vs After" in active_sections:
            render_html(f"""
                <div style="margin-bottom: 1.8rem;">
                    <h4 style="color: #6366F1; margin-top: 0; margin-bottom: 0.6rem; font-size: 1.05rem;">🔄 Before vs After Pipeline Impact</h4>
                    <table style="width: 100%; border-collapse: collapse; font-size: 0.8rem; text-align: left;">
                        <tr style="border-bottom: 1px solid {preview_border}; color: var(--text-muted);">
                            <th style="padding: 0.4rem;">Metric</th>
                            <th style="padding: 0.4rem;">Original Raw</th>
                            <th style="padding: 0.4rem;">Cleaned Pipeline</th>
                            <th style="padding: 0.4rem;">Impact / Net Delta</th>
                        </tr>
                        <tr style="border-bottom: 1px solid {preview_border};">
                            <td style="padding: 0.45rem;">Total Rows</td>
                            <td>{report_data.get('rows_orig', 0):,}</td>
                            <td>{report_data.get('rows_curr', 0):,}</td>
                            <td style="color: #10B981;">{report_data.get('rows_delta', 0):+} rows</td>
                        </tr>
                        <tr style="border-bottom: 1px solid {preview_border};">
                            <td style="padding: 0.45rem;">Missing Cells</td>
                            <td>{report_data.get('missing_orig', 0):,}</td>
                            <td>{report_data.get('missing_curr', 0):,}</td>
                            <td style="color: #10B981;">{report_data.get('missing_delta', 0):+} cells</td>
                        </tr>
                        <tr style="border-bottom: 1px solid {preview_border};">
                            <td style="padding: 0.45rem;">Duplicate Rows</td>
                            <td>{report_data.get('dups_orig', 0):,}</td>
                            <td>{report_data.get('dups_curr', 0):,}</td>
                            <td style="color: #10B981;">{report_data.get('dups_delta', 0):+} dups</td>
                        </tr>
                        <tr>
                            <td style="padding: 0.45rem;">Quality Score</td>
                            <td>{report_data.get('quality_orig', 50)}%</td>
                            <td>{report_data.get('quality_curr', 50)}%</td>
                            <td style="color: #10B981; font-weight: 700;">{report_data.get('quality_delta', 0):+}% gain</td>
                        </tr>
                    </table>
                </div>
            """)

        if "Business Insights" in active_sections:
            insights_html = "".join([f"""
                <div style="background: rgba(99,102,241,0.03); border-left: 3px solid #6366F1; padding: 0.65rem 0.9rem; border-radius: 4px; margin-bottom: 0.55rem;">
                    <div style="font-weight: 700; font-size: 0.85rem; color: var(--text-primary);">{ins.get('icon','💡')} {ins['title']}</div>
                    <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.15rem;">{ins['desc']}</div>
                </div>
            """ for ins in report_data.get("business_insights", [])[:8]])
            render_html(f"""
                <div style="margin-bottom: 1.8rem;">
                    <h4 style="color: #6366F1; margin-top: 0; margin-bottom: 0.6rem; font-size: 1.05rem;">💡 Key Business Intelligence Insights</h4>
                    {insights_html}
                </div>
            """)

        if "Recommendations" in active_sections:
            recs_html = "".join([f"""
                <div style="background: rgba(16,185,129,0.03); border-left: 3px solid #10B981; padding: 0.65rem 0.9rem; border-radius: 4px; margin-bottom: 0.55rem;">
                    <div style="font-weight: 700; font-size: 0.85rem; color: var(--text-primary);">✔ {rec['title']} <span style="font-size:0.65rem; background:rgba(16,185,129,0.15); color:#10B981; padding:0.1rem 0.35rem; border-radius:4px; margin-left:0.4rem;">{rec.get('type','General')}</span></div>
                    <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.15rem;">{rec['desc']}</div>
                </div>
            """ for rec in report_data.get("recommendations", [])])
            render_html(f"""
                <div style="margin-bottom: 1.8rem;">
                    <h4 style="color: #10B981; margin-top: 0; margin-bottom: 0.6rem; font-size: 1.05rem;">🎯 Actionable Recommendations</h4>
                    {recs_html}
                </div>
            """)

        # Risk Assessment section
        risks = report_data.get("risk_assessment", [])
        if risks:
            risks_html = "".join([f"""
                <div style="background: rgba(239,68,68,0.03); border-left: 3px solid #EF4444; padding: 0.65rem 0.9rem; border-radius: 4px; margin-bottom: 0.55rem;">
                    <div style="font-weight: 700; font-size: 0.85rem; color: var(--text-primary);">⚠️ {r['risk']} <span style="font-size:0.65rem; background:rgba(239,68,68,0.15); color:#EF4444; padding:0.1rem 0.35rem; border-radius:4px; margin-left:0.4rem;">Severity: {r.get('severity','Medium')}</span></div>
                    <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.15rem;"><b>Impact</b>: {r.get('impact','')}</div>
                    <div style="font-size: 0.78rem; color: #10B981; margin-top: 0.1rem;"><b>Mitigation</b>: {r.get('mitigation','')}</div>
                </div>
            """ for r in risks])
            render_html(f"""
                <div style="margin-bottom: 1.8rem;">
                    <h4 style="color: #EF4444; margin-top: 0; margin-bottom: 0.6rem; font-size: 1.05rem;">⚠️ Executive Risk Assessment</h4>
                    {risks_html}
                </div>
            """)

        # Opportunities section
        opps = report_data.get("opportunities", [])
        if opps:
            opps_html = "".join([f"""
                <div style="background: rgba(139,92,246,0.03); border-left: 3px solid #8B5CF6; padding: 0.65rem 0.9rem; border-radius: 4px; margin-bottom: 0.55rem;">
                    <div style="font-weight: 700; font-size: 0.85rem; color: var(--text-primary);">🚀 {o['opportunity']}</div>
                    <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.15rem;"><b>Projected Impact</b>: {o.get('impact','')}</div>
                    <div style="font-size: 0.78rem; color: #8B5CF6; margin-top: 0.1rem;"><b>Action</b>: {o.get('action','')}</div>
                </div>
            """ for o in opps])
            render_html(f"""
                <div style="margin-bottom: 1.8rem;">
                    <h4 style="color: #8B5CF6; margin-top: 0; margin-bottom: 0.6rem; font-size: 1.05rem;">🚀 Growth & Strategic Opportunities</h4>
                    {opps_html}
                </div>
            """)

        # Executive Conclusion
        if report_data.get("executive_conclusion"):
            render_html(f"""
                <div style="margin-bottom: 1.8rem;">
                    <h4 style="color: #6366F1; margin-top: 0; margin-bottom: 0.6rem; font-size: 1.05rem;">🏁 Executive Conclusion & Next Steps</h4>
                    <div style="font-size: 0.88rem; line-height: 1.65; color: var(--text-secondary); background: rgba(99,102,241,0.03); padding: 1rem; border-left: 3px solid #6366F1; border-radius: 4px;">
                        {report_data.get('executive_conclusion')}
                    </div>
                </div>
            """)

        render_html(f"""
                <div style="text-align: center; font-size: 0.72rem; color: var(--text-muted); border-top: 1px solid var(--border-color); padding-top: 1rem; margin-top: 2rem;">
                    {ai_badge_text} • End of Executive Report Preview • Generated by Data Pilot System
                </div>
            </div>
        """)

    # =============================================================================
    # DOWNLOAD CENTER
    # =============================================================================
    st.markdown("<br><hr style='border: 0.5px solid var(--border-color);'><br>", unsafe_allow_html=True)
    st.markdown("### 📥 Executive Download Center")
    st.caption("Export your configured report into high-resolution documents, spreadsheets, presentations, and code formats.")

    dl_cols = st.columns(4)

    # 1. PDF Report
    with dl_cols[0]:
        st.markdown("""
            <div class="content-card" style="text-align:center;">
                <div style="font-size:2rem; margin-bottom:0.3rem;">📄</div>
                <div style="font-weight:700; font-size:0.9rem;">PDF Report</div>
                <div style="font-size:0.72rem; color:var(--text-muted); margin-bottom:0.8rem;">Executive Printable Document</div>
            </div>
        """, unsafe_allow_html=True)
        pdf_bytes = export_pdf_report(report_data, config)
        st.download_button(
            label="📥 Download PDF",
            data=pdf_bytes,
            file_name=f"{project_name.lower().replace(' ','_')}_report_v{next_ver}.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary"
        )

    # 2. HTML Report
    with dl_cols[1]:
        st.markdown("""
            <div class="content-card" style="text-align:center;">
                <div style="font-size:2rem; margin-bottom:0.3rem;">🌐</div>
                <div style="font-weight:700; font-size:0.9rem;">Interactive HTML</div>
                <div style="font-size:0.72rem; color:var(--text-muted); margin-bottom:0.8rem;">Standalone Browser Web Document</div>
            </div>
        """, unsafe_allow_html=True)
        html_str = export_html_report(report_data, config)
        st.download_button(
            label="📥 Download HTML",
            data=html_str,
            file_name=f"{project_name.lower().replace(' ','_')}_report_v{next_ver}.html",
            mime="text/html",
            use_container_width=True
        )

    # 3. Excel Multi-sheet
    with dl_cols[2]:
        st.markdown("""
            <div class="content-card" style="text-align:center;">
                <div style="font-size:2rem; margin-bottom:0.3rem;">📊</div>
                <div style="font-weight:700; font-size:0.9rem;">Excel Workbook</div>
                <div style="font-size:0.72rem; color:var(--text-muted); margin-bottom:0.8rem;">Multi-sheet Workbook & Data</div>
            </div>
        """, unsafe_allow_html=True)
        excel_bytes = export_excel_summary(report_data, config)
        st.download_button(
            label="📥 Download Excel",
            data=excel_bytes,
            file_name=f"{project_name.lower().replace(' ','_')}_summary_v{next_ver}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    # 4. Word DOCX
    with dl_cols[3]:
        st.markdown("""
            <div class="content-card" style="text-align:center;">
                <div style="font-size:2rem; margin-bottom:0.3rem;">📝</div>
                <div style="font-weight:700; font-size:0.9rem;">Word Document</div>
                <div style="font-size:0.72rem; color:var(--text-muted); margin-bottom:0.8rem;">Editable DOCX Document</div>
            </div>
        """, unsafe_allow_html=True)
        docx_bytes = export_docx_report(report_data, config)
        st.download_button(
            label="📥 Download DOCX",
            data=docx_bytes,
            file_name=f"{project_name.lower().replace(' ','_')}_report_v{next_ver}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )

    st.markdown("<br>", unsafe_allow_html=True)
    dl_cols2 = st.columns(4)

    # 5. PowerPoint Deck
    with dl_cols2[0]:
        st.markdown("""
            <div class="content-card" style="text-align:center;">
                <div style="font-size:2rem; margin-bottom:0.3rem;">📽️</div>
                <div style="font-weight:700; font-size:0.9rem;">PowerPoint Deck</div>
                <div style="font-size:0.72rem; color:var(--text-muted); margin-bottom:0.8rem;">Executive PPTX Presentation</div>
            </div>
        """, unsafe_allow_html=True)
        pptx_bytes = export_pptx_report(report_data, config)
        st.download_button(
            label="📥 Download PPTX",
            data=pptx_bytes,
            file_name=f"{project_name.lower().replace(' ','_')}_deck_v{next_ver}.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            use_container_width=True
        )

    # 6. Markdown Report
    with dl_cols2[1]:
        st.markdown("""
            <div class="content-card" style="text-align:center;">
                <div style="font-size:2rem; margin-bottom:0.3rem;">📋</div>
                <div style="font-weight:700; font-size:0.9rem;">Markdown Text</div>
                <div style="font-size:0.72rem; color:var(--text-muted); margin-bottom:0.8rem;">GitHub Markdown Format</div>
            </div>
        """, unsafe_allow_html=True)
        md_str = export_markdown_report(report_data, config)
        st.download_button(
            label="📥 Download Markdown",
            data=md_str,
            file_name=f"{project_name.lower().replace(' ','_')}_report_v{next_ver}.md",
            mime="text/markdown",
            use_container_width=True
        )

    # 7. CSV Metrics
    with dl_cols2[2]:
        st.markdown("""
            <div class="content-card" style="text-align:center;">
                <div style="font-size:2rem; margin-bottom:0.3rem;">💾</div>
                <div style="font-weight:700; font-size:0.9rem;">CSV Summary</div>
                <div style="font-size:0.72rem; color:var(--text-muted); margin-bottom:0.8rem;">Raw Metrics Data Table</div>
            </div>
        """, unsafe_allow_html=True)
        csv_str = export_csv_summary(report_data)
        st.download_button(
            label="📥 Download CSV",
            data=csv_str,
            file_name=f"{project_name.lower().replace(' ','_')}_summary_v{next_ver}.csv",
            mime="text/csv",
            use_container_width=True
        )

    # 8. JSON Dump
    with dl_cols2[3]:
        st.markdown("""
            <div class="content-card" style="text-align:center;">
                <div style="font-size:2rem; margin-bottom:0.3rem;">⚙️</div>
                <div style="font-weight:700; font-size:0.9rem;">JSON Report Spec</div>
                <div style="font-size:0.72rem; color:var(--text-muted); margin-bottom:0.8rem;">Structured Data Payload</div>
            </div>
        """, unsafe_allow_html=True)
        json_str = export_json_report(report_data, config)
        st.download_button(
            label="📥 Download JSON",
            data=json_str,
            file_name=f"{project_name.lower().replace(' ','_')}_report_v{next_ver}.json",
            mime="application/json",
            use_container_width=True
        )

    # =============================================================================
    # REPORT HISTORY & VERSION CONTROL
    # =============================================================================
    st.markdown("<br><hr style='border: 0.5px solid var(--border-color);'><br>", unsafe_allow_html=True)
    h_c1, h_c2 = st.columns([3, 1])
    with h_c1:
        st.markdown("### 📜 Saved Report Versions & History")
        st.caption("All generated reports are snapshot-versioned in SQLite storage.")
    with h_c2:
        if st.button("💾 Save Current Version to Database", type="primary", use_container_width=True):
            meta_save = {
                "project_id": project_id,
                "version": next_ver,
                "title": rep_title,
                "author": rep_author,
                "company": rep_company,
                "department": rep_dept,
                "theme": theme_choice,
                "sections": active_sections,
                "dataset_name": file_name,
                "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            if save_report_meta(meta_save):
                _alert(f"Saved Report Version v{next_ver}.0 to SQLite database!", "success")
                st.rerun()

    history_list = list_reports(project_id)
    if history_list:
        h_data = []
        for h in history_list:
            h_data.append({
                "Version": f"v{h.get('version', 1)}.0",
                "Title": h.get("title", "Report"),
                "Created Date": h.get("created_at", ""),
                "Author": h.get("author", ""),
                "Theme": h.get("theme", "Corporate"),
                "Sections": len(h.get("sections", [])),
                "Action": h.get("id")
            })

        for row in h_data:
            r_col1, r_col2, r_col3, r_col4 = st.columns([1, 3, 2, 1])
            with r_col1:
                st.markdown(f"**{row['Version']}**")
            with r_col2:
                st.markdown(f"**{row['Title']}**  \n<span style='font-size:0.72rem; color:var(--text-muted);'>{row['Author']} • {row['Theme']} • {row['Sections']} sections</span>", unsafe_allow_html=True)
            with r_col3:
                st.markdown(f"<span style='font-size:0.8rem; color:var(--text-secondary);'>{row['Created Date']}</span>", unsafe_allow_html=True)
            with r_col4:
                if st.button("🗑️ Delete", key=f"del_rep_{row['Action']}", type="secondary"):
                    delete_report(row['Action'])
                    st.rerun()
    else:
        render_html("""
            <div style="padding: 1.5rem; background: rgba(255, 255, 255, 0.02); border: 1px dashed var(--card-border); border-radius: 8px; text-align: center; color: var(--text-secondary); font-size: 0.85rem; margin-top: 1rem;">
                No saved report versions found in project database. Click 'Save Current Version' above to store your version history.
            </div>
        """)
