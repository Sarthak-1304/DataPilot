"""
Data Cleaner Utility
====================
Pure functions that accept a DataFrame and return a cleaned copy.
Each function is side-effect free and suitable for chaining.

Operations covered:
    1.  Remove duplicate rows
    2.  Handle missing values (numeric & categorical)
    3.  Change data types
    4.  Rename columns
    5.  Remove columns
    6.  Standardize text
    7.  Replace values
    8.  Remove outliers (IQR / Z-Score)
    9.  Remove null rows
    10. Remove constant columns
    11. Remove highly-missing columns
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict


# =============================================================================
# 1. Remove Duplicate Rows
# =============================================================================

def remove_duplicates(df: pd.DataFrame, subset: Optional[List[str]] = None,
                      keep: str = "first") -> pd.DataFrame:
    """Remove duplicate rows.

    Args:
        subset: Columns to consider for identifying duplicates. None = all.
        keep: 'first', 'last', or False (drop all duplicates).
    """
    out = df.copy()
    out = out.drop_duplicates(subset=subset, keep=keep)
    return out.reset_index(drop=True)


def get_duplicate_count(df: pd.DataFrame,
                        subset: Optional[List[str]] = None) -> int:
    """Return the number of duplicate rows."""
    return int(df.duplicated(subset=subset).sum())


# =============================================================================
# 2. Handle Missing Values
# =============================================================================

def fill_missing_numeric(df: pd.DataFrame, columns: List[str],
                         strategy: str = "median",
                         constant_value: float = 0) -> pd.DataFrame:
    """Fill missing values in numeric columns.

    Args:
        strategy: 'mean', 'median', 'mode', 'constant', 'drop_rows', 'drop_column'.
    """
    out = df.copy()
    for col in columns:
        if col not in out.columns or not pd.api.types.is_numeric_dtype(out[col]):
            continue
        if strategy == "mean":
            out[col] = out[col].fillna(out[col].mean())
        elif strategy == "median":
            out[col] = out[col].fillna(out[col].median())
        elif strategy == "mode":
            mode_val = out[col].mode()
            out[col] = out[col].fillna(mode_val.iloc[0] if not mode_val.empty else 0)
        elif strategy == "constant":
            out[col] = out[col].fillna(constant_value)
        elif strategy == "drop_rows":
            out = out.dropna(subset=[col])
        elif strategy == "drop_column":
            out = out.drop(columns=[col])
    return out.reset_index(drop=True)


def fill_missing_categorical(df: pd.DataFrame, columns: List[str],
                             strategy: str = "mode",
                             constant_value: str = "Unknown") -> pd.DataFrame:
    """Fill missing values in categorical columns.

    Args:
        strategy: 'mode', 'constant', 'forward_fill', 'backward_fill',
                  'drop_rows', 'drop_column'.
    """
    out = df.copy()
    for col in columns:
        if col not in out.columns:
            continue
        if strategy == "mode":
            mode_val = out[col].mode()
            fill = mode_val.iloc[0] if not mode_val.empty else "Unknown"
            out[col] = out[col].fillna(fill)
        elif strategy == "constant":
            out[col] = out[col].fillna(constant_value)
        elif strategy == "forward_fill":
            out[col] = out[col].ffill()
        elif strategy == "backward_fill":
            out[col] = out[col].bfill()
        elif strategy == "drop_rows":
            out = out.dropna(subset=[col])
        elif strategy == "drop_column":
            out = out.drop(columns=[col])
    return out.reset_index(drop=True)


# =============================================================================
# 3. Change Data Types
# =============================================================================

def change_dtype(df: pd.DataFrame, column: str,
                 target_type: str) -> pd.DataFrame:
    """Convert a column to the specified type.

    Args:
        target_type: 'integer', 'float', 'string', 'boolean', 'datetime'.
    """
    out = df.copy()
    if column not in out.columns:
        return out

    try:
        if target_type == "integer":
            # Coerce to numeric, round to nearest integer, then cast to nullable Int64
            num_series = pd.to_numeric(out[column], errors="coerce")
            out[column] = num_series.round().astype("Int64")
        elif target_type == "float":
            out[column] = pd.to_numeric(out[column], errors="coerce").astype(float)
        elif target_type == "string":
            # Convert NaN to empty string or keep as string representation
            out[column] = out[column].astype(str)
        elif target_type == "boolean":
            out[column] = out[column].astype(bool)
        elif target_type == "datetime":
            out[column] = pd.to_datetime(out[column], errors="coerce")
    except Exception:
        # Fallback to a less strict conversion
        try:
            if target_type == "integer":
                out[column] = pd.to_numeric(out[column], errors="coerce").fillna(0).astype(int)
        except Exception:
            pass

    return out



# =============================================================================
# 4. Rename Columns
# =============================================================================

def rename_columns(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    """Rename columns. Validates no duplicate names."""
    out = df.copy()
    new_names = list(out.columns)
    for old, new in mapping.items():
        if old in new_names:
            idx = new_names.index(old)
            new_names[idx] = new
    # Check for duplicates
    if len(set(new_names)) != len(new_names):
        raise ValueError("Rename would create duplicate column names.")
    out.columns = new_names
    return out


# =============================================================================
# 5. Remove Columns
# =============================================================================

def drop_columns(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Drop specified columns."""
    out = df.copy()
    existing = [c for c in columns if c in out.columns]
    return out.drop(columns=existing)


# =============================================================================
# 6. Standardize Text
# =============================================================================

def standardize_text(df: pd.DataFrame, columns: List[str],
                     operation: str = "lowercase") -> pd.DataFrame:
    """Standardize text in string columns.

    Args:
        operation: 'lowercase', 'uppercase', 'title_case',
                   'trim_spaces', 'remove_extra_spaces'.
    """
    out = df.copy()
    for col in columns:
        if col not in out.columns or out[col].dtype != "object":
            continue
        if operation == "lowercase":
            out[col] = out[col].str.lower()
        elif operation == "uppercase":
            out[col] = out[col].str.upper()
        elif operation == "title_case":
            out[col] = out[col].str.title()
        elif operation == "trim_spaces":
            out[col] = out[col].str.strip()
        elif operation == "remove_extra_spaces":
            out[col] = out[col].str.replace(r"\s+", " ", regex=True).str.strip()
    return out


# =============================================================================
# 7. Replace Values
# =============================================================================

def replace_values(df: pd.DataFrame, column: str,
                   find: str, replace_with: str,
                   use_regex: bool = False) -> pd.DataFrame:
    """Find and replace values in a column."""
    out = df.copy()
    if column not in out.columns:
        return out
    out[column] = out[column].astype(str).str.replace(
        find, replace_with, regex=use_regex
    )
    return out


# =============================================================================
# 8. Remove Outliers
# =============================================================================

def detect_outliers_iqr(df: pd.DataFrame, column: str,
                        factor: float = 1.5) -> dict:
    """Detect outliers using IQR method. Returns stats dict."""
    q1 = df[column].quantile(0.25)
    q3 = df[column].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - factor * iqr
    upper = q3 + factor * iqr
    outlier_mask = (df[column] < lower) | (df[column] > upper)
    return {
        "q1": q1, "q3": q3, "iqr": iqr,
        "lower_bound": lower, "upper_bound": upper,
        "outlier_count": int(outlier_mask.sum()),
        "mask": outlier_mask,
    }


def detect_outliers_zscore(df: pd.DataFrame, column: str,
                           threshold: float = 3.0) -> dict:
    """Detect outliers using Z-Score method."""
    mean = df[column].mean()
    std = df[column].std()
    if std == 0:
        return {"outlier_count": 0, "mask": pd.Series(False, index=df.index),
                "mean": mean, "std": std, "threshold": threshold}
    z_scores = ((df[column] - mean) / std).abs()
    outlier_mask = z_scores > threshold
    return {
        "mean": mean, "std": std, "threshold": threshold,
        "outlier_count": int(outlier_mask.sum()),
        "mask": outlier_mask,
    }


def remove_outliers(df: pd.DataFrame, column: str,
                    method: str = "iqr", factor: float = 1.5,
                    z_threshold: float = 3.0) -> pd.DataFrame:
    """Remove rows with outliers."""
    out = df.copy()
    if method == "iqr":
        info = detect_outliers_iqr(out, column, factor)
    else:
        info = detect_outliers_zscore(out, column, z_threshold)
    return out[~info["mask"]].reset_index(drop=True)


def cap_outliers(df: pd.DataFrame, column: str,
                 factor: float = 1.5) -> pd.DataFrame:
    """Cap (Winsorize) outliers using IQR method."""
    out = df.copy()
    info = detect_outliers_iqr(out, column, factor)
    out[column] = out[column].clip(lower=info["lower_bound"],
                                   upper=info["upper_bound"])
    return out


# =============================================================================
# 9. Remove Null Rows
# =============================================================================

def remove_null_rows(df: pd.DataFrame,
                     columns: Optional[List[str]] = None,
                     how: str = "any") -> pd.DataFrame:
    """Remove rows containing null values.

    Args:
        columns: If provided, only check these columns.
        how: 'any' or 'all'.
    """
    out = df.copy()
    out = out.dropna(subset=columns, how=how)
    return out.reset_index(drop=True)


# =============================================================================
# 10. Remove Constant Columns
# =============================================================================

def find_constant_columns(df: pd.DataFrame) -> List[str]:
    """Find columns with only one unique value (excluding NaN)."""
    return [c for c in df.columns if df[c].nunique(dropna=True) <= 1]


def remove_constant_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Remove columns with only one unique value."""
    const_cols = find_constant_columns(df)
    return df.drop(columns=const_cols).copy()


# =============================================================================
# 11. Remove Highly Missing Columns
# =============================================================================

def find_highly_missing_columns(df: pd.DataFrame,
                                threshold: float = 0.7) -> List[str]:
    """Find columns where missing percentage exceeds threshold (0-1)."""
    missing_pct = df.isnull().mean()
    return missing_pct[missing_pct > threshold].index.tolist()


def remove_highly_missing_columns(df: pd.DataFrame,
                                  threshold: float = 0.7) -> pd.DataFrame:
    """Remove columns exceeding the missing threshold."""
    cols = find_highly_missing_columns(df, threshold)
    return df.drop(columns=cols).copy()


# =============================================================================
# Quality Score Calculator
# =============================================================================

def is_val_date_like(val) -> bool:
    """Check if a value looks like a date string rather than an ID or simple number."""
    val_str = str(val).strip()
    if len(val_str) < 6:
        return False
    if not any(char in val_str for char in ['-', '/', '.', ' ', ',']):
        return False
    try:
        if val_str.isdigit():
            return False
        pd.to_datetime(val_str)
        return True
    except (ValueError, TypeError):
        return False


def calculate_quality_score(df: pd.DataFrame) -> dict:
    """Calculate a comprehensive data quality score out of 100 based on deductions.

    Factors considered:
        - Completeness (30 pts max)
        - Uniqueness (20 pts max)
        - Consistency (20 pts max)
        - Validity (20 pts max)
        - Column Naming (10 pts max)
    """
    if df is None or df.empty:
        return {
            "total": 0,
            "completeness": 0.0,
            "uniqueness": 0.0,
            "consistency": 0.0,
            "validity": 0.0,
            "naming": 0.0,
            "label": "Poor",
        }

    n_rows = len(df)
    n_cols = len(df.columns)
    total_cells = n_rows * n_cols

    # --- 1. Completeness Deduction (up to 30 pts) ---
    overall_missing_ratio = df.isnull().sum().sum() / total_cells if total_cells > 0 else 0
    base_comp_deduct = overall_missing_ratio * 30

    col_missing_ratios = df.isnull().mean()
    high_missing_cols = sum(1 for c in df.columns if col_missing_ratios[c] > 0.5)
    med_missing_cols = sum(1 for c in df.columns if 0.2 < col_missing_ratios[c] <= 0.5)

    extra_comp_deduct = (high_missing_cols * 5) + (med_missing_cols * 2)
    completeness_deduction = min(30.0, base_comp_deduct + extra_comp_deduct)
    completeness_score = 30.0 - completeness_deduction

    # --- 2. Uniqueness Deduction (up to 20 pts) ---
    dup_ratio = df.duplicated().sum() / n_rows if n_rows > 0 else 0
    # Base deduction of 5.0 for having any duplicates, plus scale on ratio
    uniqueness_deduction = min(20.0, (dup_ratio * 120) + (5.0 if dup_ratio > 0 else 0.0))
    uniqueness_score = 20.0 - uniqueness_deduction

    # --- 3. Consistency Deduction (up to 20 pts) ---
    # - Mixed types within a column
    mixed_cols = 0
    for col in df.columns:
        inferred = pd.api.types.infer_dtype(df[col].dropna())
        if inferred.startswith("mixed") or "mixed" in inferred:
            mixed_cols += 1
    mixed_deduct = mixed_cols * 5

    # - Numeric columns parsed as objects (dirty numbers)
    dirty_numeric_cols = 0
    for col in df.select_dtypes(include="object").columns:
        non_null_vals = df[col].dropna()
        if len(non_null_vals) > 0:
            parsed = pd.to_numeric(non_null_vals, errors="coerce")
            parsed_ratio = parsed.notna().sum() / len(non_null_vals)
            if 0.15 < parsed_ratio < 1.0:
                dirty_numeric_cols += 1
    dirty_numeric_deduct = dirty_numeric_cols * 4

    # - Date columns stored as strings
    date_cols_as_str = 0
    for col in df.select_dtypes(include="object").columns:
        non_null_vals = df[col].dropna().head(50)
        if len(non_null_vals) > 5:
            parsed_dates = sum(1 for val in non_null_vals if is_val_date_like(val))
            date_ratio = parsed_dates / len(non_null_vals)
            if date_ratio > 0.8:
                date_cols_as_str += 1
    date_deduct = date_cols_as_str * 2

    # - Casing/whitespace inconsistencies in text categories
    casing_inconsistent_cols = 0
    for col in df.select_dtypes(include="object").columns:
        non_null_vals = df[col].dropna()
        if len(non_null_vals) > 0:
            try:
                raw_unique = non_null_vals.astype(str).nunique()
                clean_unique = non_null_vals.astype(str).str.lower().str.strip().nunique()
                if raw_unique > clean_unique:
                    casing_inconsistent_cols += 1
            except Exception:
                pass
    casing_deduct = casing_inconsistent_cols * 3

    consistency_deduction = min(20.0, mixed_deduct + dirty_numeric_deduct + date_deduct + casing_deduct)
    consistency_score = 20.0 - consistency_deduction

    # --- 4. Validity Deduction (up to 20 pts) ---
    # - Outliers (>0.5% of rows are outliers in a numeric column)
    num_cols = df.select_dtypes(include="number").columns
    outlier_cols_count = 0
    if len(num_cols) > 0:
        for col in num_cols:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            if iqr > 0:
                outliers = ((df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)).sum()
                if outliers / len(df) > 0.005:
                    outlier_cols_count += 1
    outlier_deduct = outlier_cols_count * 3

    # - Negative values in strictly positive fields (e.g. quantity, age, sales, price)
    invalid_negative_cols = 0
    for col in df.select_dtypes(include="number").columns:
        col_lower = col.lower()
        if any(kw in col_lower for kw in ["quantity", "age", "qty", "sales", "price"]):
            non_null = df[col].dropna()
            if len(non_null) > 0:
                neg_ratio = (non_null < 0).sum() / len(non_null)
                if 0.0 < neg_ratio < 0.25:
                    invalid_negative_cols += 1
    invalid_neg_deduct = invalid_negative_cols * 4

    # - Constant columns
    constant_cols = sum(1 for c in df.columns if df[c].nunique(dropna=True) <= 1)
    constant_deduct = constant_cols * 3

    # - Fully empty columns
    empty_cols = sum(1 for c in df.columns if df[c].isnull().all())
    empty_deduct = empty_cols * 5

    validity_deduction = min(20.0, outlier_deduct + constant_deduct + empty_deduct + invalid_neg_deduct)
    validity_score = 20.0 - validity_deduction

    # --- 5. Column Naming Deduction (up to 10 pts) ---
    unnamed_cols = sum(1 for c in df.columns if str(c).startswith("Unnamed") or str(c).strip() == "")
    unnamed_deduct = unnamed_cols * 4

    special_char_cols = 0
    for c in df.columns:
        c_str = str(c).strip()
        if not c_str.startswith("Unnamed") and c_str != "":
            if any(char in c_str for char in ['#', '$', '@', '!', '%', '^', '&', '*', '(', ')']):
                special_char_cols += 1
    special_char_deduct = special_char_cols * 1

    naming_deduction = min(10.0, unnamed_deduct + special_char_deduct)
    naming_score = 10.0 - naming_deduction

    total = int(round(completeness_score + uniqueness_score + consistency_score + validity_score + naming_score))
    total = min(100, max(0, total))

    if total >= 85:
        label = "Excellent"
    elif total >= 70:
        label = "Good"
    elif total >= 50:
        label = "Fair"
    else:
        label = "Poor"

    return {
        "total": total,
        "completeness": round(completeness_score, 1),
        "uniqueness": round(uniqueness_score, 1),
        "consistency": round(consistency_score, 1),
        "validity": round(validity_score, 1),
        "naming": round(naming_score, 1),
        "label": label,
    }
