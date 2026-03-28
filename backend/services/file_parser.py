import pandas as pd
import io

def parse_file(file_bytes: bytes, filename: str) -> tuple[dict, dict]:
    size_kb = len(file_bytes) / 1024
    if size_kb > 10 * 1024:
        raise ValueError(f"File {filename} exceeds 10MB limit.")

    file_ext = filename.split(".")[-1].lower()
    
    try:
        if file_ext == "csv":
            try:
                df = pd.read_csv(io.BytesIO(file_bytes), encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(io.BytesIO(file_bytes), encoding="latin-1")
        elif file_ext in ["xls", "xlsx"]:
            df = pd.read_excel(io.BytesIO(file_bytes))
        elif file_ext == "json":
            df = pd.read_json(io.BytesIO(file_bytes))
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    except Exception as e:
        raise ValueError(f"Error parsing file: {str(e)}")

    metadata = {
        "filename": filename,
        "rows": len(df),
        "columns": df.columns.tolist(),
        "size_kb": format(size_kb, ".2f"),
        "file_type": file_ext
    }

    return df.to_dict('records'), metadata
