"""
Event Stream Type Definition and Processing Functions
"""
from typing import TypedDict, Literal, AsyncIterator
from enum import Enum
import json


class StreamEventType(str, Enum):
    """Stream event types"""
    TEXT = "text"
    UI = "ui"
    ERROR = "error"
    DONE = "done"


class StreamEvent(TypedDict, total=False):
    """Stream event structure"""    
    type: StreamEventType
    content: str | None
    uiTree: dict | None
    error: str | None


def format_sse_event(event: StreamEvent) -> str:
    """
    Convert stream event to SSE format
    
    Args:
        event: StreamEvent dictionary
    
    Returns:
        str: SSE format string ("data: {...}\n\n")
    """
    # Enum을 문자열로 변환
    event_dict = {
        "type": event["type"].value if isinstance(event["type"], StreamEventType) else event["type"],
        "content": event.get("content"),
        "uiTree": event.get("uiTree"),
        "error": event.get("error")
    }
    # None 값 제거
    event_dict = {k: v for k, v in event_dict.items() if v is not None}
    data = json.dumps(event_dict, ensure_ascii=False)
    return f"data: {data}\n\n"


def parse_sse_data(data: str) -> StreamEvent | None:
    """
    Parse SSE data into StreamEvent
    
    Args:
        data: SSE "data: {...}" format string
    
    Returns:
        StreamEvent | None: Parsed event or None
    """
    try:
        if data.startswith("data: "):
            json_str = data[6:]  # "data: " 제거
            event_dict = json.loads(json_str)
            return StreamEvent(**event_dict)
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"Failed to parse SSE data: {e}")
        return None
    return None

