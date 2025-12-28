from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import uvicorn
from ogen_stream.engine import OgenEngine 

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
# 실제 운영 환경에서는 경로 관리가 중요합니다.
# 현재 폴더에 knowledge.ttl이 있다고 가정합니다.
TTL_PATH = "./data/knowledge.ttl" 
API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise ValueError("OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다.")

try:
    # 엔진 인스턴스 생성 (이때 그래프 로딩 및 임베딩 인덱싱 수행)
    engine = OgenEngine(TTL_PATH, API_KEY)
    print("✅ Ogen Engine initialized successfully.")
except Exception as e:
    print(f"❌ Failed to initialize engine: {e}")
    raise e

# --- 2. 요청 모델 정의 ---
class UIRequest(BaseModel):
    query: str
    context: str = "default"

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)