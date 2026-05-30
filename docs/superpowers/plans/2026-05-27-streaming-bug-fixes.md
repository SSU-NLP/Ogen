# Streaming Bug Fixes & Model Config Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix two runtime bugs that break the streaming pipeline and simplify model configuration to a single `OGEN_MODEL` environment variable.

**Architecture:** Three independent changes — (1) a one-line backend model fix, (2) a backend field addition, (3) a frontend subscribe-callback fix. The model config simplification removes `_load_model_config` entirely and replaces all per-stage `model_config.get(...)` calls with `self.model`. No new abstractions introduced.

**Tech Stack:** Python 3.11 / FastAPI / pyoxigraph / openai SDK (backend) · SvelteKit 5 / TypeScript (frontend) · No test framework configured — manual testing via `uvicorn` + browser.

---

## File Map

| File | Action | What changes |
|------|--------|-------------|
| `packages/ogen_stream/src/ogen_stream/engine.py` | Modify | Remove `_load_model_config`, `model_config` param; add `self.model = os.getenv(...)` |
| `apps/server/main.py` | Modify | Add `context` to `ChatRequest`; remove `model_config_path` kwarg; use `OGEN_MODEL` for `ChatOpenAI` |
| `apps/front/src/routes/+page.svelte` | Modify | Fix welcome-message state management in subscribe callback |
| `apps/server/.env.example` | Create | Document all configurable env vars |

---

## Task 1: Simplify engine model config

**Files:**
- Modify: `packages/ogen_stream/src/ogen_stream/engine.py`

### What to change

Remove the `_load_model_config` method and the `model_config` / `model_config_path` constructor parameters. Replace with a single `self.model` string read from the `OGEN_MODEL` env var.

- [ ] **Step 1: Update `__init__` signature and body**

In `engine.py`, replace the constructor's model-config block. The current signature is:

```python
def __init__(
    self,
    openai_api_key: str,
    persistence_dir: str = "./ogen_data",
    openai_base_url: str | None = None,
    model_config: dict[str, str] | None = None,
    model_config_path: str | None = None,
):
    self.client = openai.OpenAI(api_key=openai_api_key, base_url=openai_base_url)
    ...
    self.model_config = self._load_model_config(model_config, model_config_path)
```

Change it to:

```python
def __init__(
    self,
    openai_api_key: str,
    persistence_dir: str = "./ogen_data",
    openai_base_url: str | None = None,
):
    self.client = openai.OpenAI(api_key=openai_api_key, base_url=openai_base_url)
    self.model = os.getenv("OGEN_MODEL", "gpt-5")
    ...
    # remove: self.model_config = self._load_model_config(...)
```

- [ ] **Step 2: Delete `_load_model_config` method**

Remove the entire `_load_model_config` method (lines ~92–122 in engine.py):

```python
# DELETE this entire method
def _load_model_config(
    self,
    model_config: dict[str, str] | None,
    model_config_path: str | None,
) -> dict[str, str]:
    ...
```

- [ ] **Step 3: Replace all `self.model_config.get(...)` calls**

There are four usages. Replace each:

In `analyze_requirement` (~line 400):
```python
# Before
model=self.model_config.get("analysis", "gpt-5"),
# After
model=self.model,
```

In `find_anchor_node_with_llm` (~line 484):
```python
# Before
model=self.model_config.get("anchor", "gpt-5"),
# After
model=self.model,
```

In `_agentic_filter_children` (~line 282):
```python
# Before
model=self.model_config.get("pruning", "gpt-4o-mini"),
# After
model=self.model,
```

In `_generate_ui_with_context` (~line 667):
```python
# Before
model=self.model_config.get("generation", "gpt-5"),
# After
model=self.model,
```

- [ ] **Step 4: Remove redundant `import json` inside loop**

In `_get_node_properties`, there is an `import json` inside the `for binding in results:` loop. Remove that line — `json` is already imported at the top of the file.

```python
# Before (inside loop)
try:
    import json                  # DELETE this line
    parsed_value = json.loads(o_val)
except:
    parsed_value = o_val

# After
try:
    parsed_value = json.loads(o_val)
except:
    parsed_value = o_val
```

- [ ] **Step 5: Commit**

```bash
git add packages/ogen_stream/src/ogen_stream/engine.py
git commit -m "refactor: replace per-stage model_config with single OGEN_MODEL env var"
```

---

## Task 2: Fix `main.py` — ChatRequest and model wiring

**Files:**
- Modify: `apps/server/main.py`

### What to change

1. Add missing `context` field to `ChatRequest` (Bug 1).
2. Remove the now-deleted `model_config_path` kwarg from the `OgenEngine(...)` call.
3. Use `OGEN_MODEL` env var for `ChatOpenAI`.

- [ ] **Step 1: Add `context` to `ChatRequest`**

```python
# Before
class ChatRequest(BaseModel):
    message: str

# After
class ChatRequest(BaseModel):
    message: str
    context: str = "default"
```

- [ ] **Step 2: Remove `model_config_path` from `OgenEngine(...)` call**

The `OgenEngine` constructor no longer accepts `model_config_path`. Find the call (~line 40) and remove that kwarg:

```python
# Before
engine = OgenEngine(
    openai_api_key=API_KEY,
    openai_base_url=BASE_URL,
    persistence_dir=os.path.join(os.path.dirname(__file__), "ogen_data"),
    model_config_path=os.getenv("OGEN_MODEL_CONFIG_PATH"),   # DELETE
)

# After
engine = OgenEngine(
    openai_api_key=API_KEY,
    openai_base_url=BASE_URL,
    persistence_dir=os.path.join(os.path.dirname(__file__), "ogen_data"),
)
```

- [ ] **Step 3: Use `OGEN_MODEL` for the LangGraph agent**

```python
# Before
llm = ChatOpenAI(
    model="gpt-5",
    api_key=SecretStr(API_KEY),
    base_url=BASE_URL,
    temperature=0,
)

# After
llm = ChatOpenAI(
    model=os.getenv("OGEN_MODEL", "gpt-5"),
    api_key=SecretStr(API_KEY),
    base_url=BASE_URL,
    temperature=0,
)
```

- [ ] **Step 4: Verify the server starts**

```bash
cd apps/server
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Expected output includes:
```
✅ Ogen Engine initialized successfully (Ontology loaded).
✅ Langgraph Agent initialized successfully.
INFO:     Application startup complete.
```

No `TypeError: __init__() got an unexpected keyword argument 'model_config_path'` should appear.

- [ ] **Step 5: Verify `POST /chat/stream` no longer 500s**

With the server running, send a test request (in a second terminal):

```bash
curl -N -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "hello", "context": "default"}'
```

Expected: SSE frames appear (e.g. `data: {"type":"text","content":"..."}`) instead of a 500 error response.

- [ ] **Step 6: Commit**

```bash
git add apps/server/main.py
git commit -m "fix: add context field to ChatRequest; wire OGEN_MODEL to ChatOpenAI"
```

---

## Task 3: Fix welcome message state management

**Files:**
- Modify: `apps/front/src/routes/+page.svelte`

### What to change

The welcome message is currently pushed directly onto the local `messages` array inside the subscribe callback. The runtime overwrites this on the next state update. Fix: manage the welcome message as separate local state, set once when connected.

- [ ] **Step 1: Add `welcomeShown` flag before `onMount`**

Find the variable declarations near the top of the `<script>` block (around line 15–22) and add `welcomeShown`:

```typescript
let query: string = "";
let runtime: OgentRuntime | null = null;
let messages: ChatMessage[] = [];
let welcomeShown = false;           // ADD this line
let chatContainer: HTMLElement | null = null;
let connectionStatus: "disconnected" | "connecting" | "connected" | "error" =
  "disconnected";
let loadingUIMessages: Set<string> = new Set();
let activeMetadata: Record<string, ComponentMetadata> =
  defaultDesignSystemMetadata;
```

- [ ] **Step 2: Rewrite the subscribe callback**

Find the `runtime.subscribe(...)` call inside `onMount` (around line 55) and replace the entire callback body:

```typescript
// Before
const unsubscribe = runtime.subscribe((state) => {
  messages = state.messages;
  connectionStatus = state.connectionStatus;

  loadingUIMessages = new Set(
    state.messages
      .filter((m) => m.role === "assistant" && m.isStreaming && !m.uiTree)
      .map((m) => m.id),
  );

  if (state.connectionStatus === "connected" && messages.length === 0) {
    messages.push({
      id: "welcome",
      role: "assistant",
      content: "Hi! What can I help you with?",
      timestamp: new Date(),
    });
  }
});

// After
const unsubscribe = runtime.subscribe((state) => {
  connectionStatus = state.connectionStatus;

  if (state.messages.length > 0) {
    messages = state.messages;
  } else if (state.connectionStatus === "connected" && !welcomeShown) {
    welcomeShown = true;
    messages = [
      {
        id: "welcome",
        role: "assistant",
        content: "Hi! What can I help you with?",
        timestamp: new Date(),
      },
    ];
  }

  loadingUIMessages = new Set(
    state.messages
      .filter((m) => m.role === "assistant" && m.isStreaming && !m.uiTree)
      .map((m) => m.id),
  );
});
```

- [ ] **Step 3: Run type check**

```bash
cd apps/front
pnpm check
```

Expected: no errors. If any type errors appear on `welcomeShown`, verify it is declared in the same `<script>` block scope as the `onMount` call.

- [ ] **Step 4: Manual test in browser**

Start both servers (`./start.sh` from repo root), open `http://localhost:5173`.

1. Wait for "Connected" badge to appear.
2. Confirm welcome message "Hi! What can I help you with?" is visible.
3. Type a message and send it.
4. Confirm the welcome message is **not** replaced or removed — it stays as the first message in the thread while new messages append below it.

- [ ] **Step 5: Commit**

```bash
git add apps/front/src/routes/+page.svelte
git commit -m "fix: preserve welcome message across runtime state updates"
```

---

## Task 4: Create `.env.example`

**Files:**
- Create: `apps/server/.env.example`

- [ ] **Step 1: Create the file**

```dotenv
# Required
OPENAI_API_KEY=sk-...

# Optional — OpenAI-compatible base URL (default: OpenAI)
# OPENAI_BASE_URL=https://api.openai.com/v1

# Optional — single model used for all pipeline stages (default: gpt-5)
# OGEN_MODEL=gpt-5
```

- [ ] **Step 2: Commit**

```bash
git add apps/server/.env.example
git commit -m "docs: add .env.example with OGEN_MODEL documentation"
```

---

## Self-Review Notes

**Spec coverage:**
- Bug 1 (`ChatRequest.context`) → Task 2 Step 1 ✅
- Bug 2 (welcome message) → Task 3 ✅
- Feature 3 (`OGEN_MODEL` env var) → Task 1 + Task 2 Steps 2–3 ✅
- `.env.example` → Task 4 ✅

**Removed `OGEN_MODEL_CONFIG_PATH`:** The JSON-file override mechanism is removed alongside `_load_model_config`. If it was referenced in an existing `.env` file, that line can be deleted — it has no effect after Task 1.

**`is_user_data_loaded()` dead SPARQL:** Out of scope for this plan per spec (Bugs 3–5 deferred). Not included.
