<script lang="ts">
  import type { ComponentMetadata, StoryVariant } from '../types';

  export let componentName: string | null = null;
  export let component: any = null;
  export let metadata: ComponentMetadata | null = null;
  export let variants: StoryVariant[] = [];
  export let props: Record<string, unknown> | null = null;
  export let externalSlotText: string | null = null;
  export let showHeader: boolean = true;
  export let showControls: boolean = true;
  export let showProps: boolean = true;

  let selectedVariant = 0;
  let propsDraft: Record<string, unknown> = {};
  let slotText: string = 'Preview content';
  let viewport: 'mobile' | 'tablet' | 'desktop' = 'desktop';

  $: if (variants.length > 0) {
    const v = variants[Math.min(selectedVariant, variants.length - 1)];
    propsDraft = { ...(v?.props ?? {}) };
    slotText = v?.slotText ?? 'Preview content';
  } else if (metadata?.propSchema) {
    // Seed with defaults from propSchema
    const seeded: Record<string, unknown> = {};
    for (const [key, schema] of Object.entries(metadata.propSchema)) {
      if (schema.default !== undefined) seeded[key] = schema.default;
    }
    propsDraft = seeded;
  } else {
    propsDraft = {};
  }

  function updateProp(key: string, value: unknown) {
    propsDraft = { ...propsDraft, [key]: value };
  }

  function frameWidth() {
    if (viewport === 'mobile') return '375px';
    if (viewport === 'tablet') return '768px';
    return '100%';
  }

  $: activeProps = props ?? propsDraft;
  $: activeSlotText = externalSlotText ?? slotText;
  $: previewColumns = showProps ? '1fr 220px' : '1fr';
</script>

<div class="preview-root">
  {#if showHeader}
    <div class="preview-header">
      <div class="title">
        <h2>Preview</h2>
        {#if componentName}
          <span class="chip">{componentName}</span>
        {/if}
      </div>

      {#if showControls}
        <div class="controls">
          <select bind:value={viewport}>
            <option value="desktop">Desktop</option>
            <option value="tablet">Tablet</option>
            <option value="mobile">Mobile</option>
          </select>

          {#if variants.length > 0}
            <select bind:value={selectedVariant}>
              {#each variants as v, i}
                <option value={i}>{v.name}</option>
              {/each}
            </select>
          {/if}
        </div>
      {/if}
    </div>
  {/if}

  <div class="preview-body" style:grid-template-columns={previewColumns}>
    <div class="frame" style:width={frameWidth()}>
      {#if component}
        <div class="canvas">
          <svelte:component this={component} {...activeProps}>
            {activeSlotText}
          </svelte:component>
        </div>
      {:else}
        <div class="empty">No component registered for preview.</div>
      {/if}
    </div>

    {#if showProps}
      <div class="props">
        <h3>Props</h3>
        {#if metadata?.propSchema && Object.keys(metadata.propSchema).length > 0}
          {#each Object.entries(metadata.propSchema) as [key, schema]}
            <div class="field">
              <label for={`prop-${key}`}>{key}</label>

              {#if schema.enum && schema.enum.length > 0}
                <select
                  id={`prop-${key}`}
                  value={String(propsDraft[key] ?? schema.default ?? '')}
                  on:change={(e) => updateProp(key, e.currentTarget.value)}
                >
                  {#each schema.enum as opt}
                    <option value={String(opt)}>{String(opt)}</option>
                  {/each}
                </select>
              {:else if schema.type === 'boolean'}
                <input
                  id={`prop-${key}`}
                  type="checkbox"
                  checked={Boolean(propsDraft[key] ?? schema.default ?? false)}
                  on:change={(e) => updateProp(key, e.currentTarget.checked)}
                />
              {:else}
                <input
                  id={`prop-${key}`}
                  type="text"
                  value={String(propsDraft[key] ?? schema.default ?? '')}
                  on:input={(e) => updateProp(key, e.currentTarget.value)}
                />
              {/if}

              {#if schema.description}
                <div class="hint">{schema.description}</div>
              {/if}
            </div>
          {/each}
        {:else}
          <div class="empty">No propSchema available. Provide stories/variants for richer preview.</div>
        {/if}
      </div>
    {/if}
  </div>
</div>

<style>
  .preview-root {
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  .preview-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-bottom: 1px solid var(--ds-border-soft);
    background: var(--ds-panel-2);
  }

  .title {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  h2 {
    margin: 0;
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--ds-muted);
  }

  .chip {
    font-size: 12px;
    padding: 2px 8px;
    border-radius: 999px;
    border: 1px solid var(--ds-border);
    color: var(--ds-text);
  }

  .controls {
    display: flex;
    gap: 8px;
  }

  .controls select {
    background: var(--ds-surface-2);
    border: 1px solid var(--ds-border);
    color: var(--ds-text);
    padding: 6px 10px;
    border-radius: 8px;
    font-size: 13px;
  }

  .preview-body {
    display: grid;
    grid-template-columns: 1fr 220px;
    gap: 12px;
    padding: 12px;
    flex: 1;
    overflow: hidden;
  }

  .frame {
    overflow: auto;
    border-radius: 12px;
    border: 1px solid var(--ds-border);
    background: var(--ds-surface);
  }

  .canvas {
    padding: 16px;
    min-height: 240px;
    color: var(--ds-preview-text, #111);
    background: var(--ds-preview-bg, linear-gradient(180deg, #ffffff 0%, #f6f6f9 100%));
    border-radius: 12px;
  }

  .props {
    overflow: auto;
    border-radius: 12px;
    border: 1px solid var(--ds-border);
    background: var(--ds-surface);
    padding: 12px;
  }

  .props h3 {
    margin: 0 0 10px;
    font-size: 12px;
    color: var(--ds-muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }

  .field {
    margin-bottom: 10px;
  }

  .field label {
    display: block;
    font-size: 12px;
    color: var(--ds-text);
    margin-bottom: 4px;
  }

  .field input[type='text'],
  .field select {
    width: 100%;
    font-size: 13px;
    padding: 6px 8px;
    border-radius: 8px;
    border: 1px solid var(--ds-border);
    background: var(--ds-surface-2);
    color: var(--ds-text);
  }

  .field input[type='checkbox'] {
    transform: translateY(1px);
  }

  .hint {
    font-size: 11px;
    color: var(--ds-muted);
    margin-top: 4px;
  }

  .empty {
    padding: 14px;
    font-size: 13px;
    color: var(--ds-muted);
  }
</style>
