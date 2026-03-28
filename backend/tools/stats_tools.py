import json
import pandas as pd
import numpy as np
from scipy import stats
from langchain_core.tools import tool

@tool
def compute_zscore_outliers(column_name: str, df_json: str, threshold: float = 2.5) -> str:
    """Computes Z-scores for a numeric column and returns outliers."""
    df = pd.DataFrame(json.loads(df_json))
    if column_name not in df.columns:
        return f"Column {column_name} not found."
    
    col = df[column_name].dropna()
    if not pd.api.types.is_numeric_dtype(col):
        return f"Column {column_name} is not numeric."
    
    z_scores = np.abs(stats.zscore(col))
    outliers = col[z_scores > threshold]
    outlier_dict = {str(idx): val for idx, val in outliers.items()}
    return json.dumps(outlier_dict)

@tool
def compute_iqr_outliers(column_name: str, df_json: str) -> str:
    """Finds outliers using the IQR method."""
    df = pd.DataFrame(json.loads(df_json))
    if column_name not in df.columns:
        return f"Column {column_name} not found."
    
    col = df[column_name].dropna()
    if not pd.api.types.is_numeric_dtype(col):
        return f"Column {column_name} is not numeric."
        
    q1 = col.quantile(0.25)
    q3 = col.quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    outliers = col[(col < lower_bound) | (col > upper_bound)]
    outlier_dict = {str(idx): val for idx, val in outliers.items()}
    return json.dumps(outlier_dict)

@tool
def correlation_check(col1: str, col2: str, df_json: str) -> str:
    """Pearson correlation between two numeric columns."""
    df = pd.DataFrame(json.loads(df_json))
    if col1 not in df.columns or col2 not in df.columns:
        return "One or both columns not found."
    
    if not pd.api.types.is_numeric_dtype(df[col1]) or not pd.api.types.is_numeric_dtype(df[col2]):
        return "Both columns must be numeric."
        
    corr = df[col1].corr(df[col2])
    
    interpretation = "Weak"
    if abs(corr) > 0.7:
        interpretation = "Strong"
    elif abs(corr) > 0.3:
        interpretation = "Moderate"
        
    return json.dumps({"correlation": float(corr), "interpretation": interpretation})
