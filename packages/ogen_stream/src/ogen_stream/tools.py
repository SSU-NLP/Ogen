"""
UI 생성 함수 제공 (Langchain Tool과 독립적)
데모 서버에서 Langchain Tool로 래핑하여 사용
"""
from typing import Optional
from pydantic import BaseModel, Field
from .ui_generator import UIGenerationPipeline


class GenerateUIToolInput(BaseModel):
    """UI 생성 함수의 입력 스키마"""
    user_query: str = Field(description="사용자의 UI 생성 요청")
    context_mode: str = Field(default="default", description="컨텍스트 모드 (default, low-vision 등)")


def generate_ui(
    pipeline: UIGenerationPipeline,
    user_query: str,
    context_mode: str = "default"
) -> dict:
    """
    UI 생성 함수 - Langchain Tool로 래핑하여 사용
    
    Args:
        pipeline: UIGenerationPipeline 인스턴스
        user_query: 사용자의 UI 생성 요청
        context_mode: 컨텍스트 모드
    
    Returns:
        dict: UI 생성 결과
    """
    try:
        # 전체 파이프라인 실행
        requirement_analysis = pipeline.analyze_requirement(user_query)
        anchor_uri = pipeline.find_anchor(user_query, requirement_analysis)
        
        if anchor_uri:
            context = pipeline.get_context(anchor_uri)
            anchor_name = anchor_uri.split("/")[-1]
            result = pipeline.generate_with_context(
                user_query, requirement_analysis, anchor_name, context, context_mode
            )
        else:
            # 앵커를 찾지 못했지만, 요청 분석 결과가 있으면 그것을 바탕으로 UI 생성 시도
            if requirement_analysis and requirement_analysis.get("suggested_anchor"):
                suggested = requirement_analysis["suggested_anchor"]
                # suggested_anchor를 URI 형식으로 변환 시도
                for node in pipeline.engine.nodes:
                    if suggested.lower() in node["label"].lower() or node["label"].lower() in suggested.lower():
                        anchor_uri = node["uri"]
                        anchor_name = anchor_uri.split("/")[-1]
                        context = pipeline.get_context(anchor_uri)
                        result = pipeline.generate_with_context(
                            user_query, requirement_analysis, anchor_name, context, context_mode
                        )
                        break
                else:
                    # 여전히 찾지 못하면 요청 분석 결과만으로 UI 생성
                    result = pipeline.generate_from_analysis(
                        user_query, requirement_analysis, context_mode
                    )
            else:
                result = pipeline.generate_from_analysis(
                    user_query, requirement_analysis, context_mode
                )
        
        return {
            "success": True,
            "ui_tree": result.get("generated_spec"),
            "source_anchor": result.get("source_anchor"),
            "requirement_analysis": requirement_analysis
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "ui_tree": None
        }


# Langchain Tool 래퍼 (선택적, 데모 서버에서 사용)
def create_langchain_tool(pipeline: UIGenerationPipeline):
    """
    Langchain Tool 생성 함수 (선택적 의존성)
    데모 서버에서 langchain_core.tools.BaseTool을 사용하여 래핑
    
    Args:
        pipeline: UIGenerationPipeline 인스턴스
    
    Returns:
        BaseTool: Langchain Tool 인스턴스 (langchain_core가 설치된 경우)
    
    Note:
        이 함수는 데모 서버에서 사용하며, 라이브러리 자체는 Langchain 의존성이 없습니다.
    """
    try:
        from langchain_core.tools import BaseTool
        
        class GenerateUITool(BaseTool):
            """UI 생성 툴 - Agent가 필요할 때 호출"""
            
            name: str = "generate_ui"
            description: str = """
            사용자의 요청에 따라 UI 컴포넌트를 생성합니다.
            로그인 폼, 검색 바, 버튼 등의 UI 컴포넌트를 생성할 수 있습니다.
            사용자가 UI를 요청하거나 UI가 필요한 상황에서 사용하세요.
            
            예시:
            - "로그인 폼 만들어줘"
            - "검색 바를 추가해줘"
            - "버튼을 만들어줘"
            - "로그인 어떻게 해?"
            """
            args_schema: type[BaseModel] = GenerateUIToolInput
            _pipeline: UIGenerationPipeline
            
            def __init__(self, pipeline: UIGenerationPipeline, **kwargs):
                super().__init__(**kwargs)
                self._pipeline = pipeline
            
            def _run(self, user_query: str, context_mode: str = "default") -> dict:
                return generate_ui(self._pipeline, user_query, context_mode)
            
            async def _arun(self, user_query: str, context_mode: str = "default") -> dict:
                return self._run(user_query, context_mode)
        
        return GenerateUITool(pipeline=pipeline)
    except ImportError:
        raise ImportError(
            "langchain_core is required to create Langchain Tool. "
            "Install it with: pip install langchain-core"
        )
    
    def _run(self, user_query: str, context_mode: str = "default") -> dict:
        """
        UI 생성 실행
        
        Args:
            user_query: 사용자의 UI 생성 요청
            context_mode: 컨텍스트 모드
        
        Returns:
            dict: UI 생성 결과
        """
        try:
            # 전체 파이프라인 실행
            requirement_analysis = self.pipeline.analyze_requirement(user_query)
            anchor_uri = self.pipeline.find_anchor(user_query, requirement_analysis)
            
            if anchor_uri:
                context = self.pipeline.get_context(anchor_uri)
                anchor_name = anchor_uri.split("/")[-1]
                result = self.pipeline.generate_with_context(
                    user_query, requirement_analysis, anchor_name, context, context_mode
                )
            else:
                # 앵커를 찾지 못했지만, 요청 분석 결과가 있으면 그것을 바탕으로 UI 생성 시도
                if requirement_analysis and requirement_analysis.get("suggested_anchor"):
                    suggested = requirement_analysis["suggested_anchor"]
                    # suggested_anchor를 URI 형식으로 변환 시도
                    for node in self.pipeline.engine.nodes:
                        if suggested.lower() in node["label"].lower() or node["label"].lower() in suggested.lower():
                            anchor_uri = node["uri"]
                            anchor_name = anchor_uri.split("/")[-1]
                            context = self.pipeline.get_context(anchor_uri)
                            result = self.pipeline.generate_with_context(
                                user_query, requirement_analysis, anchor_name, context, context_mode
                            )
                            break
                    else:
                        # 여전히 찾지 못하면 요청 분석 결과만으로 UI 생성
                        result = self.pipeline.generate_from_analysis(
                            user_query, requirement_analysis, context_mode
                        )
                else:
                    result = self.pipeline.generate_from_analysis(
                        user_query, requirement_analysis, context_mode
                    )
            
            return {
                "success": True,
                "ui_tree": result.get("generated_spec"),
                "source_anchor": result.get("source_anchor"),
                "requirement_analysis": requirement_analysis
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "ui_tree": None
            }

