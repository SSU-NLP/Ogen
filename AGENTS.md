# AGENTS.md - Development Guidelines for Ogen-UI

This file contains essential information for agentic coding agents working in this repository.

## Project Overview

Ogen-UI is a monorepo containing an AI-driven UI generation system with:
- **Frontend**: SvelteKit 2 + TypeScript 5 + Vite 7
- **Backend**: FastAPI + Python 3.11+ with LangGraph/LangChain
- **Architecture**: Knowledge graph-driven UI generation using RDF/TTL ontology
- **Communication**: Server-Sent Events (SSE) for streaming chat interface

## Repository Structure

```
ogen-ui/
├── apps/
│   ├── front/          # SvelteKit frontend (port 5173)
│   └── server/         # FastAPI backend (port 8000)
├── packages/
│   ├── svelte/         # Custom UI library (@ogen/svelte)
│   ├── ogen_stream/    # Python streaming library
│   └── core/           # Shared code (currently empty)
├── pnpm-workspace.yaml # Node.js workspace config
├── pyproject.toml     # Python workspace config
└── start.sh           # Development startup script
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
  // Props with TypeScript types and defaults
  export let label: string = "Button";
  export let variant: 'primary' | 'secondary' = 'primary';
  
  // Imports: libraries first, then local with $lib alias
  import { onMount } from 'svelte';
  import Button from '$lib/components/Button.svelte';
  
  // Reactive statements
  $: isActive = variant === 'primary';
</script>

<!-- HTML with Svelte control flow -->
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

#### FastAPI Patterns
```python
# Error handling
try:
    result = engine.reason(request.query, context_mode=request.context)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

# Type hints for all function parameters and return values
def process_query(query: str, context_mode: str) -> Dict[str, Any]:
    """Process user query with context."""
    pass
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