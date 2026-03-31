import os
import uuid
import pandas as pd
from abc import ABC, abstractmethod
from typing import List, Any
from langchain_groq import ChatGroq
from graph_ezyerr.state import GraphState, Issue

class BaseAgent(ABC):
    @property
    @abstractmethod
    def agent_name(self) -> str:
        pass

    @property
    def llm(self) -> ChatGroq:
        return ChatGroq(
            model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            temperature=0.1,
            api_key=os.getenv("GROQ_API_KEY")
        )

    @abstractmethod
    def analyze(self, state: GraphState) -> List[Issue]:
        pass

    def _create_issue(self, title: str, description: str, severity: str, rows: List[int], cols: List[str], fix: Any, count: int, confidence: float) -> Issue:
        # Handle cases where Gemini sends a list for suggested_fix
        if isinstance(fix, list):
            fix = ". ".join(str(f) for f in fix)
            
        return {
            "id": str(uuid.uuid4()),
            "agent": self.agent_name,
            "title": title,
            "description": description,
            "severity": severity,
            "affected_rows": rows,
            "affected_columns": cols,
            "suggested_fix": fix,
            "count": count,
            "confidence": confidence
        }

    def _get_dataframe(self, state: GraphState) -> pd.DataFrame:
        return pd.DataFrame(state["dataframe"])
