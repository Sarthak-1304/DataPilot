import pandas as pd
import numpy as np
import json
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from ai.gemini_manager import get_gemini_api_key, get_best_available_model, is_gemini_configured


class InsightAgent:
    """Agent that generates AI-powered and rule-based insights from DataFrames."""

    # -----------------------------------------------------------------
    # Internal: Build a concise data profile string for Gemini prompts
    # -----------------------------------------------------------------
    @staticmethod
    def _build_data_profile(df: pd.DataFrame) -> str:
        """Create a compact statistical summary of the DataFrame for LLM prompts."""
        lines = []
        lines.append(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")
        lines.append(f"Columns: {', '.join(df.columns.tolist())}")

        # Data types
        dtype_counts = df.dtypes.value_counts().to_dict()
        lines.append(f"Data types: {', '.join(f'{v} {k}' for k, v in dtype_counts.items())}")

        # Missing values
        missing = df.isnull().sum()
        missing_cols = missing[missing > 0]
        if len(missing_cols) > 0:
            missing_strs = [f"{col}: {cnt} ({cnt/len(df)*100:.1f}%)" for col, cnt in missing_cols.items()]
            lines.append(f"Missing values: {'; '.join(missing_strs)}")
        else:
            lines.append("Missing values: None")

        # Numeric summary
        num_cols = df.select_dtypes(include='number').columns.tolist()
        if num_cols:
            desc = df[num_cols].describe().round(2)
            lines.append(f"\nNumeric summary:\n{desc.to_string()}")

            # Skewness
            skew = df[num_cols].skew().round(2)
            lines.append(f"\nSkewness: {skew.to_dict()}")

            # Correlations (top pairs)
            if len(num_cols) >= 2:
                corr = df[num_cols].corr()
                for i in range(len(corr)):
                    corr.iloc[i, i] = 0
                pairs = []
                seen = set()
                for c1 in corr.columns:
                    for c2 in corr.columns:
                        if c1 != c2 and (c2, c1) not in seen:
                            val = corr.loc[c1, c2]
                            if abs(val) > 0.3:
                                pairs.append(f"{c1} <-> {c2}: {val:.2f}")
                                seen.add((c1, c2))
                if pairs:
                    lines.append(f"\nNotable correlations: {'; '.join(pairs[:10])}")

        # Categorical summary
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        if cat_cols:
            cat_info = []
            for col in cat_cols[:8]:
                nunique = df[col].nunique()
                top = df[col].value_counts().head(3).to_dict()
                cat_info.append(f"  {col}: {nunique} unique, top values: {top}")
            lines.append(f"\nCategorical columns:\n" + "\n".join(cat_info))

        # Duplicates
        dup_count = df.duplicated().sum()
        if dup_count > 0:
            lines.append(f"\nDuplicate rows: {dup_count} ({dup_count/len(df)*100:.1f}%)")

        # Outliers (IQR)
        outlier_cols = []
        for col in num_cols:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            if iqr > 0:
                outlier_count = ((df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)).sum()
                if outlier_count > 0:
                    outlier_cols.append(f"{col}: {outlier_count}")
        if outlier_cols:
            lines.append(f"\nOutlier columns (IQR): {'; '.join(outlier_cols)}")

        return "\n".join(lines)

    @staticmethod
    def _call_gemini(prompt: str, system_instruction: str) -> Optional[str]:
        """Call Gemini API and return raw text response, or None on failure."""
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
        except Exception:
            return None

    @staticmethod
    def _clean_json_response(raw: str) -> str:
        """Extract clean JSON array string from raw LLM output."""
        import re
        text = raw.strip()
        # Find first '[' and last ']'
        start = text.find('[')
        end = text.rfind(']')
        if start != -1 and end != -1 and end > start:
            return text[start:end+1].strip()
        return text

    # -----------------------------------------------------------------
    # AI-Powered: Smart Insights
    # -----------------------------------------------------------------
    @staticmethod
    def generate_ai_smart_insights(df: pd.DataFrame) -> Optional[List[Dict[str, str]]]:
        """Generate smart data insights using Gemini AI. Returns None on failure."""
        if not is_gemini_configured():
            return None

        profile = InsightAgent._build_data_profile(df)

        system_instruction = (
            "You are an expert data analyst. You analyze datasets and produce "
            "precise, actionable, and insightful observations. Be specific — "
            "reference actual column names, values, and statistics. Avoid generic filler."
        )

        prompt = f"""Analyze this dataset profile and generate 8-12 deep, specific data insights.

DATA PROFILE:
{profile}

Return ONLY a valid JSON array. Each element must have exactly these keys:
- "title": short insight title (max 8 words)
- "desc": detailed explanation (1-2 sentences, use <b> tags for emphasis on column names and values)
- "badge": category label (one of: Variance, Skewness, Normality, Completeness, Distribution, Cardinality, Correlation, Seasonality, Outlier, Quality, Pattern, General)
- "color": one of: blue, orange, purple, green, red

Example format:
[{{"title": "High Salary Dispersion", "desc": "Column <b>Salary</b> has a standard deviation of <b>25,430</b>, indicating significant pay variation across the dataset.", "badge": "Variance", "color": "blue"}}]

IMPORTANT: Return ONLY the JSON array, no markdown, no code blocks, no explanation."""

        raw = InsightAgent._call_gemini(prompt, system_instruction)
        if not raw:
            return None

        try:
            cleaned = InsightAgent._clean_json_response(raw)
            insights = json.loads(cleaned)
            # Validate structure
            valid = []
            valid_colors = {"blue", "orange", "purple", "green", "red"}
            for item in insights:
                if isinstance(item, dict) and all(k in item for k in ("title", "desc", "badge", "color")):
                    if item["color"] not in valid_colors:
                        item["color"] = "blue"
                    valid.append(item)
            return valid if valid else None
        except (json.JSONDecodeError, TypeError, KeyError):
            return None

    # -----------------------------------------------------------------
    # AI-Powered: Business Insights
    # -----------------------------------------------------------------
    @staticmethod
    def generate_ai_business_insights(df: pd.DataFrame) -> Optional[List[str]]:
        """Generate executive business insights using Gemini AI. Returns None on failure."""
        if not is_gemini_configured():
            return None

        profile = InsightAgent._build_data_profile(df)

        system_instruction = (
            "You are a senior business analyst presenting findings to C-level executives. "
            "Write in a professional, concise, and actionable tone. Use data-driven language."
        )

        prompt = f"""Based on this dataset profile, generate 6-10 executive-level business insights.

DATA PROFILE:
{profile}

Each insight should:
- Start with a relevant emoji (📊, 📦, 🎯, 💡, ⚡, 📈, 🔍, etc.)
- Use <b> tags for emphasis on key metrics and column names
- Be 1-2 sentences, professional business language
- Reference specific numbers and percentages from the data

Return ONLY a valid JSON array of strings. No markdown, no code blocks.
Example: ["📊 <b>Revenue</b> shows a mean of <b>$45,200</b> with strong positive skew, suggesting a few high-value transactions drive the bulk of income."]"""

        raw = InsightAgent._call_gemini(prompt, system_instruction)
        if not raw:
            return None

        try:
            cleaned = InsightAgent._clean_json_response(raw)
            insights = json.loads(cleaned)
            if isinstance(insights, list) and all(isinstance(s, str) for s in insights):
                return insights if insights else None
            return None
        except (json.JSONDecodeError, TypeError):
            return None

    # -----------------------------------------------------------------
    # AI-Powered: Recommendations
    # -----------------------------------------------------------------
    @staticmethod
    def generate_ai_recommendations(
        df: pd.DataFrame,
        quality_dict: Dict[str, Any],
        outlier_col_count: int
    ) -> Optional[List[Dict[str, str]]]:
        """Generate AI-powered actionable recommendations. Returns None on failure."""
        if not is_gemini_configured():
            return None

        profile = InsightAgent._build_data_profile(df)

        quality_summary = (
            f"Quality Score: {quality_dict.get('total', 'N/A')}% ({quality_dict.get('label', 'N/A')})\n"
            f"Completeness: {quality_dict.get('completeness', 'N/A')}/30\n"
            f"Uniqueness: {quality_dict.get('uniqueness', 'N/A')}/20\n"
            f"Consistency: {quality_dict.get('consistency', 'N/A')}/20\n"
            f"Outlier Columns: {outlier_col_count}"
        )

        system_instruction = (
            "You are a machine learning engineer and data quality expert. "
            "Provide specific, prioritized, actionable recommendations to improve "
            "data quality and ML-readiness. Be precise — reference column names and metrics."
        )

        prompt = f"""Based on this dataset profile and quality assessment, generate 6-10 specific, actionable recommendations.

DATA PROFILE:
{profile}

QUALITY ASSESSMENT:
{quality_summary}

Return ONLY a valid JSON array. Each element must have:
- "rec": the recommendation text (use <b> tags for emphasis, 1-2 sentences)
- "type": category (one of: Data Quality, Statistics, Consistency, AI Prep, Performance, Feature Engineering, Missing Data, Outliers)

Order by priority (most critical first).
Example: [{{"rec": "<b>Impute Missing Values in Age:</b> Column <b>Age</b> has 12.5% missing data. Use median imputation to preserve distribution shape.", "type": "Missing Data"}}]

IMPORTANT: Return ONLY the JSON array, no markdown, no code blocks."""

        raw = InsightAgent._call_gemini(prompt, system_instruction)
        if not raw:
            return None

        try:
            cleaned = InsightAgent._clean_json_response(raw)
            recs = json.loads(cleaned)
            valid = []
            for item in recs:
                if isinstance(item, dict) and "rec" in item and "type" in item:
                    valid.append(item)
            return valid if valid else None
        except (json.JSONDecodeError, TypeError, KeyError):
            return None

    # -----------------------------------------------------------------
    # AI-Powered: Subtab Insights (Outliers, Time Series, Missing)
    # -----------------------------------------------------------------
    @staticmethod
    def generate_ai_outliers_insight(df: pd.DataFrame, outlier_info: dict) -> Optional[str]:
        """Generate AI commentary on outlier profiles."""
        if not is_gemini_configured() or not outlier_info:
            return None
        prompt = f"Analyze these outlier profiles in the dataset and provide a concise, 2-sentence executive interpretation referencing specific column names, outlier percentages, and recommended capping actions:\n{outlier_info}"
        system_instruction = "You are a statistics expert. Be concise, precise, and use <b> HTML tags for emphasis."
        return InsightAgent._call_gemini(prompt, system_instruction)

    @staticmethod
    def generate_ai_timeseries_insight(df: pd.DataFrame, date_col: str, num_col: str) -> Optional[str]:
        """Generate AI commentary on time series trends."""
        if not is_gemini_configured() or not date_col or not num_col:
            return None
        prompt = f"Analyze temporal changes for column '{num_col}' plotted over date column '{date_col}' in a dataset of {len(df)} rows. Provide a 2-sentence trend and seasonality interpretation using <b> HTML tags for emphasis."
        system_instruction = "You are a time series forecasting analyst. Be concise, precise, and professional."
        return InsightAgent._call_gemini(prompt, system_instruction)

    @staticmethod
    def generate_ai_missing_insight(df: pd.DataFrame, missing_df: pd.DataFrame) -> Optional[str]:
        """Generate AI commentary on missing data patterns."""
        if not is_gemini_configured() or missing_df.empty or missing_df["Missing Count"].sum() == 0:
            return None
        top_missing = missing_df.head(5).to_dict(orient="records")
        prompt = f"Analyze these missing value counts in the dataset and provide a 2-sentence risk assessment and imputation recommendation using <b> HTML tags for emphasis:\n{top_missing}"
        system_instruction = "You are a data quality expert. Be concise and precise."
        return InsightAgent._call_gemini(prompt, system_instruction)

    # -----------------------------------------------------------------
    # Rule-Based Fallbacks (existing functionality preserved)
    # -----------------------------------------------------------------
    @staticmethod
    def get_cleaning_recommendations(df: pd.DataFrame) -> List[str]:
        recs = []
        if df.empty:
            return ["Dataset is empty."]

        # Check missing values
        null_counts = df.isnull().sum()
        for col, count in null_counts.items():
            if count > 0:
                pct = (count / len(df)) * 100
                recs.append(f"🧹 Column **{col}** has {count} missing values ({pct:.1f}%). Consider imputing with mean/median/mode or deleting rows.")

        # Check duplicate rows
        dup_count = df.duplicated().sum()
        if dup_count > 0:
            recs.append(f"👯 Found {dup_count} duplicate rows. Recommend removing duplicate entries.")

        # Check numeric columns for outliers
        num_cols = df.select_dtypes(include='number').columns
        for col in num_cols:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outliers = df[(df[col] < lower) | (df[col] > upper)]
            if len(outliers) > 0:
                recs.append(f"📈 Column **{col}** has {len(outliers)} statistical outliers. Inspect if they are valid values or data entry errors.")

        if not recs:
            recs.append("✨ No obvious cleaning issues detected. The dataset is looking great!")
        return recs

    @staticmethod
    def suggest_charts(df: pd.DataFrame) -> List[Dict[str, str]]:
        suggestions = []
        num_cols = df.select_dtypes(include='number').columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

        if len(num_cols) >= 2:
            suggestions.append({
                "type": "Scatter Plot",
                "desc": f"Relationship between **{num_cols[0]}** and **{num_cols[1]}** to spot correlations."
            })
        if len(cat_cols) >= 1 and len(num_cols) >= 1:
            suggestions.append({
                "type": "Bar Chart",
                "desc": f"Distribution of total/average **{num_cols[0]}** across categories in **{cat_cols[0]}**."
            })
        if len(num_cols) >= 1:
            suggestions.append({
                "type": "Histogram",
                "desc": f"Frequency distribution of **{num_cols[0]}** to check skewness."
            })
        if any("date" in col.lower() or "time" in col.lower() for col in df.columns) and len(num_cols) >= 1:
            date_col = [col for col in df.columns if "date" in col.lower() or "time" in col.lower()][0]
            suggestions.append({
                "type": "Line Chart",
                "desc": f"Trend of **{num_cols[0]}** plotted over time (**{date_col}**)."
            })

        return suggestions
