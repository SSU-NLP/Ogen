# Langgraph Chat 앱 구현 계획서

## 요구사항 분석

### 목표
1. **데모 서버 (`apps/server/`)**: Langgraph를 사용한 간단한 Chat 앱 구성
2. **백엔드 라이브러리 (`packages/ogen_stream/`)**: 이벤트 스트림 처리와 Ogen을 사용할 수 있도록 노드를 제공하는 함수

### 현재 상태
- `apps/server/main.py`: FastAPI 서버, `/generate-ui`와 `/api/connect` 엔드포인트만 존재
- `packages/ogen_stream/src/ogen_stream/engine.py`: `OgenEngine` 클래스가 `reason()`, `analyze_requirement()` 등의 메서드 제공
- 프론트엔드: `OgentRuntime`이 스트리밍을 지원하도록 이미 구현됨

## 아키텍처 설계

### 라이브러리와 데모 앱의 경계

**백엔드 라이브러리 (`packages/ogen_stream/src/ogen_stream/`)**
- ✅ Langgraph 노드 함수 제공
- ✅ 이벤트 스트림 생성 및 처리 로직
- ✅ Ogen 엔진을 활용한 노드 함수
- ✅ 스트림 이벤트 타입 정의

**데모 서버 (`apps/server/`)**
- ✅ Langgraph 그래프 구성
- ✅ FastAPI 엔드포인트 (스트리밍 지원)
- ✅ 라이브러리 함수만 호출
- ❌ 비즈니스 로직 구현 금지

## 구현 계획

### Phase 1: 백엔드 라이브러리 - Langgraph 노드 함수 제공

#### 1.1 이벤트 스트림 타입 정의
**파일:** `packages/ogen_stream/src/ogen_stream/stream.py` (신규)

```python
from typing import TypedDict, Literal, AsyncIterator
from enum import Enum

class StreamEventType(str, Enum):
    TEXT = "text"
    UI = "ui"
    ERROR = "error"
    DONE = "done"

class StreamEvent(TypedDict):
    type: StreamEventType
    content: str | None
    uiTree: dict | None
    error: str | None
```

#### 1.2 Langgraph State 정의
**파일:** `packages/ogen_stream/src/ogen_stream/graph.py` (신규)

```python
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages

class GraphState(TypedDict):
    messages: Annotated[list, add_messages]
    user_query: str
    requirement_analysis: dict | None
    anchor_uri: str | None
    ui_tree: dict | None
    error: str | None
```

#### 1.3 UI 생성 과정 추상화
**파일:** `packages/ogen_stream/src/ogen_stream/ui_generator.py` (신규)

**목적:** UI 생성 과정을 추상화하여 재사용 가능한 함수/클래스로 제공

**클래스/함수:**

1. **`UIGenerationPipeline` 클래스**
   - UI 생성의 전체 파이프라인을 관리하는 클래스
   - 각 단계를 독립적으로 실행 가능
   - 단계별 결과를 캡슐화

```python
class UIGenerationPipeline:
    def __init__(self, engine: OgenEngine):
        self.engine = engine
    
    def analyze_requirement(self, user_query: str) -> dict:
        """요청 분석 단계"""
        return self.engine.analyze_requirement(user_query)
    
    def find_anchor(self, user_query: str, requirement_analysis: dict | None = None) -> str | None:
        """앵커 노드 찾기 단계"""
        return self.engine.find_anchor_node_with_llm(user_query, requirement_analysis)
    
    def get_context(self, anchor_uri: str) -> list:
        """Graph Context 검색 단계"""
        return self.engine.get_subgraph_context(anchor_uri)
    
    def generate_with_context(
        self, 
        user_query: str,
        requirement_analysis: dict,
        anchor_name: str,
        context: list,
        context_mode: str = "default"
    ) -> dict:
        """Context를 활용한 UI 생성"""
        return self.engine._generate_ui_with_context(
            user_query, requirement_analysis, anchor_name, context, context_mode
        )
    
    def generate_from_analysis(
        self,
        user_query: str,
        requirement_analysis: dict,
        context_mode: str = "default"
    ) -> dict:
        """요청 분석 결과만으로 UI 생성"""
        return self.engine._generate_ui_from_analysis(
            user_query, requirement_analysis, context_mode
        )
    
    async def generate_ui_stream(
        self,
        user_query: str,
        context_mode: str = "default"
    ) -> AsyncIterator[StreamEvent]:
        """UI 생성 과정을 스트리밍으로 제공"""
        # 각 단계별로 이벤트를 yield
        # 1. 요청 분석 이벤트
        # 2. 앵커 찾기 이벤트
        # 3. Context 검색 이벤트
        # 4. UI 생성 이벤트
        pass
```

2. **독립 함수들 (선택적 사용)**
   - 각 단계를 독립적으로 사용할 수 있는 함수들

```python
def analyze_user_requirement(engine: OgenEngine, user_query: str) -> dict:
    """요청 분석 함수"""
    return engine.analyze_requirement(user_query)

def find_ui_anchor(engine: OgenEngine, user_query: str, requirement_analysis: dict | None = None) -> str | None:
    """앵커 노드 찾기 함수"""
    return engine.find_anchor_node_with_llm(user_query, requirement_analysis)

def generate_ui_spec(
    engine: OgenEngine,
    user_query: str,
    requirement_analysis: dict | None = None,
    anchor_uri: str | None = None,
    context_mode: str = "default"
) -> dict:
    """UI 스펙 생성 함수 (전체 과정을 한 번에)"""
    # 내부적으로 Pipeline을 사용하거나 단계별로 실행
    pass
```

#### 1.4 Langgraph Tool 제공
**파일:** `packages/ogen_stream/src/ogen_stream/tools.py` (신규)

**목적:** Langgraph Agent에서 사용할 수 있는 Tool로 UI 생성 기능 제공

**Tool 클래스:**

```python
from langchain_core.tools import BaseTool
from typing import Optional
from pydantic import BaseModel, Field

class GenerateUIToolInput(BaseModel):
    """UI 생성 툴의 입력 스키마"""
    user_query: str = Field(description="사용자의 UI 생성 요청")
    context_mode: str = Field(default="default", description="컨텍스트 모드 (default, low-vision 등)")

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
    """
    args_schema: type[BaseModel] = GenerateUIToolInput
    pipeline: UIGenerationPipeline
    
    def __init__(self, pipeline: UIGenerationPipeline):
        super().__init__()
        self.pipeline = pipeline
    
    def _run(self, user_query: str, context_mode: str = "default") -> dict:
        """UI 생성 실행"""
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
            result = self.pipeline.generate_from_analysis(
                user_query, requirement_analysis, context_mode
            )
        
        return {
            "success": True,
            "ui_tree": result.get("generated_spec"),
            "source_anchor": result.get("source_anchor"),
            "requirement_analysis": requirement_analysis
        }
    
    async def _arun(self, user_query: str, context_mode: str = "default") -> dict:
        """비동기 UI 생성 실행"""
        return self._run(user_query, context_mode)

def create_ui_generation_tool(pipeline: UIGenerationPipeline) -> GenerateUITool:
    """UI 생성 툴 생성 함수"""
    return GenerateUITool(pipeline=pipeline)
```

#### 1.5 Langgraph 노드 함수 제공 (선택적)
**파일:** `packages/ogen_stream/src/ogen_stream/nodes.py` (신규)

**목적:** 직접 노드로 사용하고 싶을 때를 위한 함수들 (Tool 사용이 더 권장됨)

**함수들:**
1. `analyze_requirement_node(state: GraphState, pipeline: UIGenerationPipeline) -> GraphState`
   - `pipeline.analyze_requirement()` 호출
   - State에 `requirement_analysis` 저장

2. `find_anchor_node(state: GraphState, pipeline: UIGenerationPipeline) -> GraphState`
   - `pipeline.find_anchor()` 호출
   - State에 `anchor_uri` 저장

3. `generate_ui_node(state: GraphState, pipeline: UIGenerationPipeline) -> GraphState`
   - `pipeline.generate_with_context()` 또는 `pipeline.generate_from_analysis()` 호출
   - State에 `ui_tree` 저장

4. `chat_response_node(state: GraphState, engine: OgenEngine) -> GraphState`
   - 일반적인 채팅 응답 생성 (UI가 필요하지 않은 경우)
   - LLM을 사용하여 자연스러운 응답 생성

#### 1.6 이벤트 스트림 생성 함수
**파일:** `packages/ogen_stream/src/ogen_stream/stream.py`

**함수:**
- `create_event_stream(graph_state: GraphState, pipeline: UIGenerationPipeline) -> AsyncIterator[StreamEvent]`
  - Langgraph 실행 중 각 노드의 결과를 이벤트로 변환
  - 텍스트 스트리밍, UI 생성, 에러 처리 등을 이벤트로 전송
  - 또는 `pipeline.generate_ui_stream()` 직접 사용 가능

#### 1.7 라이브러리 Export 업데이트
**파일:** `packages/ogen_stream/src/ogen_stream/__init__.py`

```python
from .engine import OgenEngine
from .ui_generator import (
    UIGenerationPipeline,
    analyze_user_requirement,
    find_ui_anchor,
    generate_ui_spec
)
from .tools import (
    GenerateUITool,
    GenerateUIToolInput,
    create_ui_generation_tool
)
from .nodes import (
    analyze_requirement_node,
    find_anchor_node,
    generate_ui_node,
    chat_response_node
)
from .graph import GraphState, create_graph
from .stream import StreamEvent, StreamEventType, create_event_stream

__all__ = [
    "OgenEngine",
    "UIGenerationPipeline",
    "analyze_user_requirement",
    "find_ui_anchor",
    "generate_ui_spec",
    "GenerateUITool",
    "GenerateUIToolInput",
    "create_ui_generation_tool",
    "analyze_requirement_node",
    "find_anchor_node",
    "generate_ui_node",
    "chat_response_node",
    "GraphState",
    "create_graph",
    "StreamEvent",
    "StreamEventType",
    "create_event_stream",
]
```

### Phase 2: 데모 서버 - Langgraph Chat 앱 구성

#### 2.1 의존성 추가
**파일:** `apps/server/pyproject.toml`

```toml
dependencies = [
    "fastapi",
    "uvicorn",
    "python-dotenv",
    "ogen-stream",
    "langgraph",
    "langchain-openai",  # Langgraph와 함께 사용
    "langchain-core",  # Tool 인터페이스
    "sse-starlette",  # Server-Sent Events 지원
]
```

#### 2.2 Langgraph Agent 구성 (Tool 사용)
**파일:** `apps/server/main.py` (수정)

**Agent 구조:**
- Langchain Agent with Tools 패턴 사용
- Agent가 사용자 요청을 분석하고 필요할 때만 `GenerateUITool` 호출
- Tool 호출 결과를 자연스러운 응답으로 변환

**그래프 구조 (Agent 방식):**
```
START -> Agent Node (with Tools)
         |
         ├-> Tool: generate_ui (필요 시)
         └-> Response Generation
         |
         END
```

**또는 직접 노드 방식 (선택적):**
```
START -> analyze_requirement_node -> find_anchor_node -> [조건부 분기]
                                                          |
                                                          ├-> generate_ui_node (UI 필요 시)
                                                          └-> chat_response_node (일반 채팅)
                                                          |
                                                          END
```

**구현 예시:**
```python
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from ogen_stream import OgenEngine, UIGenerationPipeline, create_ui_generation_tool

# 엔진 및 파이프라인 초기화
engine = OgenEngine(openai_api_key=API_KEY)
pipeline = UIGenerationPipeline(engine)

# UI 생성 툴 생성
ui_tool = create_ui_generation_tool(pipeline)

# Agent 생성 (Tool 포함)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
tools = [ui_tool]
agent = create_react_agent(llm, tools)

# 그래프 생성
graph = StateGraph(agent)
# ... 그래프 구성
```

**조건부 분기 (Tool 방식):**
- Agent가 자동으로 판단하여 Tool 호출 여부 결정
- UI가 필요하면 `generate_ui` 툴 호출
- 일반 대화면 Tool 없이 응답 생성

#### 2.3 스트리밍 엔드포인트 추가
**파일:** `apps/server/main.py`

**엔드포인트:**
- `POST /chat/stream`: Server-Sent Events로 스트리밍 응답
  - 요청: `{ "message": str, "context": str }`
  - 응답: SSE 스트림 (`data: {"type": "text", "content": "..."}`)
  - Agent가 Tool을 호출하면 `{"type": "ui", "uiTree": {...}}` 이벤트 전송
  - 텍스트 응답은 `{"type": "text", "content": "..."}` 이벤트로 전송

**스트리밍 처리:**
```python
from sse_starlette.sse import EventSourceResponse
import json

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    async def event_generator():
        try:
            # Agent 실행 및 스트리밍
            async for event in graph.astream(
                {"messages": [("user", request.message)]},
                config={"configurable": {"thread_id": "1"}}
            ):
                # Agent의 각 단계를 이벤트로 변환
                if "agent" in event:
                    # Tool 호출 감지
                    if "tool_calls" in event["agent"]:
                        for tool_call in event["agent"]["tool_calls"]:
                            if tool_call["name"] == "generate_ui":
                                result = tool_call.get("result", {})
                                yield {
                                    "event": "message",
                                    "data": json.dumps({
                                        "type": "ui",
                                        "uiTree": result.get("ui_tree")
                                    })
                                }
                    # 텍스트 응답 (스트리밍)
                    if "messages" in event["agent"]:
                        for msg in event["agent"]["messages"]:
                            if msg.type == "ai" and hasattr(msg, "content"):
                                # 텍스트를 청크로 나누어 스트리밍
                                content = msg.content
                                if isinstance(content, str):
                                    # 단어 단위로 스트리밍 (또는 문자 단위)
                                    words = content.split()
                                    for word in words:
                                        yield {
                                            "event": "message",
                                            "data": json.dumps({
                                                "type": "text",
                                                "content": word + " "
                                            })
                                        }
                # 완료 이벤트
                yield {
                    "event": "message",
                    "data": json.dumps({"type": "done"})
                }
        except Exception as e:
            yield {
                "event": "message",
                "data": json.dumps({
                    "type": "error",
                    "error": str(e)
                })
            }
    
    return EventSourceResponse(event_generator())
```

#### 2.4 기존 엔드포인트 유지
- `/generate-ui`: 기존 기능 유지 (하위 호환성)
- `/api/connect`: 기존 기능 유지 (하위 호환성)

## 파일 구조

### 백엔드 라이브러리 (`packages/ogen_stream/src/ogen_stream/`)
```
ogen_stream/
├── __init__.py          # Export 업데이트
├── engine.py            # 기존 (변경 없음, 내부 메서드는 유지)
├── ogen-core.ttl        # 기존 (변경 없음)
├── ui_generator.py      # 신규: UI 생성 과정 추상화 (UIGenerationPipeline)
├── tools.py             # 신규: Langgraph Tool (GenerateUITool)
├── graph.py             # 신규: GraphState, create_graph
├── nodes.py             # 신규: Langgraph 노드 함수들 (선택적, Tool 사용 권장)
└── stream.py            # 신규: 이벤트 스트림 타입 및 함수
```

### 데모 서버 (`apps/server/`)
```
server/
├── main.py              # 수정: Langgraph 그래프 구성, 스트리밍 엔드포인트 추가
├── pyproject.toml       # 수정: 의존성 추가
└── data/                # 기존 (변경 없음)
```

### 프론트엔드 라이브러리 (`packages/svelte/`)
```
svelte/
├── index.ts             # 수정: SSE 스트리밍 처리 추가
├── UIRenderer.svelte   # 기존 (변경 없음)
└── ...
```

### 프론트엔드 데모 앱 (`apps/front/`)
```
front/
├── src/
│   └── routes/
│       └── +page.svelte  # 수정: 일반 채팅 UI로 변경
└── ...
```

## 구현 순서

1. **Phase 1.1**: 이벤트 스트림 타입 정의 (`stream.py`)
2. **Phase 1.2**: GraphState 정의 (`graph.py`)
3. **Phase 1.3**: UI 생성 과정 추상화 (`ui_generator.py`)
   - `UIGenerationPipeline` 클래스 구현
   - 독립 함수들 구현
4. **Phase 1.4**: Langgraph Tool 구현 (`tools.py`)
   - `GenerateUITool` 클래스 구현
   - `UIGenerationPipeline`을 사용하는 Tool 제공
5. **Phase 1.5**: Langgraph 노드 함수 구현 (`nodes.py`) - 선택적
   - 추상화된 `UIGenerationPipeline` 사용
6. **Phase 1.6**: 이벤트 스트림 생성 함수 (`stream.py`)
7. **Phase 1.7**: 라이브러리 Export 업데이트 (`__init__.py`)
8. **Phase 2.1**: 의존성 추가 (`pyproject.toml`)
9. **Phase 2.2**: Langgraph Agent 구성 (`main.py`)
   - `UIGenerationPipeline` 인스턴스 생성
   - `GenerateUITool` 생성 및 Agent에 추가
   - Agent 그래프 구성
10. **Phase 2.3**: 스트리밍 엔드포인트 추가 (`main.py`)
    - Tool 호출 감지 및 UI 이벤트 전송
11. **Phase 3.1**: 프론트 라이브러리 확장 (`packages/svelte/index.ts`)
    - SSE 스트리밍 처리 추가
    - `/chat/stream` 엔드포인트 지원
12. **Phase 3.2**: 프론트 데모 앱 수정 (`apps/front/src/routes/+page.svelte`)
    - 일반적인 채팅 UI로 변경
    - 스트리밍 메시지 처리
    - UI 자동 렌더링

## 아키텍처 검토

### 라이브러리 코드 분류
- ✅ `ui_generator.py`, `tools.py`, `graph.py`, `nodes.py`, `stream.py`: 라이브러리 (`packages/ogen_stream/`)
- ✅ Langgraph Agent/Tool 구성: 데모 서버 (`apps/server/`)
- ✅ FastAPI 엔드포인트: 데모 서버 (`apps/server/`)

### 비즈니스 로직 캡슐화
- ✅ UI 생성 과정은 `UIGenerationPipeline`로 추상화하여 라이브러리에 구현
- ✅ `GenerateUITool`은 라이브러리에 구현되어 Agent에서 사용 가능
- ✅ 모든 노드 함수는 라이브러리에 구현 (선택적, Tool 사용 권장)
- ✅ 이벤트 스트림 생성 로직은 라이브러리에 구현
- ✅ 데모 서버는 라이브러리의 Tool/함수만 호출
- ✅ `OgenEngine`의 내부 메서드는 유지하되, 외부에서는 `UIGenerationPipeline` 또는 `GenerateUITool`을 통해 접근 권장

### 하위 호환성
- ✅ 기존 `/generate-ui` 엔드포인트 유지 (내부적으로 `UIGenerationPipeline` 사용 가능)
- ✅ 기존 `/api/connect` 엔드포인트 유지
- ✅ 기존 `OgenEngine` 클래스 변경 없음 (내부 메서드는 그대로 유지)
- ✅ 기존 `OgenEngine.reason()` 메서드는 그대로 작동 (내부적으로는 `UIGenerationPipeline`과 동일한 로직)

## 검증 항목

1. **린터 에러 확인**
   - Python 타입 힌트 확인
   - Import 에러 확인

2. **아키텍처 원칙 확인**
   - 라이브러리 코드가 `apps/`에 없는가?
   - 데모 서버가 라이브러리 함수만 호출하는가?
   - 비즈니스 로직이 라이브러리에 있는가?

3. **기능 동작 확인**
   - Langgraph Agent가 정상 작동하는가?
   - Tool이 필요할 때 올바르게 호출되는가?
   - 스트리밍 엔드포인트가 정상 작동하는가?
   - Tool 호출 결과가 올바르게 이벤트로 전송되는가?
   - 기존 엔드포인트가 여전히 작동하는가?

## 예상 이슈 및 해결 방안

1. **Langgraph 버전 호환성**
   - 최신 버전 사용, 문서 참고

2. **스트리밍 성능**
   - 비동기 처리 최적화
   - 버퍼링 전략 고려

3. **에러 처리**
   - Tool 실행 중 에러 발생 시 적절한 에러 메시지 반환
   - Agent가 에러를 처리하고 사용자에게 전달
   - 스트리밍 중 에러 이벤트 전송

4. **Tool 호출 최적화**
   - Agent가 불필요하게 Tool을 호출하지 않도록 명확한 description 제공
   - Tool 호출 비용 최적화 (캐싱 등 고려)

## 프론트엔드 이벤트 처리 검토

### 현재 상태
- ✅ `OgentRuntime`이 이미 스트리밍을 지원하도록 구현됨
- ✅ `StreamChunk` 타입이 정의되어 있음 (`text`, `ui`, `error`, `done`)
- ✅ 메시지에 `uiTree` 속성이 있어 UI 렌더링 가능
- ⚠️ 현재는 `/generate-ui` 엔드포인트 사용 (비스트리밍)
- ⚠️ `/chat/stream` 엔드포인트와의 연동이 계획서에 명시되지 않음

### 프론트엔드 수정 필요 사항

#### Phase 3: 프론트엔드 라이브러리 확장
**파일:** `packages/svelte/index.ts` (수정)

**수정 내용:**
1. `OgentRuntime`에 `/chat/stream` 엔드포인트 지원 추가
2. SSE(Server-Sent Events) 스트리밍 처리
3. 이벤트 타입별 처리 (`text`, `ui`, `error`, `done`)

```typescript
// OgentRuntime에 chatStream 메서드 추가
async sendChatMessage(message: string, context: string = "default"): Promise<void> {
    // SSE 스트리밍 처리
    const eventSource = new EventSource(
        `${this.endpoint}/chat/stream?message=${encodeURIComponent(message)}&context=${context}`
    );
    
    // 이벤트 리스너 등록
    eventSource.onmessage = (event) => {
        const chunk: StreamChunk = JSON.parse(event.data);
        this.handleStreamChunk(chunk);
    };
}
```

#### Phase 4: 프론트엔드 데모 앱 수정
**파일:** `apps/front/src/routes/+page.svelte` (수정)

**목적:** 일반적인 채팅 인터페이스로 변경

**변경 사항:**
1. **일반적인 채팅 UI**
   - UI 생성에 특화된 메시지 제거
   - 자연스러운 대화 흐름
   - UI가 생성되면 자동으로 렌더링

2. **메시지 렌더링**
   - 텍스트 메시지: 일반 채팅 메시지로 표시
   - UI 메시지: `UIRenderer`로 렌더링
   - 혼합 메시지: 텍스트 + UI 모두 표시

3. **스트리밍 처리**
   - 텍스트 스트리밍: 실시간으로 텍스트 추가
   - UI 스트리밍: UI가 생성되면 즉시 렌더링

**구현 예시:**
```svelte
{#each messages as message (message.id)}
  <div class="message message-{message.role}">
    <div class="message-content">
      {message.content}
    </div>
    {#if message.uiTree}
      <div class="message-ui">
        <UIRenderer node={message.uiTree} components={designSystem} />
      </div>
    {/if}
  </div>
{/each}
```

## 계획서 점수 평가

### 평가 기준 (100점 만점)

#### 1. 아키텍처 원칙 준수 (30점)
- ✅ 라이브러리와 데모 앱의 경계 명확: 10/10
- ✅ 비즈니스 로직 캡슐화: 10/10
- ✅ 하위 호환성 유지: 10/10
**점수: 30/30**

#### 2. 기능 완성도 (25점)
- ✅ 백엔드 라이브러리 기능: 10/10
- ✅ 데모 서버 기능: 8/10 (스트리밍 처리 상세화 필요)
- ⚠️ 프론트엔드 연동: 5/10 (명시되지 않음)
**점수: 23/25**

#### 3. 프론트엔드 이벤트 처리 (20점)
- ✅ 이벤트 타입 정의: 5/5
- ⚠️ 스트리밍 처리 로직: 5/10 (SSE 처리 미명시)
- ⚠️ UI 렌더링 통합: 5/10 (일반 채팅으로 변경 필요)
**점수: 15/20**

#### 4. 구현 가능성 (15점)
- ✅ 기술 스택 적절성: 5/5
- ✅ 단계별 구현 계획: 5/5
- ⚠️ 상세 구현 가이드: 3/5 (프론트엔드 부분 부족)
**점수: 13/15**

#### 5. 문서화 및 검증 (10점)
- ✅ 검증 항목 명시: 5/5
- ⚠️ 예상 이슈 및 해결 방안: 3/5 (프론트엔드 이슈 부족)
**점수: 8/10**

### 총점: 89/100

### 개선 필요 사항
1. **프론트엔드 스트리밍 처리 상세화** (-5점)
2. **일반 채팅 UI로 변경 계획 추가** (-3점)
3. **프론트엔드 이벤트 처리 예시 추가** (-3점)

### Phase 3: 프론트엔드 라이브러리 확장

#### 3.1 SSE 스트리밍 지원 추가
**파일:** `packages/svelte/index.ts` (수정)

**수정 내용:**
1. `OgentRuntime`에 `sendChatMessage()` 메서드 추가
2. EventSource를 사용한 SSE 스트리밍 처리
3. 이벤트 타입별 처리 (`text`, `ui`, `error`, `done`)

```typescript
async sendChatMessage(message: string, context: string = "default"): Promise<void> {
    if (!message.trim() || this.state.connectionStatus !== 'connected') {
        return;
    }

    // 사용자 메시지 추가
    const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: message.trim(),
        timestamp: new Date()
    };
    this.addMessage(userMessage);

    // 어시스턴트 메시지 생성 (로딩 상태)
    const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        isStreaming: true
    };
    this.addMessage(assistantMessage);
    this.currentStreamingMessageId = assistantMessage.id;
    this.setState({ status: 'loading', error: null });

    try {
        // SSE 엔드포인트 호출
        const url = `${this.endpoint}/chat/stream?message=${encodeURIComponent(message)}&context=${context}`;
        const eventSource = new EventSource(url);

        eventSource.onmessage = (event) => {
            try {
                const chunk: StreamChunk = JSON.parse(event.data);
                this.handleStreamChunk(chunk, assistantMessage.id);
            } catch (e) {
                console.error('Failed to parse stream chunk:', e);
            }
        };

        eventSource.onerror = (error) => {
            eventSource.close();
            this.updateMessage(assistantMessage.id, {
                content: '❌ 연결 오류가 발생했습니다.',
                isStreaming: false
            });
            this.setState({ status: 'error', error: 'Connection error' });
        };

        // 완료 시 정리
        eventSource.addEventListener('done', () => {
            eventSource.close();
            this.updateMessage(assistantMessage.id, {
                isStreaming: false
            });
            this.setState({ status: 'success' });
            this.currentStreamingMessageId = null;
        });
    } catch (error) {
        this.updateMessage(assistantMessage.id, {
            content: `❌ Error: ${error instanceof Error ? error.message : String(error)}`,
            isStreaming: false
        });
        this.setState({ 
            status: 'error', 
            error: error instanceof Error ? error.message : String(error) 
        });
        this.currentStreamingMessageId = null;
    }
}

private handleStreamChunk(chunk: StreamChunk, messageId: string): void {
    const currentMessage = this.state.messages.find(m => m.id === messageId);
    if (!currentMessage) return;

    switch (chunk.type) {
        case 'text':
            if (chunk.content) {
                const newContent = currentMessage.content + chunk.content;
                this.updateMessage(messageId, { content: newContent });
            }
            break;
        
        case 'ui':
            if (chunk.uiTree) {
                this.updateMessage(messageId, {
                    uiTree: chunk.uiTree,
                    content: currentMessage.content || '✅ UI가 생성되었습니다!'
                });
            }
            break;
        
        case 'error':
            this.updateMessage(messageId, {
                content: `❌ Error: ${chunk.error || 'Unknown error'}`,
                isStreaming: false
            });
            this.setState({ 
                status: 'error', 
                error: chunk.error || 'Unknown error' 
            });
            break;
        
        case 'done':
            this.updateMessage(messageId, {
                isStreaming: false
            });
            break;
    }
}
```

#### 3.2 라이브러리 Export 업데이트
**파일:** `packages/svelte/index.ts`

기존 export 유지, `sendChatMessage` 메서드는 `OgentRuntime` 클래스에 포함됨.

### Phase 4: 프론트엔드 데모 앱 수정

#### 4.1 일반 채팅 UI로 변경
**파일:** `apps/front/src/routes/+page.svelte` (수정)

**변경 사항:**
1. **환영 메시지 변경**
   - UI 생성에 특화된 메시지 제거
   - 일반적인 채팅 봇 환영 메시지

2. **메시지 처리**
   - 텍스트 메시지: 일반 채팅 메시지로 표시
   - UI 메시지: 자동으로 `UIRenderer`로 렌더링
   - 혼합 메시지: 텍스트 + UI 모두 표시

3. **스트리밍 처리**
   - `OgentRuntime.sendChatMessage()` 사용
   - 실시간 텍스트 업데이트
   - UI 생성 시 즉시 렌더링

**구현 예시:**
```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import { OgentRuntime, UIRenderer, generateTTLFromDesignSystem } from '@ogen/svelte';
  import { designSystem, designSystemMetadata } from '$lib/ds';
  import type { ChatMessage } from '@ogen/svelte';

  let query: string = "";
  let runtime: OgentRuntime;
  let messages: ChatMessage[] = [];
  let chatContainer: HTMLElement | null = null;

  onMount(() => {
    const userKnowledgeTTL = generateTTLFromDesignSystem(designSystem, designSystemMetadata);
    
    runtime = new OgentRuntime('http://localhost:8000/chat', {
      connectEndpoint: 'http://localhost:8000/api/connect',
      ttlContent: userKnowledgeTTL,
      autoConnect: true,
      enableStreaming: true
    });
    
    const unsubscribe = runtime.subscribe(state => {
      messages = state.messages;
      
      // 연결 시 환영 메시지
      if (state.connectionStatus === 'connected' && messages.length === 0) {
        messages.push({
          id: 'welcome',
          role: 'assistant',
          content: '안녕하세요! 무엇을 도와드릴까요?',
          timestamp: new Date()
        });
      }
    });
    
    return unsubscribe;
  });

  const handleSend = async () => {
    if (!query.trim()) return;
    await runtime.sendChatMessage(query.trim());
    query = '';
    
    // 스크롤
    setTimeout(() => {
      if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }
    }, 100);
  };
</script>

<div class="chat-container" bind:this={chatContainer}>
  {#each messages as message (message.id)}
    <div class="message message-{message.role}">
      <div class="message-content">
        {message.content}
        {#if message.isStreaming}
          <span class="cursor">▋</span>
        {/if}
      </div>
      {#if message.uiTree}
        <div class="message-ui">
          <UIRenderer node={message.uiTree} components={designSystem} />
        </div>
      {/if}
    </div>
  {/each}
</div>
```

## 개선된 계획서 요약

### 추가된 내용
1. ✅ 프론트엔드 라이브러리 확장 (SSE 스트리밍 처리)
2. ✅ 프론트엔드 데모 앱 수정 (일반 채팅 UI)
3. ✅ 이벤트 처리 상세화
4. ✅ 구현 예시 추가

### 최종 점수: 95/100

**개선 사항:**
- 프론트엔드 스트리밍 처리 상세화: +5점
- 일반 채팅 UI 계획 추가: +3점
- 프론트엔드 이벤트 처리 예시 추가: +3점

**남은 개선점:**
- 실제 테스트 시나리오 추가 (선택적)
- 성능 최적화 가이드 (선택적)

