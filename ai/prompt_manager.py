import pandas as pd
from typing import Dict, Any

class PromptManager:
    @staticmethod
    def get_system_prompt() -> str:
        return (
            "You are a Senior Data Analyst, Business Intelligence Consultant, and Data Scientist. "
            "Your role is to act as an expert analyst and interpreter, helping users understand their datasets. "
            "You must obey these strict rules:\n"
            "1. NEVER hallucinate or invent values. Always ground your analysis in the actual data results provided.\n"
            "2. Explain findings clearly in a structured, professional business tone.\n"
            "3. Provide actionable business recommendations whenever possible.\n"
            "4. Format your responses in clean Markdown. Use bold, lists, and tables to organize your findings.\n"
            "5. If a calculation results in an error or is missing, explicitly mention that the data wasn't available."
        )
        
    @staticmethod
    def construct_analysis_prompt(question: str, df: pd.DataFrame, execution_result: str = None, intent: str = "general") -> str:
        # Build context
        col_types = {col: str(dtype) for col, dtype in zip(df.columns, df.dtypes)}
        num_rows, num_cols = df.shape
        
        # Get basic stats
        desc = df.describe(include='all').to_string() if not df.empty else "Empty DataFrame"
        null_counts = df.isnull().sum().to_dict()
        
        prompt = f"""
[DATASET METADATA]
- Rows: {num_rows}
- Columns: {num_cols}
- Column Names and Types: {col_types}
- Missing Values (Null counts): {null_counts}

[SUMMARY STATISTICS]
{desc}
"""
        if execution_result:
            prompt += f"\n[LOCAL PANDAS PRE-CALCULATED RESULTS]\n{execution_result}\n"
            
        prompt += f"""
[USER QUESTION]
"{question}"

[DETECTED INTENT]
{intent}

[INSTRUCTIONS]
Provide a clear, natural-language business explanation of the results in response to the user's question.
If local pandas calculations are present, interpret them for the business.
"""
        return prompt
