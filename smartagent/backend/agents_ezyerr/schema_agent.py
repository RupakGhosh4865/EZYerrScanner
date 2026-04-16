import json
import pandas as pd
from agents_ezyerr.base import BaseAgent
from graph_ezyerr.state import GraphState, Issue
from tools_ezyerr.dataframe_tools import get_all_column_names, get_dataframe_sample, detect_date_columns, get_column_stats

class SchemaIntelligenceAgent(BaseAgent):
    agent_name = "schema_intelligence"

    def analyze(self, state: GraphState) -> list[Issue]:
        return []

    def get_schema_updates(self, state: GraphState) -> dict:
        """Returns state updates: domain, column_types, primary_key_cols, date_col_pairs"""
        df = pd.DataFrame(state["dataframe"])
        
        # Performance: Only use a limited sample for schema reasoning to avoid JSON/Memory overhead
        sample_df = df.head(100) 
        
        try:
            column_names = get_all_column_names.invoke({"data": sample_df})
            sample_table = get_dataframe_sample.invoke({"data": sample_df, "n_rows": 5})
            date_cols_json = detect_date_columns.invoke({"data": sample_df})
            date_cols = json.loads(date_cols_json)
            
            col_names_list = [c.strip() for c in column_names.split(",")]
            col_stats_summary = {}
            for col in col_names_list[:20]: # Limit to first 20 columns for stats reasoning
                col_stats_summary[col] = json.loads(get_column_stats.invoke({"column_name": col, "data": sample_df}))
            
            prompt = f"""
            You are a data analyst. Analyze this dataset and return ONLY valid JSON.
            
            Column names: {column_names}
            Sample data (first 5 rows):
            {sample_table}
            Column statistics (summary): {json.dumps(col_stats_summary)}
            Detected possible date columns: {date_cols}
            
            Return this exact JSON structure with no other text:
            {{
              "domain": "project_management|hr|finance|sales|inventory|generic",
              "column_types": {{
                "col_name": "date|id|status|numeric|percentage|text|email|name"
              }},
              "primary_key_cols": ["col1"],
              "date_col_pairs": [["start_col", "end_col"]],
              "status_columns": ["col1"],
              "amount_columns": ["col1"],
              "reasoning": "brief explanation"
            }}
            """
            
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
                
            schema_info = json.loads(content)
            return schema_info

        except Exception as e:
            print(f"SCHEMA_AI_ERROR: {e}. Falling back to heuristics.")
            return self._heuristic_fallback(df)

    def _heuristic_fallback(self, df: pd.DataFrame) -> dict:
        """Simple heuristic fallback if LLM/Groq fails or data is too complex."""
        column_types = {}
        date_cols = []
        status_cols = []
        amount_cols = []
        
        for col in df.columns:
            dtype = str(df[col].dtype)
            col_lower = col.lower()
            
            if "date" in col_lower or "start" in col_lower or "end" in col_lower:
                column_types[col] = "date"
                date_cols.append(col)
            elif "status" in col_lower:
                column_types[col] = "status"
                status_cols.append(col)
            elif "id" in col_lower:
                column_types[col] = "id"
            elif "budget" in col_lower or "cost" in col_lower or "amount" in col_lower:
                column_types[col] = "numeric"
                amount_cols.append(col)
            elif "pct" in col_lower or "percent" in col_lower:
                column_types[col] = "percentage"
            elif pd.api.types.is_numeric_dtype(df[col]):
                column_types[col] = "numeric"
            else:
                column_types[col] = "text"
        
        # Logic for date pairs
        date_pairs = []
        if len(date_cols) >= 2:
            # Pair start/end if they exist
            starts = [c for c in date_cols if "start" in c.lower()]
            ends = [c for c in date_cols if "end" in c.lower() or "due" in c.lower()]
            for s in starts:
                for e in ends:
                    date_pairs.append([s, e])
                    
        return {
            "domain": "generic",
            "column_types": column_types,
            "primary_key_cols": [df.columns[0]] if not df.empty else [],
            "date_col_pairs": date_pairs,
            "status_columns": status_cols,
            "amount_columns": amount_cols,
            "reasoning": "Heuristic fallback used due to AI connection issue."
        }
