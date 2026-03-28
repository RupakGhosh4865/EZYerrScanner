import json
from .base import BaseAgent
from ..graph.state import GraphState, Issue
from ..tools.dataframe_tools import get_all_column_names, get_dataframe_sample, detect_date_columns, get_column_stats

class SchemaIntelligenceAgent(BaseAgent):
    agent_name = "schema_intelligence"

    def analyze(self, state: GraphState) -> list[Issue]:
        return []

    def get_schema_updates(self, state: GraphState) -> dict:
        """Returns state updates: domain, column_types, primary_key_cols, date_col_pairs"""
        df_json_str = json.dumps(state["dataframe"])
        
        column_names = get_all_column_names.invoke({"df_json": df_json_str})
        sample = get_dataframe_sample.invoke({"df_json": df_json_str, "n_rows": 5})
        date_cols = detect_date_columns.invoke({"df_json": df_json_str})
        
        col_names_list = [c.strip() for c in column_names.split(",")]
        col_stats_summary = {}
        for col in col_names_list:
            col_stats_summary[col] = get_column_stats.invoke({"column_name": col, "df_json": df_json_str})
        
        prompt = f"""
        You are a data analyst. Analyze this dataset and return ONLY valid JSON.
        
        Column names: {column_names}
        Sample data (first 5 rows):
        {sample}
        Column statistics: {json.dumps(col_stats_summary)}
        Detected date columns: {date_cols}
        
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
