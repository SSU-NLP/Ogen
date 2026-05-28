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
