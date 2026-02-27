"""
UI 생성 과정 추상화
"""

from typing import AsyncIterator
from .engine import OgenEngine
from .stream import StreamEvent, StreamEventType


class UIGenerationPipeline:
    """
    UI 생성의 전체 파이프라인을 관리하는 클래스
    각 단계를 독립적으로 실행 가능하며, 단계별 결과를 캡슐화
    """

    def __init__(self, engine: OgenEngine):
        """
        Args:
            engine: OgenEngine 인스턴스
        """
        self.engine = engine

    def analyze_requirement(self, user_query: str) -> dict:
        """
        요청 분석 단계

        Args:
            user_query: 사용자 요청 문자열

        Returns:
            dict: 요청 분석 결과
        """
        return self.engine.analyze_requirement(user_query)

    def find_anchor(
        self, user_query: str, requirement_analysis: dict | None = None
    ) -> str | None:
        """
        앵커 노드 찾기 단계

        Args:
            user_query: 사용자 요청 문자열
            requirement_analysis: 요청 분석 결과 (선택적)

        Returns:
            str | None: 앵커 노드 URI 또는 None
        """
        return self.engine.find_anchor_node_with_llm(user_query, requirement_analysis)

    def get_context(
        self,
        anchor_uri: str,
        user_query: str = "",
        requirement_analysis: dict | None = None,
    ) -> list:
        """
        Graph Context 검색 단계

        Args:
            anchor_uri: 앵커 노드 URI

        Returns:
            list: 하위 컴포넌트 정보 리스트
        """
        return self.engine.get_subgraph_context(
            anchor_uri,
            user_query=user_query,
            requirement_analysis=requirement_analysis,
        )

    def generate_with_context(
        self,
        user_query: str,
        requirement_analysis: dict,
        anchor_name: str,
        context: list,
        context_mode: str = "default",
    ) -> dict:
        """
        Context를 활용한 UI 생성

        Args:
            user_query: 사용자 요청 문자열
            requirement_analysis: 요청 분석 결과
            anchor_name: 앵커 노드 이름
            context: Graph Context (하위 컴포넌트 정보)
            context_mode: 컨텍스트 모드 (default, low-vision 등)

        Returns:
            dict: UI 생성 결과
        """
        return self.engine._generate_ui_with_context(
            user_query, requirement_analysis, anchor_name, context, context_mode
        )



    async def generate_ui_stream(
        self, user_query: str, context_mode: str = "default"
    ) -> AsyncIterator[StreamEvent]:
        """
        UI 생성 과정을 스트리밍으로 제공

        Args:
            user_query: 사용자 요청 문자열
            context_mode: 컨텍스트 모드

        Yields:
            StreamEvent: 각 단계별 이벤트
        """
        # Step 1: Analyze requirement
        yield StreamEvent(
            type=StreamEventType.TEXT, content="Analyzing request..."
        )
        requirement_analysis = self.analyze_requirement(user_query)

        # Step 2: Find anchor
        yield StreamEvent(
            type=StreamEventType.TEXT, content="Searching for matching component..."
        )
        anchor_uri = self.find_anchor(user_query, requirement_analysis)

        if not anchor_uri:
            yield StreamEvent(
                type=StreamEventType.ERROR,
                error="No valid anchor node was found in the knowledge graph.",
            )
            return

        # Step 3: Retrieve Graph Context
        yield StreamEvent(
            type=StreamEventType.TEXT,
            content=f"Retrieving component info for {anchor_uri}...",
        )
        context = self.get_context(
            anchor_uri,
            user_query=user_query,
            requirement_analysis=requirement_analysis,
        )

        if not context:
            yield StreamEvent(
                type=StreamEventType.ERROR,
                error="No usable subgraph context was retrieved from the knowledge graph.",
            )
            return

        # Step 4: Generate UI
        yield StreamEvent(
            type=StreamEventType.TEXT, content="Generating UI..."
        )
        result = self.generate_with_context(
            user_query, requirement_analysis, anchor_uri, context, context_mode
        )

        if result.get("error"):
            yield StreamEvent(
                type=StreamEventType.ERROR,
                error=result["error"],
            )
            return

        yield StreamEvent(type=StreamEventType.UI, uiTree=result.get("generated_spec"))
        yield StreamEvent(type=StreamEventType.DONE)


# 독립 함수들 (선택적 사용)
def analyze_user_requirement(engine: OgenEngine, user_query: str) -> dict:
    """
    요청 분석 함수

    Args:
        engine: OgenEngine 인스턴스
        user_query: 사용자 요청 문자열

    Returns:
        dict: 요청 분석 결과
    """
    return engine.analyze_requirement(user_query)


def find_ui_anchor(
    engine: OgenEngine, user_query: str, requirement_analysis: dict | None = None
) -> str | None:
    """
    앵커 노드 찾기 함수

    Args:
        engine: OgenEngine 인스턴스
        user_query: 사용자 요청 문자열
        requirement_analysis: 요청 분석 결과 (선택적)

    Returns:
        str | None: 앵커 노드 URI 또는 None
    """
    return engine.find_anchor_node_with_llm(user_query, requirement_analysis)


def generate_ui_spec(
    engine: OgenEngine,
    user_query: str,
    requirement_analysis: dict | None = None,
    anchor_uri: str | None = None,
    context_mode: str = "default",
) -> dict:
    """
    UI 스펙 생성 함수 (전체 과정을 한 번에)

    Args:
        engine: OgenEngine 인스턴스
        user_query: 사용자 요청 문자열
        requirement_analysis: 요청 분석 결과 (선택적, 없으면 자동 분석)
        anchor_uri: 앵커 노드 URI (선택적, 없으면 자동 검색)
        context_mode: 컨텍스트 모드

    Returns:
        dict: UI 생성 결과
    """
    pipeline = UIGenerationPipeline(engine)

    # Analyze requirement if not provided
    if requirement_analysis is None:
        requirement_analysis = pipeline.analyze_requirement(user_query)

    # Find anchor URI if not provided
    if anchor_uri is None:
        anchor_uri = pipeline.find_anchor(user_query, requirement_analysis)

    if not anchor_uri:
        return {
            "error": "No valid anchor node was found in the knowledge graph.",
            "reason": "Closed-world synthesis requires a registry-backed KG anchor.",
            "requirement_analysis": requirement_analysis,
        }

    context = pipeline.get_context(
        anchor_uri,
        user_query=user_query,
        requirement_analysis=requirement_analysis,
    )

    return pipeline.generate_with_context(
        user_query, requirement_analysis, anchor_uri, context, context_mode
    )
