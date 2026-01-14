"""
Workflow module for AI Finance Assistant.
Provides LangGraph-based multi-agent orchestration.
"""

from src.workflow.router import QueryRouter, route_query
from src.workflow.graph import (
    FinanceAssistantWorkflow,
    get_workflow,
    process_query
)

__all__ = [
    "QueryRouter",
    "route_query",
    "FinanceAssistantWorkflow",
    "get_workflow",
    "process_query",
]
