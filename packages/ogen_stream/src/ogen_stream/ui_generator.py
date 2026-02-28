"""
UI Generation Pipeline Abstraction
"""

from typing import AsyncIterator
from .engine import OgenEngine
from .stream import StreamEvent, StreamEventType


class UIGenerationPipeline:
    """
    Class that manages the entire UI generation pipeline.
    Each stage can be executed independently and encapsulates per-step results.
    """

    def __init__(self, engine: OgenEngine):
        """
        Args:
            engine: OgenEngine instance
        """
        self.engine = engine

    def analyze_requirement(self, user_query: str) -> dict:
        """
        Requirement analysis step.

        Args:
            user_query: User request string

        Returns:
            dict: Requirement analysis result
        """
        return self.engine.analyze_requirement(user_query)

    def find_anchor(
        self, user_query: str, requirement_analysis: dict | None = None
    ) -> str | None:
        """
        Anchor node discovery step.

        Args:
            user_query: User request string
            requirement_analysis: Requirement analysis result (optional)

        Returns:
            str | None: Anchor node URI or None
        """
        return self.engine.find_anchor_node_with_llm(user_query, requirement_analysis)

    def get_context(
        self,
        anchor_uri: str,
        user_query: str = "",
        requirement_analysis: dict | None = None,
    ) -> list:
        """
        Graph context retrieval step.

        Args:
            anchor_uri: Anchor node URI

        Returns:
            list: List of sub-component information
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
    ) -> dict:
        """
        Generate UI with Context

        Args:
            user_query: User request string
            requirement_analysis: Requirement analysis result
            anchor_name: Anchor node name
            context: Graph context (sub-component information)

        Returns:
            dict: UI generation result
        """
        return self.engine._generate_ui_with_context(
            user_query, requirement_analysis, anchor_name, context
        )



    async def generate_ui_stream(
        self, user_query: str
    ) -> AsyncIterator[StreamEvent]:
        """
        Generate UI with Context

        Args:
            user_query: user request

        Yields:
            StreamEvent: each step event
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
            user_query, requirement_analysis, anchor_uri, context
        )

        if result.get("error"):
            yield StreamEvent(
                type=StreamEventType.ERROR,
                error=result["error"],
            )
            return

        yield StreamEvent(type=StreamEventType.UI, uiTree=result.get("generated_spec"))
        yield StreamEvent(type=StreamEventType.DONE)


# Standalone functions (optional usage)
def analyze_user_requirement(engine: OgenEngine, user_query: str) -> dict:
    """
    Requirement analysis function.

    Args:
        engine: OgenEngine instance
        user_query: User request string

    Returns:
        dict: Requirement analysis result
    """
    return engine.analyze_requirement(user_query)


def find_ui_anchor(
    engine: OgenEngine, user_query: str, requirement_analysis: dict | None = None
) -> str | None:
    """
    Anchor node discovery function.

    Args:
        engine: OgenEngine instance
        user_query: User request string
        requirement_analysis: Requirement analysis result (optional)

    Returns:
        str | None: Anchor node URI or None
    """
    return engine.find_anchor_node_with_llm(user_query, requirement_analysis)


def generate_ui_spec(
    engine: OgenEngine,
    user_query: str,
    requirement_analysis: dict | None = None,
    anchor_uri: str | None = None,
) -> dict:
    """
    UI spec generation function (runs the full pipeline at once).

    Args:
        engine: OgenEngine instance
        user_query: User request string
        requirement_analysis: Requirement analysis result (optional; auto-analyzed if omitted)
        anchor_uri: Anchor node URI (optional; auto-discovered if omitted)

    Returns:
        dict: UI generation result
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
        user_query, requirement_analysis, anchor_uri, context
    )
