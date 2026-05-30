# AGENTS.md - Development Guidelines for Ogen-UI

This file contains essential information for agentic coding agents working in this repository.

## Agent Instruction Ownership

`AGENTS.md` is the canonical source for shared agent instructions in this repository. Keep repository-wide rules, commands, architecture notes, and shared safety expectations here.

Tool-specific files should be thin adapters:

- `CLAUDE.md` imports this file for Claude Code and should only contain Claude-specific routing or exceptions.
- `.claude/` is reserved for Claude Code settings, skills, commands, hooks, and local permissions.
- `.agents/` stores shared agent assets such as reusable skills, hook scripts, templates, and cross-tool notes.
- If another agent needs hooks or settings, keep its native config file minimal and call scripts from `.agents/hooks/` instead of duplicating policy.

## Project Overview

Ogen-UI is a monorepo containing an AI-driven UI generation system with:
- **Frontend**: SvelteKit 2.49.1 + TypeScript 5.9.3 + Vite 7.2.6
- **Backend**: FastAPI + Python 3.11+ with LangGraph/LangChain
- **Architecture**: Knowledge graph-driven UI generation using RDF/TTL ontology
- **Communication**: Server-Sent Events (SSE) for streaming chat interface

## Repository Structure

```
ogen-ui/
├── apps/
│   ├── front/          # SvelteKit frontend demo (port 5173)
│   └── server/         # FastAPI backend (port 8000)
├── packages/
│   ├── svelte/         # @ogen/svelte - UI runtime library
│   ├── design-studio/  # @ogen/design-studio - Component metadata management
│   ├── ogen_stream/    # Python streaming library
│   └── core/           # Shared code (currently empty)
├── pnpm-workspace.yaml # Node.js workspace config
├── pyproject.toml      # Python workspace config (uv-based)
└── start.sh            # Development startup script
```

## Build/Test/Lint Commands

### Frontend (apps/front/)
```bash
# Development
pnpm dev              # Start dev server on port 5173
pnpm build            # Production build
pnpm preview          # Preview production build

# Type Checking
pnpm check            # Run svelte-check (TypeScript validation)
pnpm check:watch      # Watch mode type checking

# Package Management
pnpm install          # Install dependencies
pnpm prepare          # SvelteKit sync
```

### Backend (apps/server/)
```bash
# Development
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Package Management
uv sync              # Install dependencies
```

### Full Stack Development
```bash
./start.sh           # Start both frontend and backend servers
```

## Code Style Guidelines

### TypeScript/Svelte Conventions

#### Component Structure (Svelte 5 syntax)
```svelte
<script lang="ts">
  // 1. Props with TypeScript types and defaults
  export let label: string = "Button";
  export let variant: 'primary' | 'secondary' = 'primary';
  
  // 2. Imports: libraries first, then local with $lib alias
  import { onMount } from 'svelte';
  import Button from '$lib/components/Button.svelte';
  
  // 3. State variables
  let isLoading: boolean = false;
  
  // 4. Reactive statements
  $: isActive = variant === 'primary';
  
  // 5. Lifecycle hooks
  onMount(() => {
    // initialization
  });
</script>

<!-- HTML with Svelte 5 control flow -->
{#if Component}
  <Component {label} {variant} />
{:else}
  <div>Loading...</div>
{/if}

<style>
  /* Scoped CSS with component-specific classes */
  button {
    /* base styles */
  }
  
  .primary {
    /* variant styles */
  }
</style>
```

#### Type Definitions
```typescript
// Union types for status
type Status = 'idle' | 'loading' | 'error' | 'success';

// Interface definitions for all data structures
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  uiTree?: UITree;
  timestamp: Date;
  isStreaming?: boolean;
}

// Recursive tree structures
export type UITree = {
  type: string;
  props?: Record<string, any>;
  children?: UITree[];
} | null;
```

#### Import/Export Patterns
```typescript
// Library imports
import { onMount } from 'svelte';
import { OgentRuntime, UIRenderer } from '@ogen/svelte';

// Local imports with $lib alias
import { designSystem } from '$lib/ds';
import Button from '$lib/components/Button.svelte';

// Type exports
export type { ComponentMetadata } from './types';
```

### Python Conventions

#### Module Structure
```python
"""
Module docstring explaining purpose.
"""
from typing import Dict, Any, AsyncIterator, Optional
from pydantic import BaseModel, Field
from .engine import OgenEngine
from .stream import StreamEvent, StreamEventType

# Constants at module level
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

class ClassName:
    """Class docstring with Args and Returns."""
    
    def __init__(self, param: str):
        """
        Args:
            param: Parameter description
        """
        self.param = param
```

#### FastAPI Patterns
```python
# Error handling
try:
    result = engine.reason(request.query, context_mode=request.context)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
except ValidationError as e:
    raise HTTPException(status_code=422, detail=str(e))
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

# Type hints for all function parameters and return values
def process_query(query: str, context_mode: str) -> Dict[str, Any]:
    """Process user query with context.
    
    Args:
        query: User query string
        context_mode: Context mode (default, low-vision, etc.)
    
    Returns:
        Dict containing processed result
    """
    pass
```

#### Python Type Annotations
```python
# Use type hints for all function signatures
from typing import Dict, List, Optional, Union, Any

def fetch_data(
    uri: str,
    options: Optional[Dict[str, Any]] = None
) -> Union[Dict[str, Any], None]:
    """Function with explicit type annotations."""
    pass

# Use Pydantic for request/response models
from pydantic import BaseModel, Field

class UIRequest(BaseModel):
    query: str
    context: str = "default"
```

## Naming Conventions

### Files and Directories
- **Components**: PascalCase (Button.svelte, InputField.svelte)
- **Utilities**: camelCase (apiClient.ts, stringHelpers.ts)
- **Types**: camelCase with .types.ts extension (chat.types.ts)
- **Constants**: UPPER_SNAKE_CASE (API_ENDPOINTS.ts)

### Variables and Functions
- **Variables/Functions**: camelCase (getUserData, isLoading)
- **Classes**: PascalCase (UIRenderer, ChatManager)
- **Constants**: UPPER_SNAKE_CASE (MAX_RETRIES, DEFAULT_TIMEOUT)
- **Types/Interfaces**: PascalCase (ChatMessage, UITree)

### CSS Classes
- **Components**: kebab-case (button, input-field)
- **Modifiers**: BEM-style (button--primary, input-field--error)
- **Utilities**: utility-name (text-center, flex-row)

## Error Handling Patterns

### Frontend
```typescript
try {
  const data: ApiResponse = await res.json();
  if (data.error) {
    throw new Error(data.error);
  }
  this.setState({ status: 'success', tree: data.generated_spec });
} catch (error) {
  this.setState({ 
    status: 'error', 
    error: error instanceof Error ? error.message : String(error) 
  });
}
```

### Backend
```python
try:
    result = engine.reason(request.query, context_mode=request.context)
    return result
except ValidationError as e:
    raise HTTPException(status_code=422, detail=str(e))
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
```

## Testing

### Current Status
- No testing framework currently configured
- Recommend adding Vitest for frontend testing
- Recommend adding pytest for backend testing

### When Adding Tests
```bash
# Frontend (when Vitest is added)
pnpm test              # Run all tests
pnpm test Button       # Run single test file
pnpm test --watch      # Watch mode

# Backend (when pytest is added)
uv run pytest          # Run all tests
uv run pytest test_module.py::test_function  # Run single test
```

## Development Workflow

1. **Start Development**: Run `./start.sh` to start both servers
2. **Type Checking**: Run `pnpm check` before committing
3. **Package Management**: Use `pnpm` for frontend, `uv` for backend
4. **Hot Reload**: Both servers support hot reload during development

## Architecture Patterns

### Component System
- **Atomic Design**: Atoms, Molecules, Organisms
- **Metadata-Driven**: Components defined via RDF/TTL ontology
- **Dynamic Rendering**: UIRenderer component renders from metadata

### State Management
- **Observer Pattern**: Classes with `subscribe()` methods
- **Reactive State**: Svelte stores and reactive statements
- **Streaming State**: SSE for real-time updates

### API Patterns
- **RESTful Endpoints**: Standard HTTP methods
- **Streaming Responses**: Server-Sent Events for chat
- **Type Safety**: TypeScript interfaces for all API responses

## Important Notes

- Always run `pnpm check` before committing changes
- Use TypeScript strict mode - all types must be explicit
- Follow Svelte 5 syntax with modern `$props()` and control flow
- Backend uses Python 3.11+ with uv package manager
- Monorepo structure - shared code goes in `packages/`
- No existing rules files (.cursor, .cursorrules, .github/copilot-instructions.md)
- TTL files are loaded from `packages/ogen_stream/src/ogen_stream/ogen-core.ttl`
- Design Studio is now at `packages/design-studio/` (npm: @ogen/design-studio)
- Access Design Studio UI at: http://localhost:5173/design-studio

## System Architecture

Ogen is an **ontology-based generative UI engine**: a SvelteKit + FastAPI monorepo where the backend turns natural-language requests into JSON UI specs by reasoning over an RDF/TTL knowledge graph (KG) of design-system components.

Required env vars in `.env`: `OPENAI_API_KEY` (required), `OPENAI_BASE_URL` (optional, for OpenAI-compatible endpoints), `OGEN_MODEL` (optional, single model used for all pipeline stages, default: `gpt-5`).

Workspaces: `pyproject.toml` (uv) declares `apps/server` and `packages/ogen_stream`; `pnpm-workspace.yaml` covers `apps/*` and `packages/*`. The Python package is consumed via `[tool.uv.sources] ogen-stream = { workspace = true }`.

### KG-grounded reasoning pipeline (`packages/ogen_stream/src/ogen_stream/engine.py`)

`OgenEngine.reason()` is the heart of the system. It runs a 4-stage closed-world synthesis pipeline — **the engine refuses to invent components not present in the KG**, and returns an `error` dict instead of falling back. Any change to generation must preserve this guarantee.

1. **Requirement analysis** — LLM extracts intent, required components, and a suggested anchor name (`analyze_requirement`, model: `analysis`).
2. **Anchor selection** — sentence-transformer (`all-MiniLM-L6-v2`) embeds all node labels, top-K cosine candidates are passed to an LLM that picks one URI (`find_anchor_node_with_llm`, model: `anchor`).
3. **Subgraph retrieval with agentic pruning** — BFS from anchor over `ex:hasPart` edges (`get_subgraph_context`, max_depth=2). When a node has ≥3 children, or at depth 0, an LLM filters them down to those relevant to the user query (`_agentic_filter_children`, model: `pruning`).
4. **Validated UI generation** — LLM produces a UI tree (`_generate_ui_with_context`, model: `generation`) constrained to `AllowedComponentIds` from the retrieved subgraph; output is validated against per-component JSON Schemas with `Draft7Validator` and **retried up to 3 times** with validation errors fed back as repair feedback.

Default model: `gpt-5` for all pipeline stages. Override via `OGEN_MODEL` env var.

### Knowledge graph storage

- pyoxigraph `Store` holds two layers loaded into the default graph: the core ontology (`packages/ogen_stream/src/ogen_stream/ogen-core.ttl` — Atomic Design vocabulary) plus user-supplied design-system TTL.
- User TTL arrives via `POST /api/connect` and is persisted to `apps/server/ogen_data/user_graph.trig` (legacy `user_graph.ttl` is also read on startup). On `force=true` reconnect, `_rebuild_store_with_user_data` builds a new `Store` in isolation and atomically swaps it under a `threading.Lock` so the engine never sees a partially-loaded graph.
- After any load, `_build_index()` re-encodes node label embeddings for anchor search.
- Conventions for design-system TTL: nodes need `rdfs:label` to be indexed; parent→child links use `ex:hasPart`; generated component `id` is the URI fragment after `#` or last `/`. The frontend component registry must use that same id as its key.

### Server entrypoint (`apps/server/main.py`)

- Constructs `OgenEngine` once at startup, wraps `UIGenerationPipeline` in a LangChain tool (`create_langchain_tool`), and builds a LangGraph agent (`langchain.agents.create_agent`) over `ChatOpenAI(model="gpt-5")` with a system prompt that forbids inventing component types.
- The agent is the streaming path. `/chat/stream` (both GET and POST) calls `agent.astream(..., stream_mode="updates")` and re-emits SSE frames typed as `StreamEventType.{TEXT,UI,DONE,ERROR}` from `stream.py`. The bridge logic in `_chat_stream_event_generator` converts AI message deltas to `text` events and tool-result `ui_tree` payloads to `ui` events. EventSource (browser) requires GET.
- `POST /generate-ui` is the synchronous (non-agent) path that calls `engine.reason()` directly.

### Frontend (`apps/front`, `packages/svelte`)

- `@ogen/svelte` exports two runtimes: `OgenRuntime` (one-shot `/generate-ui`) and `OgentRuntime` (agentic chat over `/chat/stream`, with both `EventSource`-based `sendChatMessage` and fetch+streaming `sendMessage` paths). Both expose an Observer-style `subscribe(listener)` API.
- `UIRenderer.svelte` recursively renders the JSON UI tree by looking up `node.type` in a component registry passed from the app. The frontend's local design system lives in `apps/front/src/lib/components` with metadata in `apps/front/src/lib/design-studio.metadata.json` and `ds.ts`.
- `ttl-generator.ts` (in `@ogen/svelte`) and `@ogen/design-studio` together form a UI-side authoring loop: scan components → edit metadata → generate TTL → POST to `/api/connect`. The Design Studio UI is at `http://localhost:5173/design-studio`.

### Where to look when changing things

- Pipeline behavior, validation, pruning thresholds, model selection → `engine.py`.
- New SSE event types → `stream.py` + handlers in `main.py:_chat_stream_event_generator` + `OgentRuntime.handleStreamChunk` in `packages/svelte/index.ts`.
- New endpoints → `apps/server/main.py`. CORS is wide-open (`allow_origins=["*"]`) for dev.
- TTL ontology changes → `ogen-core.ttl`. After editing, restart the backend (it loads at construction time) and re-index will run automatically when user data is reloaded.

## Shared Skills

Portable agent skills live in `.agents/skills/<skill-name>/SKILL.md`. Codex reads this location directly. Claude Code project skills should point to shared skills from `.claude/skills/<skill-name>` with a symlink when the workflow is meant to be identical across agents.

Do not edit a symlinked `.claude/skills/<skill-name>` as if it were the source; edit the matching `.agents/skills/<skill-name>` directory instead. Claude-only skills may remain as real directories under `.claude/skills/`.

## Outstanding Work / Backlog

See `handoff.md` for the full, living handoff (recently completed + how to run/verify). Summary of what's left:

- **Design Studio – editing UX**: inline propSchema editor; relation field autocomplete + validation; replace the `prompt()` add-component flow; unsaved-changes guard.
- **Design Studio – layout/a11y**: responsive layout (fixed 3-col breaks <~1000px); larger click targets; contrast/focus fixes.
- **Metadata/scanner**: reconcile the 3 sources of truth (`ds.ts` / `design-studio.metadata.json` dev-only / `localStorage`); the browser scanner is unused.
- **Ontology/engine**: canonicalize `ogen-core.ttl` to Atomic Design (add Page level; split Action/Container out of the level taxonomy; align `ComponentCategory`); make traversal level-aware; batch the N+1 SPARQL in subgraph retrieval.
- **Chat/backend**: persistent memory (SQLite checkpointer; current `InMemorySaver` is lost on restart); markdown streaming edge cases.
- **Packaging**: libraries are publish-ready but not published; for independent publish, pin a released `ogen-stream` version in `apps/server/pyproject.toml`.
- **Testing**: add a frontend test framework (Vitest) for `OgentRuntime` stream/segment logic.
- **Housekeeping**: add `@types/node` (apps/front metadata route + design-studio scanner); decide on committing untracked infra (`.agents/`, `.claude/`, `CLAUDE.md`, `docs/superpowers/`); remove the stale `CLAUDE.md.pre-agent-unifier.bak`; push `main` to origin.
