"""
State 타입 정의 (Langgraph와 독립적)
"""
from typing import TypedDict, Any


class GraphState(TypedDict, total=False):
    """
    Graph State 구조 (Langgraph와 독립적)
    데모 서버에서 Langgraph State로 변환하여 사용
    """
    messages: list  # 메시지 리스트 (Langgraph에서 add_messages로 변환)
    user_query: str
    requirement_analysis: dict[str, Any] | None
    anchor_uri: str | None
    ui_tree: dict[str, Any] | None
    error: str | None

