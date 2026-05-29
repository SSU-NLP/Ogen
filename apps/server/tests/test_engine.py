# ---------------------------------------------------------------------------
# OGEN_MODEL env var
# ---------------------------------------------------------------------------

def test_model_default(tmp_path, monkeypatch):
    """OGEN_MODEL unset → engine.model is 'gpt-5'.
    Hermetic: explicitly clear OGEN_MODEL (a developer's .env may set it) and use
    a fresh engine rather than the session fixture."""
    monkeypatch.delenv("OGEN_MODEL", raising=False)
    from ogen_stream.engine import OgenEngine

    eng = OgenEngine(openai_api_key="test-key", persistence_dir=str(tmp_path))
    assert eng.model == "gpt-5"


def test_model_from_env(tmp_path, monkeypatch):
    """OGEN_MODEL set before engine construction → engine.model picks it up.
    Uses a fresh engine (not session fixture) to avoid module cache interference."""
    monkeypatch.setenv("OGEN_MODEL", "gpt-4o")
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

SAMPLE_TTL = """
@prefix ex: <http://ogen.ai/ontology/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
<http://myapp.com/ui/Button> a ex:Atom ; rdfs:label "Button" ; ex:keywords "click, cta" .
<http://myapp.com/ui/Card> a ex:Molecule ; rdfs:label "Card" ;
    ex:hasPart <http://myapp.com/ui/Button> .
"""


def test_index_includes_components_excludes_properties(tmp_path):
    """Index must contain UI components but not the ontology's property defs.

    The core ontology gives rdfs:label to ~34 property definitions (onClick,
    hasPart, variant, ...). _build_index filters to the ex:UIElement subtree so
    those schema nodes stay out of the anchor candidate set.

    Uses a fresh engine (not the session fixture, which is READ-ONLY)."""
    from ogen_stream.engine import OgenEngine

    eng = OgenEngine(openai_api_key="test-key", persistence_dir=str(tmp_path))
    eng.load_user_data_from_string(SAMPLE_TTL)

    labels = {n["label"] for n in eng.nodes}
    assert {"Button", "Card"} <= labels          # real components indexed
    assert "onClick" not in labels               # property defs excluded
    assert "hasPart" not in labels
    assert "variant" not in labels
    assert len(eng.node_embeddings) == len(eng.nodes)
