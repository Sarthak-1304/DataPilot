import pandas as pd
import numpy as np
import google.generativeai as genai
from ai.gemini_manager import get_gemini_api_key

class DataFrameAgent:
    @staticmethod
    def query_with_pandas(question: str, df: pd.DataFrame) -> str:
        """Generate pandas code to answer the query, execute it, and return results."""
        prompt = f"""
You are a Python code generator. Write a single, valid, concise Python code block using Pandas to extract the exact data needed to answer this question about a DataFrame named `df`:
Question: "{question}"

DataFrame columns and types:
{ {col: str(dtype) for col, dtype in zip(df.columns, df.dtypes)} }

Rules:
1. ONLY return python code. Do not wrap it in markdown code blocks like ```python. Just the raw code.
2. The final result of the calculation must be assigned to a variable named `result`.
3. Keep it safe and self-contained. Do not import arbitrary packages.
4. Assumes `df` is the active pandas DataFrame.
"""
        key = get_gemini_api_key()
        if not key:
            return "Error: Gemini API Key not configured."
            
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            code = response.text.strip()
            
            # Clean response text
            if code.startswith("```"):
                code = "\n".join(code.split("\n")[1:-1]) if code.endswith("```") else code[3:]
            code = code.replace("python\n", "").strip()
            
            # Controlled execution
            local_vars = {"df": df, "pd": pd, "np": np, "result": None}
            exec(code, {}, local_vars)
            
            result = local_vars.get("result")
            if result is not None:
                if isinstance(result, (pd.DataFrame, pd.Series)):
                    return result.to_markdown()
                return str(result)
            else:
                # Try evaluating the code as expression if result is None
                res = eval(code, {}, local_vars)
                if res is not None:
                    if isinstance(res, (pd.DataFrame, pd.Series)):
                        return res.to_markdown()
                    return str(res)
            return "Calculation completed successfully, but returned no value."
        except Exception as e:
            return f"Calculated fallback context instead of running Pandas directly (Error: {str(e)})."

    @staticmethod
    def generate_plotly_code(question: str, df: pd.DataFrame) -> str:
        """Generate Plotly Express python code based on a question."""
        prompt = f"""
You are a Python data visualization expert. Write a single block of Python code using Plotly Express to generate a chart that answers the user's question about a DataFrame named `df`:
Question: "{question}"

DataFrame columns and types:
{ {col: str(dtype) for col, dtype in zip(df.columns, df.dtypes)} }

Rules:
1. ONLY return python code. Do not wrap it in markdown code blocks like ```python. Just the raw code.
2. The final plotly figure object MUST be assigned to a variable named `fig`.
3. Keep it safe and self-contained. Do not import arbitrary packages.
4. Assumes `df` is the active pandas DataFrame.
"""
        key = get_gemini_api_key()
        if not key:
            return ""
            
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            code = response.text.strip()
            
            # Clean response text
            if code.startswith("```"):
                code = "\n".join(code.split("\n")[1:-1]) if code.endswith("```") else code[3:]
            code = code.replace("python\n", "").strip()
            return code
        except Exception:
            return ""
