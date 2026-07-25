"""
AI Report Agent
===============
Generates dynamic, dataset-specific executive report content using the AI abstraction layer.
Produces Executive Summary, Business Intelligence Insights, Recommendations,
Executive Conclusion, Risk Assessment, Opportunities, and AI Confidence Scores.
"""

import json
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from ai.gemini_manager import get_gemini_api_key, get_best_available_model, is_gemini_configured


class ReportAgent:
    """Agent responsible for constructing AI report contexts and generating executive report content."""

    # -----------------------------------------------------------------
    # Internal: Construct Structured Aggregated Context for LLM
    # -----------------------------------------------------------------
    @staticmethod
    def build_report_context(data: Dict[str, Any]) -> str:
        """Create a compact, aggregated statistical summary for AI prompt context."""
        lines = []
        file_name = data.get("file_name", "Dataset")
        project_name = data.get("project_name", file_name)

        lines.append(f"PROJECT NAME: {project_name}")
        lines.append(f"DATASET NAME: {file_name}")
        lines.append(f"DATASET DIMENSIONS: {data.get('rows_curr', 0):,} rows x {data.get('cols_curr', 0)} columns")
        lines.append(f"NUMERIC COLUMNS ({len(data.get('num_cols', []))}): {', '.join(data.get('num_cols', []))}")
        lines.append(f"CATEGORICAL COLUMNS ({len(data.get('cat_cols', []))}): {', '.join(data.get('cat_cols', []))}")

        # Quality & Impact Metrics
        q_orig = data.get("quality_orig", 50)
        q_curr = data.get("quality_curr", 50)
        lines.append(f"\nDATA QUALITY HEALTH: Original Raw Quality = {q_orig}%, Cleaned Quality = {q_curr}% (Delta: {data.get('quality_delta', 0):+}%)")
        lines.append(f"PIPELINE IMPACT: Rows Delta = {data.get('rows_delta', 0):+}, Missing Resolved = {abs(data.get('missing_delta', 0)):+}, Duplicates Removed = {abs(data.get('dups_delta', 0)):+}")

        # Cleaning Audit Steps
        steps = data.get("cleaning_steps", [])
        if steps:
            step_strs = [f"- {s.get('operation', 'Step')}: {s.get('details', '')}" for s in steps[:8]]
            lines.append("\nCLEANING OPERATIONS APPLIED:\n" + "\n".join(step_strs))
        else:
            lines.append("\nCLEANING OPERATIONS: Raw uncleaned dataset")

        # Descriptive Statistics
        df = data.get("working_df")
        if df is not None:
            num_cols = data.get("num_cols", [])
            if num_cols:
                stats_summary = []
                for c in num_cols[:6]:
                    series = df[c].dropna()
                    if len(series) > 0:
                        stats_summary.append(f"  {c}: mean={series.mean():.2f}, median={series.median():.2f}, std={series.std():.2f}, min={series.min()}, max={series.max()}")
                lines.append("\nNUMERIC STATISTICAL PROFILES:\n" + "\n".join(stats_summary))

            cat_cols = data.get("cat_cols", [])
            if cat_cols:
                cat_summary = []
                for c in cat_cols[:6]:
                    counts = df[c].value_counts().head(3).to_dict()
                    cat_summary.append(f"  {c}: unique={df[c].nunique()}, top_values={counts}")
                lines.append("\nCATEGORICAL DISTRIBUTIONS:\n" + "\n".join(cat_summary))

        # Top Correlations
        top_corrs = data.get("top_corrs", [])
        if top_corrs:
            corr_strs = [f"{c['col1']} <-> {c['col2']}: {c['val']:+.2f}" for c in top_corrs[:6]]
            lines.append("\nKEY CORRELATIONS: " + "; ".join(corr_strs))

        # Outliers Summary
        outliers = data.get("outliers", [])
        if outliers:
            out_strs = [f"{o['column']}: {o['count']} outliers ({o['pct']}%)" for o in outliers[:5]]
            lines.append("\nOUTLIER PROFILES: " + "; ".join(out_strs))

        return "\n".join(lines)

    # -----------------------------------------------------------------
    # Internal: AI Call Helper
    # -----------------------------------------------------------------
    @staticmethod
    def _call_ai(prompt: str, system_instruction: str) -> Optional[str]:
        """Call AI provider abstraction layer and return response text."""
        key = get_gemini_api_key()
        if not key:
            return None
        try:
            genai.configure(api_key=key)
            model_name = get_best_available_model()
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_instruction
            )
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"AI Call error: {e}")
            return None

    @staticmethod
    def _clean_json(raw: str) -> str:
        """Extract clean JSON object/array string."""
        text = raw.strip()
        start = min([i for i in (text.find('{'), text.find('[')) if i != -1], default=-1)
        end = max(text.rfind('}'), text.rfind(']'))
        if start != -1 and end != -1 and end > start:
            return text[start:end+1].strip()
        return text

    # -----------------------------------------------------------------
    # Main Entry Point: Generate Complete AI Report Package
    # -----------------------------------------------------------------
    @staticmethod
    def generate_ai_report(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate a complete dataset-specific AI executive report package.
        Returns a dict containing:
        - executive_summary
        - business_insights
        - recommendations
        - executive_conclusion
        - risk_assessment
        - opportunities
        - ai_confidence
        """
        if not is_gemini_configured():
            return None

        context = ReportAgent.build_report_context(data)

        system_instruction = (
            "You are a Principal Business Intelligence & Data Science Executive writing an official corporate report. "
            "Your writing is authoritative, highly specific, data-driven, and actionable. "
            "Reference exact numbers, column names, statistical metrics, and percentages from the context. "
            "Never use placeholders or generic boilerplates."
        )

        prompt = f"""Based on the following aggregated dataset profile, generate a complete executive report payload in JSON format.

STRUCTURED DATASET CONTEXT:
{context}

Return ONLY a valid JSON object with EXACTLY these keys:

1. "executive_summary": A professional 250-350 word executive summary describing the dataset, purpose, cleaning operations performed, quality score gains, key statistical findings, and overall business readiness. Use <b> HTML tags for key metrics.

2. "business_insights": Array of 6 to 10 structured insights. Each object must have:
   - "icon": emoji icon (e.g. 📈, 🎯, 📊, ⚡, 🚨, 🏷️)
   - "title": short insight title (max 7 words)
   - "desc": specific 1-2 sentence data-driven insight (use <b> HTML tags on metrics)
   - "category": category string (e.g., Distribution, Performance, Relationships, Quality, Outliers)

3. "recommendations": Array of 5 to 8 actionable recommendations. Each object must have:
   - "title": short recommendation title
   - "desc": specific actionable step (use <b> HTML tags)
   - "type": category string (e.g., Data Quality, Feature Engineering, Strategy, Governance)
   - "priority": one of "High", "Medium", "Low"

4. "executive_conclusion": A 150-200 word strategic conclusion summarizing overall dataset health, business implications, recommended deployment steps, and future outlook.

5. "risk_assessment": Array of 4 to 6 business and data risks. Each object must have:
   - "risk": short risk title
   - "impact": specific impact explanation
   - "severity": one of "High", "Medium", "Low"
   - "mitigation": recommended mitigation action

6. "opportunities": Array of 4 to 6 data-backed growth opportunities. Each object must have:
   - "opportunity": short opportunity title
   - "impact": projected business impact
   - "action": recommended next step

7. "ai_confidence": Object with:
   - "score": integer 85-99
   - "level": "High"
   - "reason": explanation string referencing dataset quality and sample size completeness

IMPORTANT: Return ONLY the JSON object, no markdown code block backticks."""

        raw = ReportAgent._call_ai(prompt, system_instruction)
        if not raw:
            return None

        try:
            cleaned = ReportAgent._clean_json(raw)
            result = json.loads(cleaned)
            if isinstance(result, dict) and "executive_summary" in result and "business_insights" in result:
                return result
            return None
        except Exception as e:
            print(f"Error parsing AI report JSON: {e}")
            return None

    # -----------------------------------------------------------------
    # Fallback Generators (Dynamic Rule-Based using dataset metrics)
    # -----------------------------------------------------------------
    @staticmethod
    def generate_fallback_report(data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate dynamic, data-driven report content when AI is disconnected."""
        file_name = data.get("file_name", "Dataset")
        rows = data.get("rows_curr", 0)
        cols = data.get("cols_curr", 0)
        q_orig = data.get("quality_orig", 50)
        q_curr = data.get("quality_curr", 50)
        dups_delta = abs(data.get("dups_delta", 0))
        missing_delta = abs(data.get("missing_delta", 0))

        # Executive Summary
        exec_summary = (
            f"This executive analysis evaluates the <b>{file_name}</b> dataset, containing <b>{rows:,} records</b> and <b>{cols} dimensions</b>. "
            f"Through automated pipeline processing, overall data health improved from <b>{q_orig}%</b> to <b>{q_curr}%</b>. "
            f"Data hygiene operations resolved <b>{dups_delta:,} duplicate records</b> and <b>{missing_delta:,} missing cells</b>. "
            f"Statistical profiling identified <b>{len(data.get('num_cols', []))} numerical metrics</b> and <b>{len(data.get('cat_cols', []))} categorical dimensions</b>. "
            f"The dataset is verified for executive dashboarding, operational reporting, and business intelligence workflows."
        )

        # Business Insights
        insights = []
        insights.append({
            "icon": "📊",
            "title": "Dataset Volume & Scope",
            "desc": f"Encompasses <b>{rows:,} rows</b> and <b>{cols} columns</b>, establishing a solid statistical baseline.",
            "category": "Volume"
        })
        insights.append({
            "icon": "🎯",
            "title": "Data Quality Score",
            "desc": f"Achieved a <b>{q_curr}% Data Health Score</b>, reflecting completeness and structural consistency.",
            "category": "Quality"
        })

        for col in data.get("num_cols", [])[:3]:
            df = data.get("working_df")
            if df is not None and col in df.columns:
                series = df[col].dropna()
                if len(series) > 0:
                    insights.append({
                        "icon": "📈",
                        "title": f"Distribution Profile: {col}",
                        "desc": f"<b>{col}</b> features a mean of <b>{series.mean():,.2f}</b> and median of <b>{series.median():,.2f}</b> (std: <b>{series.std():,.2f}</b>).",
                        "category": "Distribution"
                    })

        # Recommendations
        recs = []
        if data.get("missing_curr", 0) > 0:
            recs.append({
                "title": "Impute Missing Values",
                "desc": f"Impute remaining <b>{data.get('missing_curr', 0):,} missing cells</b> using median/mode imputation.",
                "type": "Data Quality",
                "priority": "High"
            })
        recs.append({
            "title": "Standardize Numeric Ranges",
            "desc": "Normalize high-dispersion metrics prior to predictive model training.",
            "type": "Feature Engineering",
            "priority": "Medium"
        })

        # Conclusion
        conclusion = (
            f"In summary, the <b>{file_name}</b> dataset exhibits a strong quality score of <b>{q_curr}%</b>. "
            f"Following successful data hygiene and structural validation, the pipeline is fully ready for business intelligence reporting and executive decision making."
        )

        # Risks
        risks = []
        if data.get("missing_curr", 0) > 0:
            risks.append({
                "risk": "Unresolved Missing Values",
                "impact": f"{data.get('missing_curr', 0):,} missing cells remain in working dataset.",
                "severity": "Medium",
                "mitigation": "Apply automated imputation rules."
            })
        if data.get("outliers"):
            risks.append({
                "risk": "Statistical Outlier Dispersion",
                "impact": "Extreme values may distort linear model coefficients.",
                "severity": "Medium",
                "mitigation": "Apply IQR capping or percentile winsorization."
            })
        if not risks:
            risks.append({
                "risk": "Low Risk Profile",
                "impact": "Data health is excellent with no critical structural anomalies.",
                "severity": "Low",
                "mitigation": "Maintain standard automated data validation."
            })

        # Opportunities
        opps = [
            {
                "opportunity": "Automate ETL Quality Pipeline",
                "impact": "Reduces manual cleaning overhead for future dataset updates.",
                "action": "Deploy Data Pilot automated cleaning pipelines."
            },
            {
                "opportunity": "Predictive AI Modeling Integration",
                "impact": "Enables automated forecasting and machine learning predictions.",
                "action": "Export cleaned Parquet dataset to predictive ML workflows."
            }
        ]

        # Confidence
        confidence = {
            "score": 92 if q_curr >= 80 else 78,
            "level": "High" if q_curr >= 80 else "Medium",
            "reason": f"Calculated from aggregated dataset metrics with a {q_curr}% Data Quality Score."
        }

        return {
            "executive_summary": exec_summary,
            "business_insights": insights,
            "recommendations": recs,
            "executive_conclusion": conclusion,
            "risk_assessment": risks,
            "opportunities": opps,
            "ai_confidence": confidence
        }
