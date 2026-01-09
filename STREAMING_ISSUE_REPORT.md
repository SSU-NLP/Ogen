# 스트리밍 문제 분석 보고서

## 테스트 환경
- **날짜**: 2025년 1월
- **프론트엔드**: SvelteKit (http://localhost:5173)
- **백엔드**: FastAPI (http://localhost:8000)
- **브라우저**: Chrome (개발자 도구 사용)

## 발견된 문제점 및 해결

### 1. URL 경로 중복 문제 ✅ (해결됨)
**문제**: `/chat/chat/stream`으로 잘못된 경로 요청
- **원인**: 프론트엔드 `endpoint`가 `http://localhost:8000/chat`으로 설정되어 있었음
- **해결**: `endpoint`를 `http://localhost:8000`으로 수정
- **상태**: ✅ 해결 완료

### 2. HTTP 메서드 불일치 ✅ (해결됨)
**문제**: `EventSource`는 GET만 지원하는데 백엔드가 POST 사용
- **원인**: `EventSource` API는 GET 요청만 지원
- **해결**: 백엔드 엔드포인트를 `@app.get("/chat/stream")`으로 변경
- **상태**: ✅ 해결 완료

### 3. SSE 이벤트 형식 문제 ✅ (수정 완료)
**문제**: 스트리밍 요청은 200으로 성공하지만 데이터가 전송되지 않음

**원인 분석**:
1. **Enum 직렬화 문제**: `StreamEventType`이 Enum인데 JSON 직렬화 시 문제 발생 가능
2. **EventSourceResponse 형식**: `sse-starlette`의 `EventSourceResponse`가 문자열을 직접 처리하는 방식 확인 필요
3. **Langgraph 이벤트 구조**: `agent.astream()`의 실제 이벤트 구조가 예상과 다를 수 있음

**수정 사항**:
- ✅ `ServerSentEvent` 객체 직접 사용 (`format_sse_event` 대신)
- ✅ Enum을 문자열로 명시적 변환 (`StreamEventType.value`)
- ✅ 디버깅 로그 추가 (백엔드/프론트엔드)
- ✅ Langgraph 이벤트 구조 안전하게 처리 (dict/객체 모두 지원)

**상태**: ✅ 수정 완료 (테스트 필요)

### 4. 프론트엔드 이벤트 처리 ✅ (로깅 추가)
**문제**: `EventSource`의 `onmessage`가 호출되지 않을 수 있음

**확인 사항**:
- ✅ SSE 응답 형식 확인 (ServerSentEvent 사용)
- ✅ CORS 설정 확인 (모든 origin 허용)
- ✅ 디버깅 로그 추가

**상태**: ✅ 로깅 추가 완료 (테스트 필요)

## 수정된 코드

### 백엔드 (`apps/server/main.py`)

**주요 변경사항**:
1. `ServerSentEvent` 객체 직접 사용
2. Enum을 문자열로 명시적 변환
3. 상세한 디버깅 로그 추가
4. Langgraph 이벤트 구조 안전하게 처리

```python
# 변경 전
yield format_sse_event(StreamEvent(
    type=StreamEventType.TEXT,
    content=word + " "
))

# 변경 후
event_dict = {
    "type": StreamEventType.TEXT.value,
    "content": word + " "
}
yield ServerSentEvent(data=json.dumps(event_dict, ensure_ascii=False))
```

**디버깅 로그**:
- 이벤트 수신 시 노드 이름 및 타입 로그
- 메시지 개수 및 타입 로그
- Tool 호출 감지 로그
- AI 응답 내용 로그
- Tool 결과 파싱 로그

### 라이브러리 (`packages/ogen_stream/src/ogen_stream/stream.py`)

**주요 변경사항**:
- `format_sse_event`에서 Enum을 문자열로 명시적 변환
- None 값 제거로 JSON 크기 최적화

```python
def format_sse_event(event: StreamEvent) -> str:
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
```

### 프론트엔드 (`packages/svelte/index.ts`)

**주요 변경사항**:
- 콘솔 로그 추가로 디버깅 용이성 향상

```typescript
eventSource.onmessage = (event) => {
    console.log('📥 SSE message received:', event.data);
    try {
        const chunk: StreamChunk = JSON.parse(event.data);
        console.log('📦 Parsed chunk:', chunk);
        this.handleStreamChunk(chunk, assistantMessage.id);
    } catch (e) {
        console.error('❌ Failed to parse stream chunk:', e, event.data);
    }
};
```

## 테스트 결과

### 브라우저 테스트 결과
- ✅ 페이지 로드 성공
- ✅ `/api/connect` 요청 성공 (200)
- ⚠️ `/chat/stream` 요청은 아직 테스트되지 않음 (서버 재시작 필요)

### 현재 수정 상태
- ✅ URL 경로 문제 해결 (`/chat/chat/stream` → `/chat/stream`)
- ✅ HTTP 메서드 문제 해결 (`POST` → `GET`)
- ✅ SSE 형식 개선 (`ServerSentEvent` 객체 사용)
- ✅ Enum 직렬화 문제 해결 (`StreamEventType.value` 사용)
- ✅ 디버깅 로그 추가 (백엔드/프론트엔드)
- ✅ Langgraph 이벤트 구조 안전하게 처리
- ⚠️ 실제 스트리밍 동작 확인 필요 (서버 재시작 후 테스트)

## 다음 테스트 단계

### 1. 서버 재시작 후 실제 테스트
```bash
# 백엔드 서버 재시작
cd apps/server
python main.py
```

**테스트 시나리오**:
1. 프론트엔드에서 "로그인 폼 만들어줘" 메시지 전송
2. 백엔드 터미널에서 디버깅 로그 확인
3. 브라우저 콘솔에서 SSE 메시지 수신 확인
4. 네트워크 탭에서 실제 SSE 응답 확인

### 2. 콘솔 로그 확인
**백엔드 로그에서 확인할 내용**:
- `📩 Starting stream for message: ...`
- `🔍 Event received: [...]`
- `📦 Node: agent, Type: ...`
- `💬 Messages count: ...`
- `✍️ AI Content: ...`
- `🛠️ Tools node output`
- `✅ UI Tree found, sending...`

**프론트엔드 콘솔에서 확인할 내용**:
- `📥 SSE message received: ...`
- `📦 Parsed chunk: ...`
- 에러 메시지 (있는 경우)

### 3. 네트워크 탭 확인
- `/chat/stream` 요청의 Response 탭에서 SSE 이벤트 스트림 확인
- `data: {"type":"text","content":"..."}` 형식으로 전송되는지 확인

### 4. Langgraph 이벤트 구조 검증
- 백엔드 로그를 통해 실제 이벤트 구조 확인
- 필요시 이벤트 처리 로직 수정

## 예상되는 추가 문제점

### 1. Langgraph 이벤트 구조 불일치
**가능성**: `create_react_agent`의 실제 이벤트 구조가 예상과 다를 수 있음

**대응 방안**:
- 디버깅 로그를 통해 실제 구조 확인
- 필요시 이벤트 처리 로직 수정
- Langgraph 문서 참고

### 2. SSE 이벤트 타입
**가능성**: 일부 브라우저는 `event: message` 형식을 요구할 수 있음

**대응 방안**:
```python
yield ServerSentEvent(
    event="message",
    data=json.dumps(event_dict, ensure_ascii=False)
)
```

### 3. CORS 설정
**현재 상태**: ✅ FastAPI CORS 미들웨어가 모든 origin을 허용하도록 설정됨

## 권장 사항

1. **서버 재시작 후 테스트**
   - 수정된 코드로 서버 재시작
   - 실제 스트리밍 동작 확인

2. **로그 기반 디버깅**
   - 백엔드/프론트엔드 로그를 통해 이벤트 흐름 추적
   - 문제 발생 시 로그를 기반으로 수정

3. **점진적 개선**
   - 기본 스트리밍이 작동하는지 먼저 확인
   - 이후 텍스트 스트리밍, UI 렌더링 순서로 검증

4. **에러 처리 강화**
   - 각 단계에서 예외 처리
   - 사용자에게 명확한 에러 메시지 표시

## 결론

### 해결된 문제
- ✅ URL 경로 중복
- ✅ HTTP 메서드 불일치
- ✅ SSE 형식 개선
- ✅ Enum 직렬화
- ✅ 디버깅 로그 추가

### 확인 필요
- ⚠️ 실제 스트리밍 동작 (서버 재시작 후 테스트)
- ⚠️ Langgraph 이벤트 구조 (로그 확인)
- ⚠️ 프론트엔드 이벤트 수신 (콘솔 확인)

### 다음 액션
1. 백엔드 서버 재시작
2. 프론트엔드에서 메시지 전송
3. 백엔드/프론트엔드 로그 확인
4. 필요시 추가 수정
