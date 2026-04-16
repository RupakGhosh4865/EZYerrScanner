import json
import pandas as pd
from langchain_core.tools import tool

def _get_df(data: any) -> pd.DataFrame:
    """Helper to get a DataFrame from various input types."""
    if isinstance(data, str):
        try:
            return pd.DataFrame(json.loads(data))
        except:
            return pd.DataFrame()
    if isinstance(data, list):
        return pd.DataFrame(data)
    if isinstance(data, pd.DataFrame):
        return data
    return pd.DataFrame()

@tool
def get_column_stats(column_name: str, data: any) -> str:
    """Returns statistics for a specific column. Data can be JSON string or list of dicts."""
    df = _get_df(data)
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
        stats["min"] = float(col.min()) if not col.dropna().empty else 0
        stats["max"] = float(col.max()) if not col.dropna().empty else 0
        stats["mean"] = float(col.mean()) if not col.dropna().empty else 0
        stats["std"] = float(col.std()) if not col.dropna().empty else 0
        
    return json.dumps(stats)

@tool
def get_all_column_names(data: any) -> str:
    """Returns a comma-separated list of all column names."""
    df = _get_df(data)
    return ", ".join(df.columns.tolist())

@tool
def detect_date_columns(data: any) -> str:
    """Tries parsing each column as datetime and returns a list of date columns."""
    df = _get_df(data)
    date_cols = []
    for col in df.columns:
        if df[col].dtype == 'object' or df[col].dtype.name == 'category':
            try:
                sample = df[col].dropna().head(10)
                if len(sample) > 0:
                    pd.to_datetime(sample, errors='raise')
                    date_cols.append(col)
            except:
                continue
    return json.dumps(date_cols)

@tool
def get_dataframe_sample(data: any, n_rows: int = 5) -> str:
    """Returns the first n_rows as a readable markdown table string."""
    df = _get_df(data)
    return df.head(n_rows).to_markdown(index=False)

@tool
def get_value_distribution(column_name: str, data: any) -> str:
    """Returns a summary of the value distribution for a column."""
    df = _get_df(data)
    if column_name not in df.columns:
        return f"Column {column_name} not found."
    
    return df[column_name].value_counts().head(10).to_string()
