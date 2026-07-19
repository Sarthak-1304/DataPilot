import re

class IntentRouter:
    @staticmethod
    def detect_intent(query: str) -> str:
        q = query.lower().strip()
        
        # Chart / Visual request
        if any(w in q for w in ["chart", "plot", "graph", "visual", "trend", "distribution", "correlation", "histogram", "scatter", "bar", "pie", "line"]):
            return "chart"
            
        # Summary / Statistics request
        if any(w in q for w in ["summarize", "summary", "describe", "overview", "stats", "statistics"]):
            return "summary"
            
        # Cleaning advice
        if any(w in q for w in ["clean", "recommend", "advice", "missing", "outlier", "anomaly", "anomalies", "duplicate"]):
            return "cleaning"
            
        # SQL Generator
        if "sql" in q:
            return "sql"
            
        # Code Generator
        if any(w in q for w in ["python", "code", "script", "pandas", "snippet"]):
            return "code"
            
        # Executive Summary / Report
        if "executive" in q or "report" in q or "insight" in q:
            return "report"
            
        # Aggregation / Query
        if any(w in q for w in ["highest", "lowest", "max", "min", "top", "bottom", "average", "mean", "sum", "total", "count"]):
            return "aggregation"
            
        return "general"
