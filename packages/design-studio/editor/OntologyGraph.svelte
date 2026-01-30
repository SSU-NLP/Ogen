<script lang="ts">
  import { createEventDispatcher, onMount, onDestroy } from 'svelte';
  import type cytoscape from 'cytoscape';
  import type { ComponentMetadata } from '../types';

  export let metadata: Record<string, ComponentMetadata> = {};
  export let selected: string | null = null;

  const dispatch = createEventDispatcher<{ select: string }>();

  let containerEl: HTMLDivElement | null = null;
  let cy: cytoscape.Core | null = null;

  function buildElements(meta: Record<string, ComponentMetadata>) {
    const elements: cytoscape.ElementDefinition[] = [];

    const nodeIds = new Set<string>(Object.keys(meta));

    for (const [name, m] of Object.entries(meta)) {
      elements.push({
        data: {
          id: name,
          label: m.label ?? name,
          category: m.category ?? 'Unknown'
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

  onMount(async () => {
    if (!containerEl) return;
    // Lazy import to avoid SSR/runtime issues
    const cytoscapeModule = await import('cytoscape');
    const cytoscapeImpl = cytoscapeModule.default;

    cy = cytoscapeImpl({
      container: containerEl,
      elements: buildElements(metadata),
      layout: { name: 'breadthfirst', directed: true, padding: 20 },
      style: [
        {
          selector: 'node',
          style: {
            'background-color': '#4c4f69',
            label: 'data(label)',
            color: '#cdd6f4',
            'font-size': '10px',
            'text-wrap': 'wrap',
            'text-max-width': '90px',
            'text-valign': 'center',
            'text-halign': 'center',
            width: '34px',
            height: '34px'
          }
        },
        {
          selector: 'node.selected',
          style: {
            'background-color': '#10a37f',
            'border-width': 3,
            'border-color': '#b7f4df'
          }
        },
        {
          selector: 'edge',
          style: {
            width: 2,
            'line-color': '#6c7086',
            'target-arrow-color': '#6c7086',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            label: 'data(rel)',
            'font-size': '8px',
            color: '#a6adc8',
            'text-rotation': 'autorotate'
          }
        }
      ]
    });

    cy.on('tap', 'node', (evt: cytoscape.EventObject) => {
      const id = evt.target.id();
      dispatch('select', id);
    });

    applySelection(selected);
  });

  $: if (cy) {
    cy.json({ elements: buildElements(metadata) });
    cy.layout({ name: 'breadthfirst', directed: true, padding: 20 }).run();
    applySelection(selected);
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
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    background: #181825;
  }

  h2 {
    margin: 0;
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #a6adc8;
  }

  button {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: #cdd6f4;
    padding: 6px 10px;
    border-radius: 8px;
    font-size: 13px;
  }

  .graph-canvas {
    flex: 1;
    min-height: 320px;
    background: radial-gradient(1200px 600px at 20% 10%, rgba(203, 166, 247, 0.10), transparent 50%),
      radial-gradient(900px 500px at 80% 30%, rgba(16, 163, 127, 0.10), transparent 55%),
      #0f111a;
  }
</style>
