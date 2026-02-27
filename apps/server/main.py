from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, SecretStr
from typing import Any, cast
from dotenv import load_dotenv
import os
import json
import uvicorn
from sse_starlette.sse import EventSourceResponse
from sse_starlette.event import ServerSentEvent
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from ogen_stream.engine import OgenEngine
from ogen_stream.ui_generator import UIGenerationPipeline
from ogen_stream.tools import create_langchain_tool
from ogen_stream.stream import StreamEvent, StreamEventType, format_sse_event

# load .env
load_dotenv()
    
app = FastAPI(title="Ogen AI Engine API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# engine initialization (server start)
# ontology is loaded automatically inside the library
API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL")

if not API_KEY:
    raise ValueError("OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다.")

try:
    # engine initialization (ontology loaded, user data received via API)
    engine = OgenEngine(
        openai_api_key=API_KEY,
        openai_base_url=BASE_URL,
        persistence_dir=os.path.join(os.path.dirname(__file__), "ogen_data"),
        model_config_path=os.getenv("OGEN_MODEL_CONFIG_PATH"),
    )
    print("✅ Ogen Engine initialized successfully (Ontology loaded).")

    pipeline = UIGenerationPipeline(engine)

    ui_tool = create_langchain_tool(pipeline)

    # Generate Agent (Tool included)
    # Use an OpenAI-compatible tool-calling model.
    llm = ChatOpenAI(
        model="gpt-5",
        api_key=SecretStr(API_KEY),
        base_url=BASE_URL,
        temperature=0,
    )
    tools = [ui_tool]

    TOOL_CALLING_SYSTEM_PROMPT = (
        "You are an enterprise UI assistant. Your job is to help users quickly by either: "
        "(A) answering with plain text when text is sufficient, or "
        "(B) calling the generate_ui tool when showing a UI would help the user. "
        "If a UI would help, you MUST call generate_ui. "
        "Never invent component types not present in the knowledge graph. "
        "When calling generate_ui, pass user_query exactly and pass context_mode when relevant."
    )

    agent = create_agent(llm, tools, system_prompt=TOOL_CALLING_SYSTEM_PROMPT)

    print("✅ Langgraph Agent initialized successfully.")
except Exception as e:
    print(f"❌ Failed to initialize engine/agent: {e}")
    raise e


class UIRequest(BaseModel):
    query: str


class ChatRequest(BaseModel):
    message: str


class ConnectRequest(BaseModel):
    ttl_content: str
    base_iri: str = "http://myapp.com/ui/"
    force: bool = False


@app.post("/generate-ui")
def generate_ui(request: UIRequest):
    """
    [Flow]
    User Request -> FastAPI -> OgenEngine (Search -> Prompt -> LLM) -> JSON Response
    """
    print(f"📩 Received Query: {request.query}")

    try:
        result = engine.reason(request.query)

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
    Check connection status (already connected)

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


@app.post("/api/connect")
async def connect_knowledge_graph(request: ConnectRequest):
    """
    Connect knowledge graph from frontend to backend

    Returns:
        dict: {
            "status": "success" | "already_connected",
            "node_count": int,
            "message": str
        }
    """

    try:
        result = engine.connect_user_data(
            ttl_string=request.ttl_content,
            base_iri=request.base_iri,
            force=request.force,
        )
        return result

    except ValueError as e:
        print(f"❌ Connect Error: {str(e)}")

        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"🔥 Internal Error: {str(e)}")

        raise HTTPException(status_code=500, detail=str(e))


def _chat_stream_event_generator(message: str, context: str):
    """Shared SSE generator for chat streaming.

    Design goal:
    - Tool-calling only: UI JSON must come from the generate_ui tool.
    - LLM decides: If showing UI is helpful, call the tool.
    """

    async def event_generator():
        try:
            print(f"📩 Starting stream for message: {message} (Context: {context})")

            config = {"configurable": {"thread_id": f"thread_{os.urandom(4).hex()}"}}
            emitted_text = ""

            inputs = {
                "messages": [
                    {
                        "role": "user",
                        "content": f"{message}",
                    }
                ]
            }

            async for event in agent.astream(
                cast(Any, inputs),
                config=cast(Any, config),
                stream_mode="updates",
            ):
                if not isinstance(event, dict):
                    continue

                for _node_name, node_output in event.items():
                    if not isinstance(node_output, dict):
                        continue

                    node_messages = node_output.get("messages", [])
                    for msg in node_messages:
                        msg_type = getattr(msg, "type", None) or (
                            msg.get("type") if isinstance(msg, dict) else None
                        )

                        # Text from AI messages
                        if msg_type == "ai" or (
                            isinstance(msg, dict) and msg.get("type") == "ai"
                        ):
                            content = getattr(msg, "content", None) or (
                                msg.get("content") if isinstance(msg, dict) else None
                            )
                            if not content or not isinstance(content, str):
                                continue

                            if content.startswith(emitted_text):
                                delta = content[len(emitted_text) :]
                            else:
                                delta = content

                            if delta:
                                emitted_text = content
                                yield ServerSentEvent(
                                    data=json.dumps(
                                        {
                                            "type": StreamEventType.TEXT.value,
                                            "content": delta,
                                        },
                                        ensure_ascii=False,
                                    )
                                )

                        # Tool results from ToolMessage
                        if msg_type == "tool" or (
                            isinstance(msg, dict) and msg.get("type") == "tool"
                        ):
                            msg_content = getattr(msg, "content", None) or (
                                msg.get("content") if isinstance(msg, dict) else None
                            )
                            if not msg_content:
                                continue

                            try:
                                tool_result = (
                                    json.loads(msg_content)
                                    if isinstance(msg_content, str)
                                    else msg_content
                                )
                            except Exception:
                                continue

                            if isinstance(tool_result, dict) and tool_result.get(
                                "success"
                            ):
                                ui_tree = tool_result.get("ui_tree")
                                if ui_tree:
                                    yield ServerSentEvent(
                                        data=json.dumps(
                                            {
                                                "type": StreamEventType.UI.value,
                                                "uiTree": ui_tree,
                                            },
                                            ensure_ascii=False,
                                        )
                                    )

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

    return event_generator


# Browser EventSource requires GET (no request body).
@app.get("/chat/stream")
async def chat_stream(message: str, context: str = "default"):
    """
    Response with Server-Sent Events
    When the agent calls a tool, it sends a UI event, and the text response is sent as a text event.
    """
    event_generator = _chat_stream_event_generator(message, context)
    return EventSourceResponse(event_generator())


@app.post("/chat/stream")
async def chat_stream_post(request: ChatRequest):
    event_generator = _chat_stream_event_generator(request.message, request.context)
    return EventSourceResponse(event_generator())


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
