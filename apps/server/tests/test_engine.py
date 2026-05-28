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
