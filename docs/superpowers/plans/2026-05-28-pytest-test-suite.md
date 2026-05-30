# pytest Test Suite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bootstrap a pytest test suite for the FastAPI backend that verifies the four streaming bug-fix changes without making real LLM API calls.

**Architecture:** Three files under `apps/server/tests/`. `conftest.py` patches heavy deps at module level before any import so `main.py`'s module-level init never hits real APIs. `test_engine.py` tests pure functions directly on a real-KG engine fixture. `test_api.py` uses FastAPI `TestClient` with a captured `fake_astream` to verify the context-suffix bridge logic.

**Tech Stack:** pytest 8, pytest-asyncio, httpx, FastAPI TestClient, unittest.mock, pyoxigraph (real), sentence-transformers (real), openai (mocked).

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `apps/server/pyproject.toml` | Modify | Add `dev` optional-dependencies with pytest + httpx |
| `apps/server/tests/__init__.py` | Create | Empty — makes `tests/` a package |
| `apps/server/tests/conftest.py` | Create | Module-level patches, `engine` + `client` fixtures |
| `apps/server/tests/test_engine.py` | Create | Unit tests for `_validate_ui_tree`, `_build_component_schema_map`, `OGEN_MODEL` env var, KG index |
| `apps/server/tests/test_api.py` | Create | API tests for `/generate-ui`, `/api/connect/status`, `/chat/stream` |

---

## Task 1: pytest infrastructure

**Files:**
- Modify: `apps/server/pyproject.toml`
- Create: `apps/server/tests/__init__.py`
- Create: `apps/server/tests/conftest.py`

- [ ] **Step 1: Add dev dependencies to pyproject.toml**

Open `apps/server/pyproject.toml`. It currently looks like:

```toml
[project]
name = "ogen-server"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi",
    "uvicorn",
    "python-dotenv",
    "ogen-stream",
    "langgraph",
    "langchain-openai",
    "langchain-core",
    "sse-starlette",
]

[tool.uv.sources]
ogen-stream = { workspace = true }
```

Add the `dev` optional-dependencies block **after** the `[project]` section:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "httpx>=0.27",
]
```

- [ ] **Step 2: Install dev dependencies**

```bash
cd /Users/joseonghyeon/Ogen/apps/server
uv sync --extra dev
```

Expected: uv resolves and installs pytest, pytest-asyncio, httpx with no errors.

- [ ] **Step 3: Create `tests/` package**

```bash
mkdir -p /Users/joseonghyeon/Ogen/apps/server/tests
touch /Users/joseonghyeon/Ogen/apps/server/tests/__init__.py
```

- [ ] **Step 4: Create `conftest.py`**

Create `/Users/joseonghyeon/Ogen/apps/server/tests/conftest.py` with this exact content:

```python
# Module-level patches MUST come before any other import.
# main.py creates engine/llm/agent at module import time; patching here
# ensures those constructors see mocks when main is first imported by any test.
import os
import sys
os.environ.setdefault("OPENAI_API_KEY", "test-key")

from unittest.mock import MagicMock, patch

patch("openai.OpenAI", return_value=MagicMock()).start()
patch("langchain_openai.ChatOpenAI", return_value=MagicMock()).start()
patch("langchain.agents.create_agent", return_value=MagicMock()).start()

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def engine(tmp_path_factory):
    """Real pyoxigraph store + real sentence-transformer. OpenAI already mocked above.
    Session-scoped so the ~5s transformer load happens once per test run.
    Treat as READ-ONLY in all tests — mutations leak state to subsequent tests."""
    from ogen_stream.engine import OgenEngine

    tmp_dir = tmp_path_factory.mktemp("ogen_data")
    return OgenEngine(openai_api_key="test-key", persistence_dir=str(tmp_dir))


@pytest.fixture
def client(engine):
    """FastAPI TestClient backed by the session engine with a fresh MagicMock agent."""
    from main import app
    import main as m

    m.engine = engine
    m.agent = MagicMock()
    with TestClient(app) as c:
        yield c
```

- [ ] **Step 5: Verify pytest discovers the package**

```bash
cd /Users/joseonghyeon/Ogen/apps/server
uv run pytest tests/ --collect-only
```

Expected: output contains `<Module tests/conftest.py>` with no import errors. (No tests collected yet — that's fine.)

- [ ] **Step 6: Commit**

```bash
cd /Users/joseonghyeon/Ogen
git add apps/server/pyproject.toml apps/server/tests/__init__.py apps/server/tests/conftest.py
git commit -m "test: add pytest infrastructure and conftest fixtures"
```

---

## Task 2: Engine unit tests

**Files:**
- Create: `apps/server/tests/test_engine.py`

- [ ] **Step 1: Create `test_engine.py`**

Create `/Users/joseonghyeon/Ogen/apps/server/tests/test_engine.py`:

```python
import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# OGEN_MODEL env var
# ---------------------------------------------------------------------------

def test_model_default(engine):
    """OGEN_MODEL unset → engine.model is 'gpt-5'."""
    assert engine.model == os.environ.get("OGEN_MODEL", "gpt-5")


def test_model_from_env(tmp_path, monkeypatch):
    """OGEN_MODEL set before engine construction → engine.model picks it up.
    Uses a fresh engine (not session fixture) to avoid module cache interference.
    sys.modules.pop forces a clean re-import so os.getenv is evaluated again."""
    monkeypatch.setenv("OGEN_MODEL", "gpt-4o")
    sys.modules.pop("ogen_stream.engine", None)
    from ogen_stream.engine import OgenEngine

    eng = OgenEngine(openai_api_key="test-key", persistence_dir=str(tmp_path))
    assert eng.model == "gpt-4o"


# ---------------------------------------------------------------------------
# _validate_ui_tree
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# _build_component_schema_map
# ---------------------------------------------------------------------------

def test_build_schema_map_includes_with_schema(engine):
    children = [
        {"id": "Button", "propSchema": {"type": "object", "properties": {}}},
        {"id": "Card"},   # no propSchema → excluded
        "not_a_dict",     # ignored
    ]
    schema_map = engine._build_component_schema_map(children)
    assert "Button" in schema_map
    assert "Card" not in schema_map


def test_build_schema_map_empty(engine):
    assert engine._build_component_schema_map([]) == {}


# ---------------------------------------------------------------------------
# KG index
# ---------------------------------------------------------------------------

def test_index_built_from_ontology(engine):
    """Real TTL was loaded; index must be non-empty."""
    assert len(engine.nodes) > 0
    assert len(engine.node_embeddings) == len(engine.nodes)
```

- [ ] **Step 2: Run tests and verify they pass**

```bash
cd /Users/joseonghyeon/Ogen/apps/server
uv run pytest tests/test_engine.py -v
```

Expected output (all green):
```
tests/test_engine.py::test_model_default PASSED
tests/test_engine.py::test_model_from_env PASSED
tests/test_engine.py::test_validate_valid_tree PASSED
tests/test_engine.py::test_validate_unknown_component PASSED
tests/test_engine.py::test_validate_missing_props PASSED
tests/test_engine.py::test_validate_schema_violation PASSED
tests/test_engine.py::test_validate_nested_invalid_child PASSED
tests/test_engine.py::test_build_schema_map_includes_with_schema PASSED
tests/test_engine.py::test_build_schema_map_empty PASSED
tests/test_engine.py::test_index_built_from_ontology PASSED
```

If `test_model_from_env` fails with `AssertionError: assert 'gpt-5' == 'gpt-4o'`, check that `sys.modules.pop("ogen_stream.engine", None)` runs before the import inside the test. If `test_index_built_from_ontology` fails with 0 nodes, the TTL file path inside `OgenEngine.__init__` may not resolve correctly from the temp directory — check that `ogen-core.ttl` is bundled in the installed package.

- [ ] **Step 3: Commit**

```bash
cd /Users/joseonghyeon/Ogen
git add apps/server/tests/test_engine.py
git commit -m "test: add OgenEngine unit tests (model env var, validate_ui_tree, schema_map)"
```

---

## Task 3: API integration tests

**Files:**
- Create: `apps/server/tests/test_api.py`

- [ ] **Step 1: Create `test_api.py`**

Create `/Users/joseonghyeon/Ogen/apps/server/tests/test_api.py`:

```python
import pytest
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Pydantic model defaults — field omitted entirely (regression test)
# ---------------------------------------------------------------------------

def test_chat_request_context_defaults_when_omitted():
    """Omitting 'context' key entirely must default to 'default'.
    This was the bug: missing field caused AttributeError → 500."""
    from main import ChatRequest
    req = ChatRequest(**{"message": "hi"})
    assert req.context == "default"


def test_ui_request_context_defaults_when_omitted():
    from main import UIRequest
    req = UIRequest(**{"query": "hi"})
    assert req.context == "default"


# ---------------------------------------------------------------------------
# GET /api/connect/status
# ---------------------------------------------------------------------------

def test_connect_status_returns_200(client):
    resp = client.get("/api/connect/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "connected" in data
    assert "node_count" in data


# ---------------------------------------------------------------------------
# POST /generate-ui — context_mode propagation
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# POST /chat/stream — context suffix bridge logic (core regression tests)
# ---------------------------------------------------------------------------

def _install_fake_astream(captured: list):
    """Returns an async generator that records inputs and immediately ends."""
    async def fake_astream(inputs, **kw):
        captured.append(inputs)
        return
        yield  # make it an async generator

    return fake_astream


def test_chat_stream_post_returns_200(client):
    """POST /chat/stream previously 500d because ChatRequest had no context field."""
    import main as m
    captured = []
    m.agent.astream = _install_fake_astream(captured)
    resp = client.post("/chat/stream", json={"message": "hi", "context": "default"})
    assert resp.status_code == 200


def test_chat_stream_default_context_no_suffix(client):
    """context='default' → message content is unchanged, no [context_mode:] appended."""
    import main as m
    captured = []
    m.agent.astream = _install_fake_astream(captured)
    client.post("/chat/stream", json={"message": "hello", "context": "default"})

    assert len(captured) == 1, "agent.astream was not called"
    content = captured[0]["messages"][0]["content"]
    assert content == "hello"
    assert "[context_mode:" not in content


def test_chat_stream_nondefault_context_appends_suffix(client):
    """context='low-vision' → [context_mode: low-vision] must appear in message."""
    import main as m
    captured = []
    m.agent.astream = _install_fake_astream(captured)
    client.post("/chat/stream", json={"message": "hello", "context": "low-vision"})

    assert len(captured) == 1, "agent.astream was not called"
    content = captured[0]["messages"][0]["content"]
    assert "[context_mode: low-vision]" in content
```

- [ ] **Step 2: Run tests and verify they pass**

```bash
cd /Users/joseonghyeon/Ogen/apps/server
uv run pytest tests/test_api.py -v
```

Expected output (all green):
```
tests/test_api.py::test_chat_request_context_defaults_when_omitted PASSED
tests/test_api.py::test_ui_request_context_defaults_when_omitted PASSED
tests/test_api.py::test_connect_status_returns_200 PASSED
tests/test_api.py::test_generate_ui_passes_default_context PASSED
tests/test_api.py::test_generate_ui_passes_nondefault_context PASSED
tests/test_api.py::test_chat_stream_post_returns_200 PASSED
tests/test_api.py::test_chat_stream_default_context_no_suffix PASSED
tests/test_api.py::test_chat_stream_nondefault_context_appends_suffix PASSED
```

**Debugging tips:**

- If `test_chat_stream_default_context_no_suffix` fails with `len(captured) == 0`: the `client` fixture's `m.agent` was already replaced before `m.agent.astream = ...` in the test. Move the astream assignment before the `client.post(...)` call (it already is in the code above — double check the fixture yield order).
- If `test_generate_ui_passes_default_context` fails with `assert 'gpt-5' == ...`: `engine.reason` was not mocked. Check that `m.engine = engine` is in the `client` fixture and that the same `engine` instance is used.
- If any test fails with `ValidationError` on `ChatRequest` or `UIRequest`: the Pydantic model field is missing — this would be a regression in `main.py`.

- [ ] **Step 3: Run the full test suite**

```bash
cd /Users/joseonghyeon/Ogen/apps/server
uv run pytest tests/ -v
```

Expected: all 18 tests pass. First run takes ~5–10s for sentence-transformer load; subsequent runs are faster.

- [ ] **Step 4: Commit**

```bash
cd /Users/joseonghyeon/Ogen
git add apps/server/tests/test_api.py
git commit -m "test: add FastAPI API integration tests (context propagation, stream suffix)"
```

---

## Self-Review Notes

**Spec coverage:**
- `conftest.py` import timing fix → Task 1 Step 4 ✅
- `tmp_path_factory` for unique temp dirs → Task 1 Step 4 (engine fixture) ✅
- `OGEN_MODEL` default + env override → Task 2 (`test_model_default`, `test_model_from_env`) ✅
- `_validate_ui_tree` (5 cases) → Task 2 ✅
- `_build_component_schema_map` → Task 2 ✅
- KG index non-empty → Task 2 ✅
- Pydantic field omission regression → Task 3 ✅
- `/api/connect/status` → Task 3 ✅
- `/generate-ui` context propagation (default + non-default) → Task 3 ✅
- `/chat/stream` POST no-500 → Task 3 ✅
- `/chat/stream` no suffix on default → Task 3 ✅
- `/chat/stream` suffix on non-default → Task 3 ✅
