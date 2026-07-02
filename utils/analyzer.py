"""
Data Analysis Utility Functions
================================
Provides automated dataset profiling: shape, types, missing values,
duplicates, summary statistics, correlation matrix, and column-level info.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List


def get_dataset_shape(df: pd.DataFrame) -> Dict[str, int]:
    """Return row and column counts."""
    return {"rows": df.shape[0], "columns": df.shape[1]}


def get_data_types(df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame summarizing column data types."""
    dtype_df = pd.DataFrame({
        "Column": df.columns,
        "Data Type": [str(dt) for dt in df.dtypes],
        "Category": [
            "Numeric" if pd.api.types.is_numeric_dtype(dt)
            else "DateTime" if pd.api.types.is_datetime64_any_dtype(dt)
            else "Boolean" if pd.api.types.is_bool_dtype(dt)
            else "Categorical"
            for dt in df.dtypes
        ],
    })
    return dtype_df


def get_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Return per-column missing value counts and percentages."""
    missing = df.isnull().sum()
    percent = (missing / len(df) * 100).round(2)
    result = pd.DataFrame({
        "Column": missing.index,
        "Missing Count": missing.values,
        "Missing %": percent.values,
    })
    result = result.sort_values("Missing Count", ascending=False).reset_index(drop=True)
    return result


def get_unique_values(df: pd.DataFrame) -> pd.DataFrame:
    """Return per-column unique value counts and percentages."""
    unique = df.nunique()
    percent = (unique / len(df) * 100).round(2)
    return pd.DataFrame({
        "Column": unique.index,
        "Unique Count": unique.values,
        "Unique %": percent.values,
    })


def get_duplicate_info(df: pd.DataFrame) -> Dict[str, Any]:
    """Return duplicate row statistics."""
    dup_count = int(df.duplicated().sum())
    dup_pct = round(dup_count / len(df) * 100, 2) if len(df) > 0 else 0
    return {
        "duplicate_count": dup_count,
        "duplicate_percentage": dup_pct,
        "total_rows": len(df),
        "unique_rows": len(df) - dup_count,
    }


def get_summary_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return descriptive statistics for all columns.
    Numeric columns get mean/std/min/max/quartiles.
    Categorical columns get count/unique/top/freq.
    """
    numeric_df = df.select_dtypes(include=["number"])
    categorical_df = df.select_dtypes(exclude=["number"])

    parts = []
    if not numeric_df.empty:
        parts.append(numeric_df.describe().T)
    if not categorical_df.empty:
        cat_desc = categorical_df.describe().T
        parts.append(cat_desc)

    if parts:
        result = pd.concat(parts)
        result.index.name = "Column"
        return result.reset_index()
    return pd.DataFrame()


def get_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Return the Pearson correlation matrix for numeric columns."""
    numeric_df = df.select_dtypes(include=["number"])
    if numeric_df.shape[1] < 2:
        return pd.DataFrame()
    return numeric_df.corr().round(3)


def get_column_info(df: pd.DataFrame) -> pd.DataFrame:
    """Return detailed per-column information table."""
    info_rows = []
    for col in df.columns:
        series = df[col]
        info_rows.append({
            "Column": col,
            "Data Type": str(series.dtype),
            "Non-Null": int(series.notna().sum()),
            "Null": int(series.isna().sum()),
            "Null %": round(series.isna().sum() / len(df) * 100, 1) if len(df) > 0 else 0,
            "Unique": int(series.nunique()),
            "Unique %": round(series.nunique() / len(df) * 100, 1) if len(df) > 0 else 0,
            "Sample Value": str(series.dropna().iloc[0]) if series.notna().any() else "N/A",
        })
    return pd.DataFrame(info_rows)


def get_numeric_columns(df: pd.DataFrame) -> List[str]:
    """Return list of numeric column names."""
    return df.select_dtypes(include=["number"]).columns.tolist()


def get_categorical_columns(df: pd.DataFrame) -> List[str]:
    """Return list of categorical (object / category) column names."""
    return df.select_dtypes(include=["object", "category"]).columns.tolist()


def get_column_stats(df: pd.DataFrame, column: str) -> Dict[str, Any]:
    """Return detailed statistics for a single column."""
    series = df[column]
    stats = {
        "name": column,
        "dtype": str(series.dtype),
        "count": int(series.count()),
        "null_count": int(series.isna().sum()),
        "null_pct": round(series.isna().sum() / len(df) * 100, 2) if len(df) > 0 else 0,
        "unique": int(series.nunique()),
    }

    if pd.api.types.is_numeric_dtype(series):
        stats.update({
            "mean": round(float(series.mean()), 4) if series.notna().any() else None,
            "median": round(float(series.median()), 4) if series.notna().any() else None,
            "std": round(float(series.std()), 4) if series.notna().any() else None,
            "min": float(series.min()) if series.notna().any() else None,
            "max": float(series.max()) if series.notna().any() else None,
            "skewness": round(float(series.skew()), 4) if series.notna().any() else None,
            "kurtosis": round(float(series.kurtosis()), 4) if series.notna().any() else None,
        })
    else:
        top = series.mode()
        stats.update({
            "top_value": str(top.iloc[0]) if not top.empty else "N/A",
            "top_freq": int(series.value_counts().iloc[0]) if series.notna().any() else 0,
        })

    return stats
