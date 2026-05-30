# Streaming Bug Fixes & Model Config Design

**Date**: 2026-05-27  
**Scope**: Bug 1 + Bug 2 (streaming correctness) + Feature 3 (single shared model config)

---

## Context

Ogen-UI is a full-stack streaming app: the backend emits SSE frames (text / ui / done / error), and the frontend parses and renders them in real time. Two bugs currently break this pipeline. Additionally, the model used across all pipeline stages is hardcoded and cannot be changed without editing source.

---

## Bug 1 — `POST /chat/stream` always 500s

### Location
`apps/server/main.py:83-84`, `main.py:311-313`

### Root cause
`ChatRequest` has only a `message` field, but `chat_stream_post` reads `request.context`. Python raises `AttributeError` before any SSE frame is sent.

```python
# Current — broken
class ChatRequest(BaseModel):
    message: str

async def chat_stream_post(request: ChatRequest):
    event_generator = _chat_stream_event_generator(
        request.message, request.context  # AttributeError
    )
```

### Fix
Add `context: str = "default"` to `ChatRequest`.

```python
class ChatRequest(BaseModel):
    message: str
    context: str = "default"
```

### Impact
`POST /chat/stream` becomes functional. The `OgentRuntime.executeStreaming()` fetch-based path can now reach the SSE generator.

---

## Bug 2 — Welcome message disappears on first streaming update

### Location
`apps/front/src/routes/+page.svelte:55-75`

### Root cause
The welcome message is appended to the **local** `messages` variable inside the `runtime.subscribe` callback. The next state update from the runtime overwrites `messages = state.messages`, erasing it.

```typescript
// Current — broken
const unsubscribe = runtime.subscribe((state) => {
    messages = state.messages;              // overwrites local array
    connectionStatus = state.connectionStatus;

    if (state.connectionStatus === "connected" && messages.length === 0) {
        messages.push({ id: "welcome", ... }); // lost on next update
    }
});
```

### Fix
Manage the welcome message as local state, set once on connection. Switch to `state.messages` only when the runtime has real messages.

```typescript
let welcomeShown = false;
let messages: ChatMessage[] = [];

const unsubscribe = runtime.subscribe((state) => {
    connectionStatus = state.connectionStatus;

    if (state.messages.length > 0) {
        messages = state.messages;
    } else if (state.connectionStatus === "connected" && !welcomeShown) {
        welcomeShown = true;
        messages = [{
            id: "welcome",
            role: "assistant",
            content: "Hi! What can I help you with?",
            timestamp: new Date(),
        }];
    }
});
```

### Impact
- Welcome message appears exactly once when connected.
- Streaming messages replace it cleanly with no flicker.
- `clearMessages()` after chatting does not re-show the welcome (`welcomeShown` stays `true`).

---

## Feature 3 — Single shared model via environment variable

### Current state
All four engine stages (analysis, anchor, generation, pruning) read from `self.model_config` dict, each with a different hardcoded default. The LangGraph agent model in `main.py` is also hardcoded separately. Neither can be changed without editing source.

### Fix — `engine.py`
Remove `_load_model_config` and the `model_config` dict. Replace with a single `self.model` string resolved from the `OGEN_MODEL` env var, falling back to `"gpt-5"`. The existing single `self.client` is kept as-is.

```python
# __init__
self.model = os.getenv("OGEN_MODEL", "gpt-5")
```

Every `self.model_config.get("<stage>", ...)` call becomes `self.model`.

### Fix — `main.py`
```python
llm = ChatOpenAI(
    model=os.getenv("OGEN_MODEL", "gpt-5"),
    api_key=SecretStr(API_KEY),
    base_url=BASE_URL,
    temperature=0,
)
```

### New file — `apps/server/.env.example`
```dotenv
OPENAI_API_KEY=sk-...
# OPENAI_BASE_URL=

# Single model used across all pipeline stages (optional, default: gpt-5)
# OGEN_MODEL=gpt-5
```

---

## Files Changed

| File | Change |
|------|--------|
| `apps/server/main.py` | Add `context` to `ChatRequest`; read `OGEN_MODEL` for `ChatOpenAI` |
| `apps/front/src/routes/+page.svelte` | Fix welcome-message state management in subscribe callback |
| `packages/ogen_stream/src/ogen_stream/engine.py` | Remove `_load_model_config`; replace `model_config` dict with single `self.model` |
| `apps/server/.env.example` (new) | Document all configurable env vars |

---

## Out of Scope

- BFS `deque` swap (performance, separate PR)
- N+1 SPARQL batching (performance, separate PR)
- Bugs 3–5 (code hygiene, separate PR — defined below)

---

## Bugs 3–5 (code hygiene) — definitions

Identified 2026-05-29 by code audit. These were referenced as deferred but
never specified; recorded here so the follow-up PR has a concrete scope.

### Bug 3 — dead SPARQL in `is_user_data_loaded()`

`packages/ogen_stream/src/ogen_stream/engine.py:673` builds and executes a
`SELECT (COUNT(?s) ...)` query, assigns the result to `results`, then ignores
it and returns `self.user_data_loaded`. The query hits the store on every
`connect_user_data()` and `GET /api/connect/status` call for no effect.

**Fix:** delete the query block; return `self.user_data_loaded` directly.
Update the stale comment that claims it "Check[s] if GRAPH_USER has data".

### Bug 4 — vestigial named-graph constants

`OgenEngine.__init__` (engine.py:58–60) defines `self.GRAPH_CORE`,
`self.GRAPH_USER`, `self.GRAPH_CONTEXT` as `NamedNode`s, but nothing reads
them — all data is loaded into the default graph (confirmed by grep across
`packages/` and `apps/`; only references are these definitions plus a docstring
and a comment). Leftover from an abandoned named-graph design.

**Fix:** remove the three attributes and update the stale docstring on
`_build_index` ("unified search across GRAPH_CORE + GRAPH_USER") and the
comment in `is_user_data_loaded` (resolved alongside Bug 3).

### Bug 5 — unused imports in `main.py`

`apps/server/main.py:16` imports `StreamEvent` and `format_sse_event` from
`ogen_stream.stream`, but only `StreamEventType` is used (5×). The other two
are dead imports.

**Fix:** drop `StreamEvent` and `format_sse_event` from the import, keeping
`StreamEventType`. (Minor: trailing whitespace on line 20 can be cleaned up in
the same pass.)
