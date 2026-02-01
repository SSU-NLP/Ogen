<script lang="ts">
  import { createEventDispatcher, onMount, onDestroy } from 'svelte';
  import type cytoscape from 'cytoscape';
  import type { ComponentMetadata } from '../types';

export let metadata: Record<string, ComponentMetadata> = {};
export let registryKeys: string[] = [];
export let theme: 'light' | 'dark' = 'dark';
export let selected: string | null = null;

  const dispatch = createEventDispatcher<{ select: string }>();

  let containerEl: HTMLDivElement | null = null;
  let cy: cytoscape.Core | null = null;
  let lastGraphSignature: string = '';

  function computeGraphSignature(meta: Record<string, ComponentMetadata>): string {
    const registry = [...registryKeys].sort();
    const keys = Object.keys(meta).sort();
    const rel = keys.map((k) => {
      const m = meta[k];
      return [
        k,
        m?.label ?? '',
        [...(m?.hasPart ?? [])].sort(),
        [...(m?.requires ?? [])].sort(),
        [...(m?.recommends ?? [])].sort(),
        [...(m?.conflictsWith ?? [])].sort(),
        [...(m?.dependsOn ?? [])].sort()
      ];
    });
    return JSON.stringify({ registry, rel });
  }

  function buildElements(meta: Record<string, ComponentMetadata>) {
    const elements: cytoscape.ElementDefinition[] = [];

    const registryIdSet = new Set<string>(registryKeys);
    const nodeIds = new Set<string>([...Object.keys(meta), ...registryKeys]);

    // Also include missing targets referenced by relations so edges remain visible
    const missingTargets = new Set<string>();

    for (const [name, m] of Object.entries(meta)) {
      // Collect missing targets
      for (const relList of [m.hasPart, m.requires, m.recommends, m.conflictsWith, m.dependsOn]) {
        for (const t of relList ?? []) {
          if (t && !nodeIds.has(t)) missingTargets.add(t);
        }
      }
    }

    for (const t of missingTargets) {
      nodeIds.add(t);
    }

    // Nodes: union(registryKeys, metadata keys, missing targets)
    for (const id of nodeIds) {
      const hasMeta = Object.prototype.hasOwnProperty.call(meta, id);
      const isInRegistry = registryIdSet.has(id);
      const status = hasMeta && isInRegistry ? 'green' : isInRegistry ? 'gray' : 'red';
      const label = hasMeta ? (meta[id]?.label ?? id) : id;

      elements.push({
        data: {
          id,
          label,
          status
        }
      });
    }

    const addEdges = (from: string, rel: string, targets?: string[]) => {
      if (!targets) return;
      for (const t of targets) {
        if (!t) continue;

        // This view is "component graph only". Skip edges to nodes
        // that are not present in the component metadata set.
        if (!nodeIds.has(t)) {
          continue;
        }
        const edgeId = `${from}__${rel}__${t}`;
        elements.push({ data: { id: edgeId, source: from, target: t, rel } });
      }
    };

    for (const [name, m] of Object.entries(meta)) {
      addEdges(name, 'hasPart', m.hasPart);
      addEdges(name, 'requires', m.requires);
      addEdges(name, 'recommends', m.recommends);
      addEdges(name, 'conflictsWith', m.conflictsWith);
      addEdges(name, 'dependsOn', m.dependsOn);
    }

    return elements;
  }

  function applySelection(id: string | null) {
    if (!cy) return;
    cy.nodes().removeClass('selected');
    if (id && cy.getElementById(id).length) {
      cy.getElementById(id).addClass('selected');
    }
  }

  function applyThemeStyles(): void {
    if (!cy) return;
    const nodeText = theme === 'dark' ? '#cdd6f4' : '#111827';
    const edgeText = theme === 'dark' ? '#a6adc8' : '#374151';
    const edgeLine = theme === 'dark' ? '#6c7086' : '#9ca3af';

    cy.style()
      .selector('node')
      .style('color', nodeText)
      .update();
    cy.style()
      .selector('edge')
      .style('line-color', edgeLine)
      .style('target-arrow-color', edgeLine)
      .style('color', edgeText)
      .update();
  }

  onMount(async () => {
    if (!containerEl) return;
    // Lazy import to avoid SSR/runtime issues
    const cytoscapeModule = await import('cytoscape');
    const cytoscapeImpl = cytoscapeModule.default;

    const nodeText = theme === 'dark' ? '#cdd6f4' : '#111827';
    const edgeText = theme === 'dark' ? '#a6adc8' : '#374151';
    const edgeLine = theme === 'dark' ? '#6c7086' : '#9ca3af';

    cy = cytoscapeImpl({
      container: containerEl,
      elements: buildElements(metadata),
      layout: { name: 'breadthfirst', directed: true, padding: 20 },
      style: [
        {
          selector: 'node',
          style: {
            label: 'data(label)',
            color: nodeText,
            'font-size': '10px',
            'text-wrap': 'wrap',
            'text-max-width': '90px',
            'text-valign': 'center',
            'text-halign': 'center',
            width: '34px',
            height: '34px',
            'border-width': 2,
            'border-color': 'rgba(255,255,255,0.10)'
          }
        },
        {
          selector: 'node[status = "green"]',
          style: {
            'background-color': '#10a37f'
          }
        },
        {
          selector: 'node[status = "gray"]',
          style: {
            'background-color': '#6c7086'
          }
        },
        {
          selector: 'node[status = "red"]',
          style: {
            'background-color': '#b91c1c'
          }
        },
        {
          selector: 'node.selected',
          style: {
            'border-width': 4,
            'border-color': '#b7f4df'
          }
        },
        {
          selector: 'edge',
          style: {
            width: 2,
            'line-color': edgeLine,
            'target-arrow-color': edgeLine,
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            label: 'data(rel)',
            'font-size': '8px',
            color: edgeText,
            'text-rotation': 'autorotate'
          }
        }
      ]
    });

    cy.on('tap', 'node', (evt: cytoscape.EventObject) => {
      const id = evt.target.id();
      dispatch('select', id);
    });

    lastGraphSignature = computeGraphSignature(metadata);
    applySelection(selected);
    applyThemeStyles();
  });

  // Only rebuild elements/layout when the underlying graph changes.
  // Clicking a node updates `selected` and should NOT re-layout (prevents zoom/viewport jumps).
  $: if (cy) {
    const sig = computeGraphSignature(metadata);
    if (sig !== lastGraphSignature) {
      const zoom = cy.zoom();
      const pan = cy.pan();
      cy.json({ elements: buildElements(metadata) });
      cy.layout({ name: 'breadthfirst', directed: true, padding: 20 }).run();
      cy.zoom(zoom);
      cy.pan(pan);
      lastGraphSignature = sig;
    }
  }

  $: if (cy) {
    applySelection(selected);
  }

  $: if (cy) {
    applyThemeStyles();
  }

  onDestroy(() => {
    cy?.destroy();
    cy = null;
  });
</script>

<div class="graph-root">
  <div class="graph-header">
    <h2>Ontology Graph</h2>
    <button on:click={() => cy?.fit(undefined, 20)}>Fit</button>
  </div>
  <div class="graph-canvas" bind:this={containerEl}></div>
</div>

<style>
  .graph-root {
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  .graph-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    border-bottom: 1px solid var(--ds-border-soft);
    background: var(--ds-panel-2);
  }

  h2 {
    margin: 0;
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--ds-muted);
  }

  button {
    background: var(--ds-surface-2);
    border: 1px solid var(--ds-border);
    color: var(--ds-text);
    padding: 6px 10px;
    border-radius: 8px;
    font-size: 13px;
  }

  .graph-canvas {
    flex: 1;
    min-height: 320px;
    background: radial-gradient(1200px 600px at 20% 10%, rgba(203, 166, 247, 0.10), transparent 50%),
      radial-gradient(900px 500px at 80% 30%, rgba(16, 163, 127, 0.10), transparent 55%),
      var(--ds-bg);
  }
</style>
