# Module-level patches MUST come before any other import.
# main.py creates engine/llm/agent at module import time; patching here
# ensures those constructors see mocks when main is first imported by any test.
import os
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
