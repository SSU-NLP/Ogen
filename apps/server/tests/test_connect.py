"""Tests for the front→backend knowledge-graph sync path (/api/connect).

Covers the robustness fixes:
- malformed TTL on the force-reconnect path surfaces as a clean 400 (ValueError),
  not an opaque 500;
- propSchema embedded as an escaped string literal round-trips through Turtle
  parsing back into a JSON object (the old triple-quoted long-string form
  corrupted JSON escape sequences).
"""
import json

import pytest

PREFIX = (
    "@prefix user: <http://myapp.com/ui/> .\n"
    "@prefix ogen: <http://ogen.ai/ontology/> .\n"
    "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
    "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n"
)


def _escape_ttl_string(s: str) -> str:
    """Mirror the design-studio generator's escapeString (TTL ECHAR escaping)."""
    return (
        s.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )


def _fresh_engine(tmp_path):
    from ogen_stream.engine import OgenEngine

    return OgenEngine(openai_api_key="test-key", persistence_dir=str(tmp_path))


# ---------------------------------------------------------------------------
# Malformed TTL → ValueError (→ HTTP 400)
# ---------------------------------------------------------------------------

def test_force_connect_malformed_ttl_raises_valueerror(tmp_path):
    """Force reconnect with unparseable TTL raises ValueError (not a raw parser
    error), so the API layer returns 400 instead of 500."""
    eng = _fresh_engine(tmp_path)
    with pytest.raises(ValueError):
        eng.connect_user_data("this is not valid turtle @@@", force=True)


def test_connect_malformed_ttl_returns_400(client):
    """POST /api/connect with malformed TTL → 400. Safe against the session
    engine: the rebuild fails before the atomic swap, leaving the store intact."""
    resp = client.post(
        "/api/connect",
        json={"ttl_content": "@@ not turtle @@", "base_iri": "http://myapp.com/ui/", "force": True},
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# propSchema escaped-literal round-trip
# ---------------------------------------------------------------------------

def test_propschema_escaped_literal_round_trips(tmp_path):
    """A propSchema with a newline and a quote, embedded the way the generator
    now does (escaped normal literal), parses back into a dict via json.loads."""
    prop_schema = {"label": {"type": "string", "default": 'a\nb"c'}}
    json_text = json.dumps(prop_schema, separators=(",", ":"))
    literal = _escape_ttl_string(json_text)

    ttl = PREFIX + (
        'user:Btn a ogen:Atom ;\n'
        '    rdfs:label "Btn" ;\n'
        f'    ogen:propSchema "{literal}"^^xsd:string .\n'
    )

    eng = _fresh_engine(tmp_path)
    eng.connect_user_data(ttl, force=True)

    props = eng._get_node_properties("http://myapp.com/ui/Btn")
    assert isinstance(props.get("propSchema"), dict)
    assert props["propSchema"]["label"]["default"] == 'a\nb"c'
