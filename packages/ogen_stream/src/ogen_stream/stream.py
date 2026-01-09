"""
이벤트 스트림 타입 정의 및 처리 함수
"""
from typing import TypedDict, Literal, AsyncIterator
from enum import Enum
import json


class StreamEventType(str, Enum):
    """스트림 이벤트 타입"""
    TEXT = "text"
    UI = "ui"
    ERROR = "error"
    DONE = "done"


class StreamEvent(TypedDict, total=False):
    """스트림 이벤트 구조"""
    type: StreamEventType
    content: str | None
    uiTree: dict | None
    error: str | None


def format_sse_event(event: StreamEvent) -> str:
    """
    스트림 이벤트를 SSE 형식으로 변환
    
    Args:
        event: StreamEvent 딕셔너리
    
    Returns:
        str: SSE 형식 문자열 ("data: {...}\n\n")
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
    SSE 데이터를 StreamEvent로 파싱
    
    Args:
        data: SSE "data: {...}" 형식의 문자열
    
    Returns:
        StreamEvent | None: 파싱된 이벤트 또는 None
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

