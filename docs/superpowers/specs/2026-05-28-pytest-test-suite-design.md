# pytest Test Suite Design

**Date**: 2026-05-28  
**Scope**: Backend-only pytest suite (vitest deferred). Real KG + sentence-transformer, mocked OpenAI client. Covers engine unit tests and FastAPI API integration tests.

---

## Context

Zero tests exist today. This suite bootstraps pytest infrastructure and covers the four changes made in the streaming bug-fix PR:
1. `OGEN_MODEL` env var replaces per-stage `model_config`
2. `ChatRequest.context: str = "default"` (was missing → 500)
3. `UIRequest.context: str = "default"` passed to `engine.reason()`
4. `_chat_stream_event_generator` appends `[context_mode: {context}]` when non-default

---

## Strategy: Real KG, Mocked LLM (Option B)

- **pyoxigraph Store + sentence-transformer + real TTL**: loaded for real to test KG logic
- **openai.OpenAI + langchain ChatOpenAI + create_agent**: patched at module level before any import, so `main.py`'s module-level init never calls real APIs
- **No API key required**, no network calls, CI-safe

---

## Directory Structure

```
apps/server/
└── tests/
    ├── conftest.py     # session-level patches + fixtures
    ├── test_engine.py  # OgenEngine pure function unit tests
    └── test_api.py     # FastAPI endpoint integration tests
```

---

## Dependencies (`apps/server/pyproject.toml`)

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "httpx>=0.27",
]
```

Run with: `cd apps/server && uv run pytest tests/ -v`

---

## Section 1: `conftest.py`

### Import timing fix

`main.py` creates `engine`, `llm`, and `agent` at **module import time**. Patching after import is too late. Solution: patch at the top of `conftest.py` before any other import, so the patches are active when `main` is first imported by any test.

```python
# conftest.py — top of file, before any other imports
import os, sys
os.environ.setdefault("OPENAI_API_KEY", "test-key")

from unittest.mock import MagicMock, patch

# Patch heavy deps before main.py is ever imported
patch("openai.OpenAI", return_value=MagicMock()).start()
patch("langchain_openai.ChatOpenAI", return_value=MagicMock()).start()
patch("langchain.agents.create_agent", return_value=MagicMock()).start()
```

### Fixtures

```python
import pytest
from fastapi.testclient import TestClient

@pytest.fixture(scope="session")
def engine(tmp_path_factory):
    """Real KG + real sentence-transformer. OpenAI already mocked above.
    scope=session: sentence-transformer loads once (~5s), shared across all tests.
    Tests MUST treat this as read-only to avoid KG state leaks."""
    from ogen_stream.engine import OgenEngine
    tmp_dir = tmp_path_factory.mktemp("ogen_data")
    return OgenEngine(openai_api_key="test-key", persistence_dir=str(tmp_dir))


@pytest.fixture
def client(engine):
    """FastAPI TestClient with real engine, mocked agent.
    Swaps module-level globals after import (safe because patches above
    prevented real init at import time)."""
    from main import app
    import main as m
    m.engine = engine
    m.agent = MagicMock()
    with TestClient(app) as c:
        yield c
```

**Why `tmp_path_factory`**: avoids the shared `/tmp/ogen_test_data` contamination risk flagged by Codex. Each session gets a unique temp dir.

**Why read-only engine**: tests that call `/api/connect` would mutate the shared engine's KG store. Such tests must either use `engine` as a fresh fixture scope or mock `engine.connect_user_data`.

---

## Section 2: `test_engine.py` — Unit Tests

All tests call methods directly on the `engine` fixture. No HTTP involved.

### OGEN_MODEL env var

```python
def test_model_default(engine):
    """OGEN_MODEL unset → defaults to gpt-5."""
    assert engine.model == os.environ.get("OGEN_MODEL", "gpt-5")

def test_model_from_env(tmp_path, monkeypatch):
    """OGEN_MODEL set → new engine picks it up.
    Uses fresh engine (not session fixture) to avoid module cache issues."""
    monkeypatch.setenv("OGEN_MODEL", "gpt-4o")
    # Remove cached module so __init__ re-reads os.getenv
    sys.modules.pop("ogen_stream.engine", None)
    from ogen_stream.engine import OgenEngine
    eng = OgenEngine(openai_api_key="test-key", persistence_dir=str(tmp_path))
    assert eng.model == "gpt-4o"
```

### `_validate_ui_tree`

```python
ALLOWED = {"Button", "Card", "Input"}
SCHEMA_MAP = {
    "Button": {
        "type": "object",
        "properties": {"label": {"type": "string"}},
        "required": ["label"],
    }
}

def test_validate_valid_tree(engine):
    node = {"type": "Button", "props": {"label": "Click"}, "children": []}
    assert engine._validate_ui_tree(node, ALLOWED, SCHEMA_MAP) == []

def test_validate_unknown_component(engine):
    node = {"type": "FakeWidget", "props": {}, "children": []}
    errors = engine._validate_ui_tree(node, ALLOWED, {})
    assert any("not included in AllowedComponentIds" in e for e in errors)

def test_validate_missing_props(engine):
    node = {"type": "Button", "children": []}
    errors = engine._validate_ui_tree(node, ALLOWED, SCHEMA_MAP)
    assert any("missing 'props'" in e for e in errors)

def test_validate_schema_violation(engine):
    node = {"type": "Button", "props": {"label": 123}, "children": []}
    errors = engine._validate_ui_tree(node, ALLOWED, SCHEMA_MAP)
    assert any("schema violation" in e for e in errors)

def test_validate_nested_invalid_child(engine):
    node = {
        "type": "Card",
        "props": {},
        "children": [{"type": "FakeWidget", "props": {}, "children": []}],
    }
    errors = engine._validate_ui_tree(node, ALLOWED, {})
    assert any("FakeWidget" in e for e in errors)
```

### `_build_component_schema_map`

```python
def test_build_schema_map_includes_components_with_schema(engine):
    children = [
        {"id": "Button", "propSchema": {"type": "object", "properties": {}}},
        {"id": "Card"},      # no propSchema → excluded
        "not_a_dict",        # ignored
    ]
    schema_map = engine._build_component_schema_map(children)
    assert "Button" in schema_map
    assert "Card" not in schema_map

def test_build_schema_map_empty(engine):
    assert engine._build_component_schema_map([]) == {}
```

### KG index loaded

```python
def test_index_built_from_ontology(engine):
    assert len(engine.nodes) > 0
    assert len(engine.node_embeddings) == len(engine.nodes)
```

---

## Section 3: `test_api.py` — API Integration Tests

### Pydantic model defaults (field omitted entirely)

```python
from main import ChatRequest, UIRequest

def test_chat_request_context_defaults_when_omitted():
    req = ChatRequest(**{"message": "hi"})
    assert req.context == "default"

def test_ui_request_context_defaults_when_omitted():
    req = UIRequest(**{"query": "hi"})
    assert req.context == "default"
```

### `/api/connect/status`

```python
def test_connect_status_returns_200(client):
    resp = client.get("/api/connect/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "connected" in data
    assert "node_count" in data
```

### `/generate-ui` — context_mode propagation

```python
def test_generate_ui_passes_default_context(client, engine):
    engine.reason = MagicMock(return_value={
        "generated_spec": {"type": "Button", "props": {}}
    })
    client.post("/generate-ui", json={"query": "make a button"})
    engine.reason.assert_called_once_with("make a button", context_mode="default")

def test_generate_ui_passes_nondefault_context(client, engine):
    engine.reason = MagicMock(return_value={
        "generated_spec": {"type": "Button", "props": {}}
    })
    client.post("/generate-ui", json={"query": "make a button", "context": "low-vision"})
    engine.reason.assert_called_once_with("make a button", context_mode="low-vision")
```

### `/chat/stream` POST — context suffix (Codex Q5: verifies bridge logic)

```python
def test_chat_stream_default_context_no_suffix(client):
    """context='default' → message unchanged, no [context_mode:] appended."""
    import main as m
    captured = []

    async def fake_astream(inputs, **kw):
        captured.append(inputs)
        yield {}

    m.agent.astream = fake_astream
    client.post("/chat/stream", json={"message": "hello", "context": "default"})
    content = captured[0]["messages"][0]["content"]
    assert content == "hello"
    assert "[context_mode:" not in content

def test_chat_stream_nondefault_context_appends_suffix(client):
    """context='low-vision' → [context_mode: low-vision] appended to message."""
    import main as m
    captured = []

    async def fake_astream(inputs, **kw):
        captured.append(inputs)
        yield {}

    m.agent.astream = fake_astream
    client.post("/chat/stream", json={"message": "hello", "context": "low-vision"})
    content = captured[0]["messages"][0]["content"]
    assert "[context_mode: low-vision]" in content

def test_chat_stream_post_returns_200(client):
    """POST /chat/stream previously 500d due to missing context field."""
    import main as m

    async def fake_astream(inputs, **kw):
        yield {}

    m.agent.astream = fake_astream
    resp = client.post("/chat/stream", json={"message": "hi", "context": "default"})
    assert resp.status_code == 200
```

---

## What Is NOT Tested (Deferred)

- `engine.reason()` end-to-end (requires LLM mock returning valid JSON)
- `engine.find_anchor_node_with_llm()` (LLM-dependent)
- `engine._agentic_filter_children()` (LLM-dependent)
- vitest / SvelteKit frontend tests
- Real SSE frame parsing from `/chat/stream` response body
