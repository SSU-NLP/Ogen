from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import uvicorn
import json
from sse_starlette.sse import EventSourceResponse, ServerSentEvent
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from ogen_stream.engine import OgenEngine
from ogen_stream.ui_generator import UIGenerationPipeline
from ogen_stream.tools import create_langchain_tool
from ogen_stream.stream import StreamEvent, StreamEventType, format_sse_event

# .env 로드
load_dotenv()

app = FastAPI(title="Ogen AI Engine API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- 1. 엔진 초기화 (서버 시작 시 1회 로드) ---
# 온톨로지는 라이브러리 내부에서 자동 로드됨
API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise ValueError("OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다.")

try:
    # 엔진 인스턴스 생성 (온톨로지만 로드, 사용자 데이터는 API로 받음)
    engine = OgenEngine(openai_api_key=API_KEY)
    print("✅ Ogen Engine initialized successfully (Ontology loaded).")

    # UI 생성 파이프라인 생성
    pipeline = UIGenerationPipeline(engine)

    # Langchain Tool 생성
    ui_tool = create_langchain_tool(pipeline)

    # Agent 생성 (Tool 포함)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=API_KEY)
    tools = [ui_tool]
    agent = create_agent(llm, tools)

    print("✅ Langgraph Agent initialized successfully.")
except Exception as e:
    print(f"❌ Failed to initialize engine/agent: {e}")
    raise e


# --- 2. 요청 모델 정의 ---
class UIRequest(BaseModel):
    query: str
    context: str = "default"


class ChatRequest(BaseModel):
    message: str
    context: str = "default"


class ConnectRequest(BaseModel):
    ttl_content: str
    base_iri: str = "http://myapp.com/ui/"


# --- 3. API 엔드포인트 ---
@app.post("/generate-ui")
def generate_ui(request: UIRequest):
    """
    [Flow]
    User Request -> FastAPI -> OgenEngine (Search -> Prompt -> LLM) -> JSON Response
    """
    print(f"📩 Received Query: {request.query} (Context: {request.context})")

    try:
        # 엔진에게 모든 '추론'과 '생성'을 위임합니다.
        result = engine.reason(request.query, context_mode=request.context)

        # 엔진에서 에러를 딕셔너리로 반환했을 경우 처리
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return result

    except Exception as e:
        print(f"🔥 Internal Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# --- 4. 연결 상태 확인 API ---
@app.get("/api/connect/status")
async def check_connection_status():
    """
    현재 연결 상태 확인 (이미 연결되어 있는지 확인)

    Returns:
        dict: {
            "connected": bool,
            "node_count": int,
            "design_system_loaded": bool
        }
    """
    try:
        is_connected = engine.is_user_data_loaded()
        node_count = len(engine.nodes) if is_connected else 0

        return {
            "connected": is_connected,
            "node_count": node_count,
            "design_system_loaded": is_connected,
        }
    except Exception as e:
        return {
            "connected": False,
            "node_count": 0,
            "design_system_loaded": False,
            "error": str(e),
        }


# --- 5. 연결 API 엔드포인트 ---
@app.post("/api/connect")
async def connect_knowledge_graph(request: ConnectRequest):
    """
    프론트엔드에서 지식 그래프를 전송하여 백엔드에 연결

    Returns:
        dict: {
            "status": "success" | "already_connected",
            "node_count": int,
            "message": str
        }
    """
    try:
        # 라이브러리 함수 호출 - 모든 로직이 여기에 캡슐화됨
        result = engine.connect_user_data(
            ttl_string=request.ttl_content, base_iri=request.base_iri
        )
        return result  # 그대로 반환
    except ValueError as e:
        # TTL 파싱 에러 등
        print(f"❌ Connect Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 기타 서버 에러
        print(f"🔥 Internal Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# --- 5. Chat 스트리밍 엔드포인트 ---
@app.get("/chat/stream")
async def chat_stream(message: str, context: str = "default"):
    """
    Server-Sent Events로 스트리밍 응답
    Agent가 Tool을 호출하면 UI 이벤트 전송, 텍스트 응답은 텍스트 이벤트로 전송
    """

    async def event_generator():
        try:
            # Agent 실행 및 스트리밍
            config = {"configurable": {"thread_id": f"thread_{os.urandom(4).hex()}"}}

            print(f"📩 Starting stream for message: {message}")

            async for event in agent.astream(
                {"messages": [("user", message)]}, config=config
            ):
                print(f"🔍 Event received: {list(event.keys())}")

                # Agent의 각 단계를 이벤트로 변환
                for node_name, node_output in event.items():
                    print(f"  📦 Node: {node_name}, Type: {type(node_output)}")

                    if node_name == "agent":
                        # Langgraph agent는 StateGraph를 반환하므로 node_output은 State
                        if isinstance(node_output, dict):
                            messages = node_output.get("messages", [])
                            print(f"    💬 Messages count: {len(messages)}")

                            for msg in messages:
                                # Langchain 메시지 객체 확인
                                msg_type = getattr(msg, "type", None) or (
                                    msg.get("type") if isinstance(msg, dict) else None
                                )
                                print(f"      📨 Message type: {msg_type}")

                                # Tool 호출 메시지 확인
                                tool_calls = getattr(msg, "tool_calls", None) or (
                                    msg.get("tool_calls")
                                    if isinstance(msg, dict)
                                    else None
                                )
                                if tool_calls:
                                    print(f"      🔧 Tool calls: {len(tool_calls)}")
                                    for tool_call in tool_calls:
                                        tool_name = (
                                            tool_call.get("name")
                                            if isinstance(tool_call, dict)
                                            else getattr(tool_call, "name", None)
                                        )
                                        print(f"        🛠️ Tool: {tool_name}")

                                # AI 응답 메시지
                                if msg_type == "ai" or (
                                    isinstance(msg, dict) and msg.get("type") == "ai"
                                ):
                                    content = (
                                        getattr(msg, "content", None)
                                        or (
                                            msg.get("content")
                                            if isinstance(msg, dict)
                                            else None
                                        )
                                        or str(msg)
                                    )
                                    if (
                                        content
                                        and isinstance(content, str)
                                        and content.strip()
                                    ):
                                        print(f"      ✍️ AI Content: {content[:50]}...")
                                        # 텍스트를 단어 단위로 스트리밍
                                        words = content.split()
                                        for word in words:
                                            event_dict = {
                                                "type": StreamEventType.TEXT.value,
                                                "content": word + " ",
                                            }
                                            yield ServerSentEvent(
                                                data=json.dumps(
                                                    event_dict, ensure_ascii=False
                                                )
                                            )

                    elif node_name == "tools":
                        # Tool 실행 결과 처리
                        print(f"    🛠️ Tools node output")
                        if isinstance(node_output, dict):
                            messages = node_output.get("messages", [])
                            for msg in messages:
                                msg_content = getattr(msg, "content", None) or (
                                    msg.get("content")
                                    if isinstance(msg, dict)
                                    else None
                                )
                                if msg_content:
                                    print(
                                        f"      📦 Tool result: {str(msg_content)[:100]}..."
                                    )
                                    try:
                                        # Tool 결과가 JSON 문자열일 수 있음
                                        tool_result = (
                                            json.loads(msg_content)
                                            if isinstance(msg_content, str)
                                            else msg_content
                                        )
                                        if isinstance(tool_result, dict):
                                            if tool_result.get(
                                                "success"
                                            ) and tool_result.get("ui_tree"):
                                                print(
                                                    f"      ✅ UI Tree found, sending..."
                                                )
                                                event_dict = {
                                                    "type": StreamEventType.UI.value,
                                                    "uiTree": tool_result["ui_tree"],
                                                }
                                                yield ServerSentEvent(
                                                    data=json.dumps(
                                                        event_dict, ensure_ascii=False
                                                    )
                                                )
                                    except (json.JSONDecodeError, AttributeError) as e:
                                        print(
                                            f"      ⚠️ Failed to parse tool result: {e}"
                                        )
                                        pass

            # 완료 이벤트
            yield ServerSentEvent(
                data=json.dumps(
                    {"type": StreamEventType.DONE.value}, ensure_ascii=False
                )
            )

        except Exception as e:
            print(f"🔥 Stream Error: {str(e)}")
            import traceback

            traceback.print_exc()
            yield ServerSentEvent(
                data=json.dumps(
                    {"type": StreamEventType.ERROR.value, "error": str(e)},
                    ensure_ascii=False,
                )
            )

    return EventSourceResponse(event_generator())


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
