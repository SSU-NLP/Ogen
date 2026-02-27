"""
UI generation functions (independent of Langchain Tool)
Wrapped as a Langchain Tool for use in the demo server
"""

from typing import Optional
import json
from pydantic import BaseModel, Field
from .ui_generator import UIGenerationPipeline


class GenerateUIToolInput(BaseModel):
    """Input schema for UI generation function"""

    user_query: str = Field(description="User's UI generation request")
    context_mode: str = Field(
        default="default", description="Context mode (default, low-vision, etc.)"
    )


def generate_ui(
    pipeline: UIGenerationPipeline, user_query: str, context_mode: str = "default"
) -> dict:
    """
    UI generation function - wrapped as a Langchain Tool for use

    Args:
        pipeline: UIGenerationPipeline instance
        user_query: User's UI generation request
        context_mode: Context mode

    Returns:
        dict: UI generation result
    """
    try:
        # Execute the full pipeline
        requirement_analysis = pipeline.analyze_requirement(user_query)
        anchor_uri = pipeline.find_anchor(user_query, requirement_analysis)

        if not anchor_uri:
            return {
                "success": False,
                "error": "No valid anchor node was found in the knowledge graph.",
                "reason": "Closed-world synthesis requires a registry-backed KG anchor.",
                "ui_tree": None,
                "requirement_analysis": requirement_analysis,
            }

        context = pipeline.get_context(
            anchor_uri,
            user_query=user_query,
            requirement_analysis=requirement_analysis,
        )

        if not context:
            return {
                "success": False,
                "error": "No usable subgraph context was retrieved from the knowledge graph.",
                "reason": "Closed-world synthesis requires KG-backed component context.",
                "ui_tree": None,
                "source_anchor": anchor_uri,
                "requirement_analysis": requirement_analysis,
            }

        result = pipeline.generate_with_context(
            user_query, requirement_analysis, anchor_uri, context, context_mode
        )

        if result.get("error"):
            return {
                "success": False,
                "error": result["error"],
                "reason": result.get("reason"),
                "ui_tree": result.get("generated_spec"),
                "source_anchor": result.get("source_anchor"),
                "requirement_analysis": requirement_analysis,
            }

        return {
            "success": True,
            "ui_tree": result.get("generated_spec"),
            "source_anchor": result.get("source_anchor"),
            "requirement_analysis": requirement_analysis,
            "validated": result.get("validated"),
            "validation_attempts": result.get("validation_attempts"),
        }
    except Exception as e:
        return {"success": False, "error": str(e), "ui_tree": None}


# Langchain Tool wrapper (optional, used in demo server)
def create_langchain_tool(pipeline: UIGenerationPipeline):
    """
    Create a Langchain Tool (optional dependency)
    Wraps with langchain_core.tools.BaseTool for use in the demo server

    Args:
        pipeline: UIGenerationPipeline instance

    Returns:
        BaseTool: Langchain Tool instance (when langchain_core is installed)

    """
    try:
        from langchain_core.tools import BaseTool
        from langchain_core.tools.base import ArgsSchema

        class GenerateUITool(BaseTool):
            """UI generation tool - called when the Agent needs it"""

            name: str = "generate_ui"
            description: str = """
            Generate an enterprise UI JSON specification using ONLY the company's registered components
            from the knowledge graph.

            Call this tool when:
            - The user asks to create/build/show a screen or UI (forms, pages, cards, flows)
            - The user asks "how to do X" and showing the UI would help them understand or act
            - The user intent can be expressed as UI using existing components

            Do NOT call this tool when:
            - A plain text answer is sufficient and no UI would help

            Rules:
            - Never invent component types that do not exist in the knowledge graph.
            - If you cannot map the request to existing components, ask a clarifying question instead.
            - Use `context_mode` from the conversation if provided.

            Examples:
            - "로그인 폼 만들어줘"
            - "검색 바를 추가해줘"
            - "로그인 어떻게 해?" (UI helps, so call the tool)
            """
            args_schema: ArgsSchema | None = GenerateUIToolInput
            _pipeline: UIGenerationPipeline

            def __init__(self, pipeline: UIGenerationPipeline, **kwargs):
                super().__init__(**kwargs)
                self._pipeline = pipeline

            def _run(self, user_query: str, context_mode: str = "default") -> str:
                # ToolMessage content should be JSON for reliable parsing in SSE.
                return json.dumps(
                    generate_ui(self._pipeline, user_query, context_mode),
                    ensure_ascii=False,
                )

            async def _arun(
                self, user_query: str, context_mode: str = "default"
            ) -> str:
                return self._run(user_query, context_mode)

        return GenerateUITool(pipeline=pipeline)
    except ImportError:
        raise ImportError(
            "langchain_core is required to create Langchain Tool. "
            "Install it with: pip install langchain-core"
        )
