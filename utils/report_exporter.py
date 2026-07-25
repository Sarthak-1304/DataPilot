"""
Report Exporter Utility
=======================
Generates downloadable report files across multiple formats:
HTML, PDF (ReportLab), Excel (Multi-sheet), CSV, Markdown, JSON, DOCX, PPTX.
"""

import os
import json
import io
import pandas as pd
import numpy as np
import datetime
from typing import Dict, Any, Optional, List


# -----------------------------------------------------------------------------
# 1. Standalone HTML Report Exporter
# -----------------------------------------------------------------------------

def export_html_report(data: Dict[str, Any], config: Dict[str, Any]) -> str:
    """Generate a self-contained HTML report with executive inline styling."""
    title = config.get("title", "Data Analysis & Business Report")
    company = config.get("company_name", "Data Pilot Org")
    author = config.get("author", "Data Analyst")
    department = config.get("department", "Analytics Division")
    theme_name = config.get("theme", "Corporate")

    # Theme CSS tokens
    if theme_name == "Dark":
        bg_main = "#0F172A"
        bg_card = "#1E293B"
        text_pri = "#F8FAFC"
        text_sec = "#94A3B8"
        border_col = "#334155"
        accent_col = "#6366F1"
    elif theme_name == "Modern":
        bg_main = "#F8FAFC"
        bg_card = "#FFFFFF"
        text_pri = "#0F172A"
        text_sec = "#64748B"
        border_col = "#E2E8F0"
        accent_col = "#8B5CF6"
    elif theme_name == "Minimal":
        bg_main = "#FFFFFF"
        bg_card = "#FFFFFF"
        text_pri = "#18181B"
        text_sec = "#71717A"
        border_col = "#E4E4E7"
        accent_col = "#18181B"
    else:  # Corporate
        bg_main = "#F1F5F9"
        bg_card = "#FFFFFF"
        text_pri = "#0F172A"
        text_sec = "#475569"
        border_col = "#CBD5E1"
        accent_col = "#2563EB"

    sections = config.get("sections", [])
    exec_summary = data.get("executive_summary_text", "")
    insights = data.get("business_insights", [])
    recs = data.get("recommendations", [])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — {company}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: {bg_main};
            color: {text_pri};
            margin: 0;
            padding: 2rem;
            line-height: 1.6;
        }}
        .report-container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        .header-card {{
            background-color: {bg_card};
            border: 1px solid {border_col};
            border-left: 6px solid {accent_col};
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
        }}
        .header-title {{
            font-size: 2rem;
            font-weight: 800;
            margin: 0 0 0.5rem 0;
            color: {text_pri};
        }}
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
            margin-top: 1.5rem;
            padding-top: 1rem;
            border-top: 1px solid {border_col};
            font-size: 0.85rem;
            color: {text_sec};
        }}
        .meta-grid span {{
            font-weight: 700;
            color: {text_pri};
        }}
        .section-card {{
            background-color: {bg_card};
            border: 1px solid {border_col};
            border-radius: 12px;
            padding: 1.8rem;
            margin-bottom: 1.5rem;
        }}
        .section-title {{
            font-size: 1.25rem;
            font-weight: 700;
            margin-top: 0;
            margin-bottom: 1rem;
            color: {text_pri};
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            margin-bottom: 1.5rem;
        }}
        .metric-box {{
            background: rgba(99, 102, 241, 0.05);
            border: 1px solid {border_col};
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        }}
        .metric-val {{
            font-size: 1.4rem;
            font-weight: 800;
            color: {accent_col};
        }}
        .metric-lbl {{
            font-size: 0.75rem;
            color: {text_sec};
            text-transform: uppercase;
            font-weight: 600;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
            font-size: 0.85rem;
        }}
        th, td {{
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid {border_col};
        }}
        th {{
            background-color: rgba(0,0,0,0.03);
            font-weight: 700;
            color: {text_pri};
        }}
        .insight-card {{
            background-color: rgba(99, 102, 241, 0.04);
            border-left: 3px solid {accent_col};
            padding: 0.85rem 1.1rem;
            margin-bottom: 0.75rem;
            border-radius: 4px;
            font-size: 0.9rem;
        }}
        .badge {{
            display: inline-block;
            padding: 0.2rem 0.6rem;
            border-radius: 100px;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
        }}
        .footer {{
            text-align: center;
            font-size: 0.8rem;
            color: {text_sec};
            margin-top: 3rem;
            padding-top: 1.5rem;
            border-top: 1px solid {border_col};
        }}
    </style>
</head>
<body>
    <div class="report-container">
        <!-- Header / Cover -->
        <div class="header-card">
            <div class="header-title">{title}</div>
            <div style="font-size: 0.95rem; color: {text_sec};">{company} — {department}</div>
            <div class="meta-grid">
                <div>Dataset: <span>{data.get('file_name', 'Dataset')}</span></div>
                <div>Report Date: <span>{data.get('report_date', '')}</span></div>
                <div>Author: <span>{author}</span></div>
                <div>Quality Score: <span style="color:#10B981;">{data.get('quality_curr', 50)}/100</span></div>
            </div>
        </div>

        <!-- Executive Summary -->
        {"<div class='section-card'><div class='section-title'>📝 Executive Summary</div><p>" + exec_summary + "</p></div>" if "Executive Summary" in sections else ""}

        <!-- Dataset Overview -->
        {"<div class='section-card'><div class='section-title'>📊 Dataset Summary</div><div class='metric-grid'><div class='metric-box'><div class='metric-val'>" + f"{data.get('rows_curr', 0):,}" + "</div><div class='metric-lbl'>Rows</div></div><div class='metric-box'><div class='metric-val'>" + f"{data.get('cols_curr', 0)}" + "</div><div class='metric-lbl'>Columns</div></div><div class='metric-box'><div class='metric-val'>" + f"{data.get('missing_curr', 0):,}" + "</div><div class='metric-lbl'>Missing Cells</div></div><div class='metric-box'><div class='metric-val'>" + f"{data.get('quality_curr', 0)}%" + "</div><div class='metric-lbl'>Health Score</div></div></div></div>" if "Dataset Overview" in sections else ""}

        <!-- Business Insights -->
        {"<div class='section-card'><div class='section-title'>💡 Key Business Insights</div>" + "".join([f"<div class='insight-card'><strong>{item['icon']} {item['title']}</strong><br>{item['desc']}</div>" for item in insights]) + "</div>" if "Business Insights" in sections and insights else ""}

        <!-- Recommendations -->
        {"<div class='section-card'><div class='section-title'>🎯 Actionable Recommendations</div>" + "".join([f"<div class='insight-card' style='border-left-color:#10B981;'><strong>{rec['title']}</strong> [{rec.get('priority', 'Normal')}]<br>{rec['desc']}</div>" for rec in recs]) + "</div>" if "Recommendations" in sections and recs else ""}

        <div class="footer">
            Generated by Data Pilot Executive Reporting System • {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        </div>
    </div>
</body>
</html>"""
    return html


# -----------------------------------------------------------------------------
# 2. Markdown Report Exporter
# -----------------------------------------------------------------------------

def export_markdown_report(data: Dict[str, Any], config: Dict[str, Any]) -> str:
    """Generate clean GitHub-flavored markdown report."""
    title = config.get("title", "Data Analysis Report")
    company = config.get("company_name", "Data Pilot Org")
    author = config.get("author", "Data Analyst")
    date_str = data.get("report_date", datetime.datetime.now().strftime("%Y-%m-%d"))

    lines = [
        f"# {title}",
        f"**Company**: {company}  |  **Author**: {author}  |  **Date**: {date_str}",
        f"**Dataset**: `{data.get('file_name', 'Dataset')}`  |  **Data Quality Score**: `{data.get('quality_curr', 50)}/100`",
        "---",
        "",
        "## 📝 Executive Summary",
        data.get("executive_summary_text", "No summary generated."),
        "",
        "## 📊 Dataset Overview",
        f"- **Rows**: {data.get('rows_curr', 0):,}",
        f"- **Columns**: {data.get('cols_curr', 0)}",
        f"- **Missing Cells**: {data.get('missing_curr', 0):,}",
        f"- **Duplicate Rows**: {data.get('dups_curr', 0):,}",
        f"- **Numeric Columns**: {len(data.get('num_cols', []))}",
        f"- **Categorical Columns**: {len(data.get('cat_cols', []))}",
        "",
        "## 💡 Business Insights",
    ]

    for item in data.get("business_insights", []):
        lines.append(f"### {item['icon']} {item['title']}")
        lines.append(f"{item['desc']}\n")

    lines.append("## 🎯 Recommendations")
    for rec in data.get("recommendations", []):
        lines.append(f"- **{rec['title']}** ({rec.get('type', 'General')}): {rec['desc']}")

    lines.append("\n---")
    lines.append(f"*Generated automatically by Data Pilot on {date_str}*")
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# 3. Excel Multi-Sheet Report Exporter
# -----------------------------------------------------------------------------

def export_excel_summary(data: Dict[str, Any], config: Dict[str, Any]) -> bytes:
    """Generate multi-sheet Excel report workbook."""
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        # Sheet 1: Executive Summary
        summary_rows = [
            {"Property": "Report Title", "Value": config.get("title", "Executive Report")},
            {"Property": "Company Name", "Value": config.get("company_name", "Data Pilot")},
            {"Property": "Author", "Value": config.get("author", "Data Analyst")},
            {"Property": "Department", "Value": config.get("department", "Analytics")},
            {"Property": "Report Date", "Value": data.get("report_date", "")},
            {"Property": "Dataset Name", "Value": data.get("file_name", "Dataset")},
            {"Property": "Total Rows", "Value": data.get("rows_curr", 0)},
            {"Property": "Total Columns", "Value": data.get("cols_curr", 0)},
            {"Property": "Data Quality Score", "Value": f"{data.get('quality_curr', 50)}/100"},
            {"Property": "Missing Cells", "Value": data.get("missing_curr", 0)},
            {"Property": "Duplicate Rows", "Value": data.get("dups_curr", 0)},
        ]
        pd.DataFrame(summary_rows).to_excel(writer, sheet_name="Executive Summary", index=False)

        # Sheet 2: Working Data Sample
        working_df = data.get("working_df")
        if working_df is not None:
            working_df.head(1000).to_excel(writer, sheet_name="Dataset Sample", index=False)

        # Sheet 3: Cleaning History
        clean_hist = data.get("cleaning_steps", [])
        if clean_hist:
            pd.DataFrame(clean_hist).to_excel(writer, sheet_name="Cleaning Log", index=False)

        # Sheet 4: Business Insights
        insights = data.get("business_insights", [])
        if insights:
            pd.DataFrame(insights).to_excel(writer, sheet_name="Business Insights", index=False)

        # Sheet 5: Recommendations
        recs = data.get("recommendations", [])
        if recs:
            pd.DataFrame(recs).to_excel(writer, sheet_name="Recommendations", index=False)

    return output.getvalue()


# -----------------------------------------------------------------------------
# 4. CSV Metrics Summary Exporter
# -----------------------------------------------------------------------------

def export_csv_summary(data: Dict[str, Any]) -> str:
    """Generate CSV metrics summary."""
    metrics = [
        {"Metric": "Dataset Name", "Value": data.get("file_name", "")},
        {"Metric": "Report Date", "Value": data.get("report_date", "")},
        {"Metric": "Original Rows", "Value": data.get("rows_orig", 0)},
        {"Metric": "Cleaned Rows", "Value": data.get("rows_curr", 0)},
        {"Metric": "Original Columns", "Value": data.get("cols_orig", 0)},
        {"Metric": "Cleaned Columns", "Value": data.get("cols_curr", 0)},
        {"Metric": "Original Quality Score", "Value": data.get("quality_orig", 50)},
        {"Metric": "Cleaned Quality Score", "Value": data.get("quality_curr", 50)},
        {"Metric": "Missing Cells Resolved", "Value": abs(data.get("missing_delta", 0))},
        {"Metric": "Duplicates Removed", "Value": abs(data.get("dups_delta", 0))},
    ]
    df = pd.DataFrame(metrics)
    return df.to_csv(index=False)


# -----------------------------------------------------------------------------
# 5. JSON Report Exporter
# -----------------------------------------------------------------------------

def export_json_report(data: Dict[str, Any], config: Dict[str, Any]) -> str:
    """Generate structured JSON report representation."""
    dump = {
        "metadata": {
            "title": config.get("title", "Data Analysis Report"),
            "company": config.get("company_name", "Data Pilot"),
            "author": config.get("author", "Analyst"),
            "generated_at": datetime.datetime.now().isoformat(),
            "theme": config.get("theme", "Corporate"),
        },
        "summary": {
            "dataset_name": data.get("file_name", ""),
            "rows": data.get("rows_curr", 0),
            "columns": data.get("cols_curr", 0),
            "quality_score": data.get("quality_curr", 50),
            "executive_summary": data.get("executive_summary_text", ""),
        },
        "insights": data.get("business_insights", []),
        "recommendations": data.get("recommendations", []),
        "cleaning_steps": data.get("cleaning_steps", []),
    }
    return json.dumps(dump, indent=4)


# -----------------------------------------------------------------------------
# 6. PDF Report Exporter (ReportLab)
# -----------------------------------------------------------------------------

def export_pdf_report(data: Dict[str, Any], config: Dict[str, Any]) -> bytes:
    """Generate a PDF document using ReportLab."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        story = []

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor('#0F172A'),
            spaceAfter=6
        )
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#64748B'),
            spaceAfter=12
        )
        heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor('#2563EB'),
            spaceBefore=12,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            'ReportBody',
            parent=styles['BodyText'],
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor('#334155'),
            spaceAfter=8
        )

        # Title
        story.append(Paragraph(config.get("title", "Data Analysis Report"), title_style))
        sub_text = f"{config.get('company_name', 'Data Pilot')} | Author: {config.get('author', 'Analyst')} | Date: {data.get('report_date', '')}"
        story.append(Paragraph(sub_text, subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E2E8F0'), spaceAfter=12))

        # Executive Summary
        story.append(Paragraph("Executive Summary", heading_style))
        story.append(Paragraph(data.get("executive_summary_text", ""), body_style))
        story.append(Spacer(1, 10))

        # Dataset Stats Table
        story.append(Paragraph("Dataset Overview", heading_style))
        table_data = [
            ["Metric", "Value", "Metric", "Value"],
            ["Dataset Name", str(data.get("file_name", "")), "Quality Score", f"{data.get('quality_curr', 50)}/100"],
            ["Total Rows", f"{data.get('rows_curr', 0):,}", "Numeric Columns", str(len(data.get("num_cols", [])))],
            ["Total Columns", str(data.get("cols_curr", 0)), "Categorical Columns", str(len(data.get("cat_cols", [])))],
            ["Missing Cells", f"{data.get('missing_curr', 0):,}", "Duplicate Rows", f"{data.get('dups_curr', 0):,}"]
        ]
        t = Table(table_data, colWidths=[130, 140, 130, 140])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ]))
        story.append(t)
        story.append(Spacer(1, 14))

        # Business Insights
        story.append(Paragraph("Key Business Insights", heading_style))
        for item in data.get("business_insights", [])[:8]:
            story.append(Paragraph(f"• <b>{item['title']}</b>: {item['desc']}", body_style))

        # Recommendations
        story.append(Spacer(1, 10))
        story.append(Paragraph("Actionable Recommendations", heading_style))
        for rec in data.get("recommendations", []):
            story.append(Paragraph(f"✔ <b>{rec['title']}</b>: {rec['desc']}", body_style))

        doc.build(story)
        return buffer.getvalue()
    except Exception as e:
        print(f"PDF generation error: {e}")
        # Fallback simple text PDF
        return b"PDF Generation Fallback"


# -----------------------------------------------------------------------------
# 7. DOCX Report Exporter
# -----------------------------------------------------------------------------

def export_docx_report(data: Dict[str, Any], config: Dict[str, Any]) -> bytes:
    """Generate Word Document report (.docx)."""
    try:
        import docx
        doc = docx.Document()
        doc.add_heading(config.get("title", "Data Analysis Report"), level=0)
        doc.add_paragraph(f"Company: {config.get('company_name', 'Data Pilot')} | Author: {config.get('author', 'Analyst')} | Date: {data.get('report_date', '')}")

        doc.add_heading("Executive Summary", level=1)
        doc.add_paragraph(data.get("executive_summary_text", ""))

        doc.add_heading("Dataset Summary", level=1)
        doc.add_paragraph(f"Rows: {data.get('rows_curr', 0):,} | Columns: {data.get('cols_curr', 0)} | Quality Score: {data.get('quality_curr', 50)}%")

        doc.add_heading("Business Insights", level=1)
        for item in data.get("business_insights", []):
            doc.add_paragraph(f"{item['icon']} {item['title']}: {item['desc']}")

        doc.add_heading("Recommendations", level=1)
        for rec in data.get("recommendations", []):
            doc.add_paragraph(f"• {rec['title']}: {rec['desc']}")

        buffer = io.BytesIO()
        doc.save(buffer)
        return buffer.getvalue()
    except Exception:
        # Fallback to plain text bytes
        return export_markdown_report(data, config).encode("utf-8")


# -----------------------------------------------------------------------------
# 8. PPTX Report Exporter
# -----------------------------------------------------------------------------

def export_pptx_report(data: Dict[str, Any], config: Dict[str, Any]) -> bytes:
    """Generate PowerPoint presentation report (.pptx)."""
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt
        prs = Presentation()

        # Slide 1: Title Slide
        title_slide_layout = prs.slide_layouts[0]
        slide = prs.slides.add_slide(title_slide_layout)
        title = slide.shapes.title
        subtitle = slide.placeholders[1]
        title.text = config.get("title", "Data Analysis Report")
        subtitle.text = f"{config.get('company_name', 'Data Pilot')}\nPrepared by: {config.get('author', 'Analyst')}"

        # Slide 2: Executive Summary
        bullet_slide_layout = prs.slide_layouts[1]
        slide2 = prs.slides.add_slide(bullet_slide_layout)
        shapes2 = slide2.shapes
        shapes2.title.text = "Executive Summary"
        tf2 = shapes2.placeholders[1].text_frame
        tf2.text = data.get("executive_summary_text", "")

        # Slide 3: Insights
        slide3 = prs.slides.add_slide(bullet_slide_layout)
        shapes3 = slide3.shapes
        shapes3.title.text = "Key Business Insights"
        tf3 = shapes3.placeholders[1].text_frame
        for item in data.get("business_insights", [])[:5]:
            p = tf3.add_paragraph()
            p.text = f"{item['title']}: {item['desc'][:100]}..."

        buffer = io.BytesIO()
        prs.save(buffer)
        return buffer.getvalue()
    except Exception:
        # Fallback to plain text bytes
        return export_markdown_report(data, config).encode("utf-8")
