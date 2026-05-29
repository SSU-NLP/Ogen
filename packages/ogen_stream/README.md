# ogen-stream

Ontology-grounded generative UI engine. `ogen-stream` turns natural-language
requests into **validated JSON UI specifications** by reasoning over an RDF/TTL
knowledge graph of design-system components.

It is the framework-agnostic core of [Ogen-UI](https://github.com/) — no web
framework is required to use it. A bundled Atomic-Design ontology
(`ogen-core.ttl`) ships with the package; you connect your own design-system
TTL on top.

## Install

```bash
pip install ogen-stream
# optional: LangChain tool wrapper for agentic use
pip install "ogen-stream[langchain]"
```

## Usage

```python
from ogen_stream.engine import OgenEngine

engine = OgenEngine(openai_api_key="sk-...")

# Connect your design-system knowledge graph (TTL produced by your authoring
# tool, e.g. @ogen/design-studio). Components are typed under ex:UIElement
# (ex:Atom / ex:Molecule / ex:Organism / ...) and linked via ex:hasPart.
engine.connect_user_data(ttl_string=my_design_system_ttl)

# Generate a UI spec for a request, grounded strictly in the connected graph.
result = engine.reason("a login form with email and password")
print(result["generated_spec"])
```

The engine is closed-world: it refuses to invent components that are not present
in the connected knowledge graph, returning an `error` dict instead.

## Pipeline

`OgenEngine.reason()` runs four stages: requirement analysis → anchor selection
(sentence-transformer embeddings + LLM) → subgraph retrieval with agentic
pruning over `ex:hasPart` → validated UI generation against per-component JSON
schemas (retried with repair feedback).

## Configuration

- `OPENAI_API_KEY` — required (or pass `openai_api_key=`).
- `OPENAI_BASE_URL` — optional, for OpenAI-compatible endpoints.
- `OGEN_MODEL` — optional, model used for all pipeline stages (default `gpt-5`).

## Streaming / LangChain

- `ogen_stream.stream` provides `StreamEvent` / `StreamEventType` and SSE
  helpers for streaming UIs.
- `ogen_stream.tools.create_langchain_tool(pipeline)` wraps the pipeline as a
  LangChain tool (requires the `langchain` extra).
