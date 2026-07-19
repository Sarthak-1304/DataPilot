import pandas as pd
from typing import Dict, Any

class ReportAgent:
    @staticmethod
    def generate_metrics_summary(df: pd.DataFrame) -> str:
        if df.empty:
            return "Dataset is empty."
            
        total_rows = len(df)
        total_cols = len(df.columns)
        num_cols = df.select_dtypes(include='number').columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        summary = f"""
### 📊 Dataset Overview
- **Total Records (Rows)**: {total_rows:,}
- **Attributes (Columns)**: {total_cols}
- **Numeric Fields**: {len(num_cols)} ({', '.join(num_cols[:4])}...)
- **Categorical Fields**: {len(cat_cols)} ({', '.join(cat_cols[:4])}...)
- **Total Missing Fields**: {df.isnull().sum().sum()}
"""
        return summary
