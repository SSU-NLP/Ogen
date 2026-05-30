# Handoff — Ogen-UI

Living handoff doc: what recently landed and what's left. Update as work moves.
Last updated: 2026-05-30.

## Recently completed (this work stream)

- **Engine hygiene**: removed dead SPARQL in `is_user_data_loaded`, vestigial
  `GRAPH_*` NamedNode constants, unused imports; BFS queue → `collections.deque`.
- **Anchor index fix**: `_build_index` now indexes only `ex:UIElement`-subtree
  nodes (`?s a/rdfs:subClassOf* ex:UIElement`), excluding the ~34 RDF property
  definitions that were polluting anchor search.
- **Publishable libraries**:
  - `ogen_stream` → clean PyPI wheel (added `[build-system]`, README, trimmed
    deps to what's imported + `pydantic`, `langchain` optional extra, `.ttl`
    shipped as wheel artifact).
  - `@ogen/svelte` & `@ogen/design-studio` → built with `@sveltejs/package`
    (`src/lib/` layout, `svelte.config.js`, `dist/` output, `exports`/`files`).
- **Design Studio sync robustness**: TTL generator escapes all fields, validates
  component/relation names + category (skips bad items into `warnings[]` instead
  of breaking the whole graph), safe propSchema embedding; backend force-reconnect
  raises `ValueError` → clean **400** (not 500); `handleSync` timeout + clear errors.
- **Studio rendering**: `ComponentPreview` error boundary + aliasing notice;
  `OntologyGraph` readable labels + auto fit-to-view.
- **Chat UI**: one assistant message per turn with ordered `segments` (text/UI
  interleave, single avatar); conversation memory via backend `InMemorySaver` +
  per-session `thread_id`; Markdown rendering (marked + DOMPurify, SSR-guarded);
  persistent welcome; shimmering "Responding…" indicator; system prompt no longer
  dumps the UI spec/JSON.
- **Config discoverability**: `.env.example` documents `OPENAI_BASE_URL` /
  `OGEN_MODEL` (uncommitted at time of writing).

Backend tests: `cd apps/server && uv run pytest -q` → **24 passing**.

## Remaining work

### Design Studio (editing UX)
- Inline **propSchema editor** (currently read-only; requires export→edit JSON→import).
- Relation fields (`hasPart`/`requires`/…): **autocomplete + validation** against
  known component ids (currently brittle comma-separated free text).
- Replace the browser **`prompt()`** add-component flow with a proper form.
- **Unsaved-changes guard** before navigation/reload.

### Design Studio (layout / a11y)
- Responsive layout (fixed 3-column breaks below ~1000px).
- Larger click targets; fix low-contrast muted text; add focus rings.

### Metadata sources / scanner
- Reconcile the **3 sources of truth**: `apps/front/src/lib/ds.ts` defaults,
  `design-studio.metadata.json` (dev-only disk), and `localStorage`.
- Browser scanner is **unused** (Node `fs`/`path`); either wire an upload-based
  flow or drop it.

### Ontology / engine
- Canonicalize `ogen-core.ttl` to Atomic Design: add the **Page** level; split
  `Action`/`Container` out of the level taxonomy (they're roles, not levels);
  align design-studio `ComponentCategory` (currently missing Page, includes Container).
- Make engine traversal **Atomic-Design-level aware** (currently the classes are
  defined but unused in BFS/depth logic). **Prior art to port**: an earlier
  (Feb 2026) line implemented category/hierarchy-aware indexing + candidate
  re-ranking (KAPING, `Template > Organism > Molecule > Atom` boost) in
  `engine.py`. It was superseded by the current main but preserved on
  `origin/archive/2026-02-engine-line` (tip `f8f7836`); see commit `c87ae91`.
  Note that line also deleted `ogen-core.ttl` and moved the ontology to
  `apps/server/data/knowledge.ttl` — port the indexing idea, not that layout.
- Perf: **N+1 SPARQL batching** in subgraph retrieval (`_get_node_properties` /
  `_get_children` query per node).

### Chat / backend
- **Persistent memory**: `InMemorySaver` is dev-scoped (lost on restart) → optional
  SQLite checkpointer for cross-restart conversations.
- Markdown streaming edge cases (partial/incomplete markdown mid-stream).

### Packaging / publish
- Libraries are publish-*ready* but not published. For independent publish,
  `apps/server/pyproject.toml` `[tool.uv.sources] ogen-stream = {workspace=true}`
  must pin a released version.
- Smoke-test the `ogen_stream` wheel in a fresh venv (`pip install dist/*.whl`;
  skipped so far due to heavy torch/sentence-transformers download).

### Testing
- No frontend test framework. Add **Vitest** and cover the `OgentRuntime`
  segment-accumulation / stream handling.

### Housekeeping
- ~~`@types/node` errors in apps/front metadata route + design-studio scanner~~
  **Done** — added `@types/node`; `pnpm check` passes clean in both packages.
- a11y label warnings in `apps/front/src/lib/components/*` (10 warnings; still open).
- ~~Loose/untracked: `.env.example`, `README.md`, `user_graph.trig`, `.bak`,
  `.agents/`, `.claude/`, `CLAUDE.md`, `docs/superpowers/`~~ **Done** —
  committed shared infra (AGENTS/CLAUDE/.agents + agent-workspace-unifier +
  claude-code-setup), handoff, and config docs; `user_graph.trig` untracked +
  gitignored as a runtime artifact; personal research skills and
  `.claude/settings.local.json`/`worktrees` gitignored; `.bak` already gone.
- ~~Push `main` to `origin`~~ **Done (2026-05-30)** — `origin/main` had a
  divergent **Feb 2026** line (7 commits built on the same base `506b2c1` but
  never pulled before the May work). Reconciled by **force-pushing the May line
  as canonical**; the Feb line is preserved at
  `origin/archive/2026-02-engine-line` (see Ontology/engine above for what to
  salvage). If resuming on another machine, `git pull` before new work to avoid
  re-diverging.

## How to run / verify
- Full stack: `./start.sh` (builds the npm packages, then runs backend :8000 +
  frontend :5173). Chat at `/`, Design Studio at `/design-studio`.
- Backend tests: `cd apps/server && uv run pytest -q`.
- Frontend type-check: `cd apps/front && pnpm check` (3 pre-existing `@types/node`
  errors are expected until that backlog item is done).
- Rebuild libs after editing `packages/*`: `pnpm -r --filter "./packages/*" build`.
- Env: `.env` needs `OPENAI_API_KEY`; optional `OPENAI_BASE_URL` (OpenAI-compatible
  endpoint) and `OGEN_MODEL`.
