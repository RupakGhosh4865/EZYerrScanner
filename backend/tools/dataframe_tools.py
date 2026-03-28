import json
import pandas as pd
from langchain_core.tools import tool

@tool
def get_column_stats(column_name: str, df_json: str) -> str:
    """Returns statistics for a specific column."""
    df = pd.DataFrame(json.loads(df_json))
    if column_name not in df.columns:
        return f"Column {column_name} not found."
    
    col = df[column_name]
    stats = {
        "dtype": str(col.dtype),
        "null_count": int(col.isnull().sum()),
        "null_pct": float(col.isnull().mean() * 100),
        "unique_count": int(col.nunique()),
        "sample_values": col.dropna().head(5).tolist()
    }
    
    if pd.api.types.is_numeric_dtype(col):
        stats["min"] = float(col.min())
        stats["max"] = float(col.max())
        stats["mean"] = float(col.mean())
        stats["std"] = float(col.std())
        
    return json.dumps(stats)

@tool
def get_all_column_names(df_json: str) -> str:
    """Returns a comma-separated list of all column names."""
    df = pd.DataFrame(json.loads(df_json))
    return ", ".join(df.columns.tolist())

@tool
def detect_date_columns(df_json: str) -> str:
    """Tries parsing each column as datetime and returns a list of date columns."""
    df = pd.DataFrame(json.loads(df_json))
    date_cols = []
    for col in df.columns:
        if df[col].dtype == 'object' or df[col].dtype.name == 'category':
            try:
                sample = df[col].dropna().head(10)
                if len(sample) > 0:
                    pd.to_datetime(sample, errors='raise')
                    date_cols.append(col)
            except (ValueError, TypeError):
                continue
    return json.dumps(date_cols)

@tool
def get_dataframe_sample(df_json: str, n_rows: int = 5) -> str:
    """Returns the first n_rows as a readable markdown table string."""
    df = pd.DataFrame(json.loads(df_json))
    return df.head(n_rows).to_markdown(index=False)

@tool
def get_value_distribution(column_name: str, df_json: str) -> str:
    """Returns a summary of the value distribution for a column."""
    df = pd.DataFrame(json.loads(df_json))
    if column_name not in df.columns:
        return f"Column {column_name} not found."
    
    return df[column_name].value_counts().head(10).to_string()
