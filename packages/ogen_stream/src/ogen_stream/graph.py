"""
State Type Definition (Independent of Langgraph)
"""
from typing import TypedDict, Any


class GraphState(TypedDict, total=False):
    """
    Graph State Structure (Independent of Langgraph)
    Converted to Langgraph State in the demo server
    """
    messages: list  # Message list (converted to add_messages in Langgraph)
    user_query: str
    requirement_analysis: dict[str, Any] | None
    anchor_uri: str | None
    ui_tree: dict[str, Any] | None
    error: str | None

