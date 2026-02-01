<script lang="ts">
  import type { ComponentMetadata, ComponentRegistry, StoryMap } from '../types';
  import { generateTTLForRegistry } from '../generator';
  import { createEventDispatcher, onMount } from 'svelte';
  import ComponentPreview from './ComponentPreview.svelte';
  import OntologyGraph from './OntologyGraph.svelte';
  import { createDefaultMetadata } from '../types/utils';
  
  // Props
  export let registry: ComponentRegistry = {};
  export let metadata: Record<string, ComponentMetadata> = {};
  export let stories: StoryMap = {};
  export let backendUrl: string = 'http://localhost:8000';
  /** Optional file persistence endpoint (demo convenience). */
  export let fileApiUrl: string | null = null;
  /** Theme mode for Design Studio UI. */
  export let theme: 'system' | 'light' | 'dark' = 'system';
  export let persistTheme: boolean = true;
  
  const dispatch = createEventDispatcher<{
    save: { metadata: Record<string, ComponentMetadata>; ttl: string };
    sync: { success: boolean; message: string };
    select: { componentName: string };
    fileSaved: { success: boolean; message: string };
    fileLoaded: { success: boolean; message: string };
  }>();
  
  // State
  let selectedComponent: string | null = null;
  let editedMetadata: Record<string, ComponentMetadata> = {};
  let isDirty = false;
  let connectionStatus: 'disconnected' | 'connecting' | 'connected' | 'error' = 'disconnected';
  let statusMessage = '';
  let ttlPreview = '';
  let inspectorTab: 'controls' | 'metadata' | 'graph' | 'ttl' = 'controls';
  let viewMode: 'studio' | 'ontology' = 'studio';
  let fileStatusMessage = '';
  let fileStatusKind: 'success' | 'error' | 'info' = 'info';
  let componentNames: string[] = [];
  let navQuery: string = '';

  const THEME_STORAGE_KEY = 'ogen_design_studio_theme';
  let themeMode: 'system' | 'light' | 'dark' = theme;
  let effectiveTheme: 'light' | 'dark' = 'dark';

  let hasInitialized = false;

  $: componentNames = Object.keys(registry ?? {}).filter((k) => k !== 'default');
  $: currentVariants = selectedComponent ? stories[selectedComponent] ?? [] : [];

  $: appComponents = componentNames.filter((name) => {
    const cat = editedMetadata[name]?.category;
    return cat === 'Organism' || cat === 'Template' || cat === 'Container';
  });

  $: designComponents = componentNames.filter((name) => !appComponents.includes(name));

  $: filteredAppComponents = appComponents.filter((name) =>
    name.toLowerCase().includes(navQuery.toLowerCase())
  );

  $: filteredDesignComponents = designComponents.filter((name) =>
    name.toLowerCase().includes(navQuery.toLowerCase())
  );

  function computeEffectiveTheme(): 'light' | 'dark' {
    if (typeof window === 'undefined') return 'dark';
    if (themeMode === 'light' || themeMode === 'dark') return themeMode;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function setThemeMode(next: 'system' | 'light' | 'dark') {
    themeMode = next;
    effectiveTheme = computeEffectiveTheme();
    if (persistTheme && typeof window !== 'undefined') {
      localStorage.setItem(THEME_STORAGE_KEY, themeMode);
    }
  }
  
  // Reactive: Update TTL preview (registry-only; excludes metadata-only/red nodes)
  $: ttlPreview = generateTTLForRegistry(componentNames, editedMetadata);
  
  // Initialize from props once
  $: if (!hasInitialized) {
    editedMetadata = { ...metadata };
    hasInitialized = true;
  }

  // Track changes (after init)
  $: isDirty = hasInitialized && JSON.stringify(editedMetadata) !== JSON.stringify(metadata);
  
  function selectComponent(name: string) {
    selectedComponent = name;
    dispatch('select', { componentName: name });
  }

  // Preview state (storybook-like)
  let previewViewport: 'desktop' | 'tablet' | 'mobile' = 'desktop';
  let previewVariantIndex = 0;
  let previewProps: Record<string, unknown> = {};
  let previewSlotText = 'Preview content';

  function seedPreviewFromVariantsOrSchema(): void {
    if (!selectedComponent) return;
    if (currentVariants.length > 0) {
      const v = currentVariants[Math.min(previewVariantIndex, currentVariants.length - 1)];
      previewProps = { ...(v?.props ?? {}) };
      previewSlotText = v?.slotText ?? 'Preview content';
      return;
    }

    const schema = editedMetadata[selectedComponent]?.propSchema;
    if (schema) {
      const seeded: Record<string, unknown> = {};
      for (const [key, s] of Object.entries(schema)) {
        if (s.default !== undefined) seeded[key] = s.default;
      }
      previewProps = seeded;
    } else {
      previewProps = {};
    }
  }

  function updatePreviewProp(key: string, value: unknown) {
    previewProps = { ...previewProps, [key]: value };
  }
  
  function updateMetadata(field: keyof ComponentMetadata, value: unknown) {
    if (!selectedComponent) return;
    
    editedMetadata = {
      ...editedMetadata,
      [selectedComponent]: {
        ...editedMetadata[selectedComponent],
        [field]: value
      }
    };
  }
  
  function updateKeywords(value: string) {
    const keywords = value.split(',').map(k => k.trim()).filter(k => k);
    updateMetadata('keywords', keywords);
  }
  
  function updateRelation(relation: 'hasPart' | 'requires' | 'recommends', value: string) {
    const items = value.split(',').map(k => k.trim()).filter(k => k);
    updateMetadata(relation, items);
  }
  
  async function handleSave() {
    const ttl = generateTTLForRegistry(componentNames, editedMetadata);
    dispatch('save', { metadata: editedMetadata, ttl });
  }

  function downloadText(filename: string, content: string, mime: string) {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  function handleExportJson() {
    downloadText('design-system.metadata.json', JSON.stringify(editedMetadata, null, 2), 'application/json');
  }

  function handleExportTtl() {
    downloadText('design-system.ttl', ttlPreview, 'text/turtle');
  }

  // Ontology graph GUI actions
  let registryToAdd: string = '';
  let placeholderToAdd: string = '';
  let relType: 'hasPart' | 'requires' | 'recommends' | 'conflictsWith' | 'dependsOn' = 'hasPart';
  let relFrom: string = '';
  let relTo: string = '';

  $: registryAddOptions = componentNames.filter((n) => !Object.prototype.hasOwnProperty.call(editedMetadata, n));
  $: graphNodeIds = Array.from(new Set([...componentNames, ...Object.keys(editedMetadata)]));

  function ensureMetadata(id: string) {
    if (!Object.prototype.hasOwnProperty.call(editedMetadata, id)) {
      editedMetadata = { ...editedMetadata, [id]: createDefaultMetadata(id) };
    }
  }

  function addRegistryMetadata() {
    if (!registryToAdd) return;
    ensureMetadata(registryToAdd);
    registryToAdd = '';
  }

  function addPlaceholderMetadata() {
    const id = placeholderToAdd.trim();
    if (!id) return;
    ensureMetadata(id);
    placeholderToAdd = '';
  }

  function addRelationEdge() {
    const from = relFrom.trim();
    const to = relTo.trim();
    if (!from || !to || from === to) return;

    ensureMetadata(from);

    const current = editedMetadata[from];
    const existing = (current[relType] ?? []) as string[];
    const next = Array.from(new Set([...existing, to]));

    editedMetadata = {
      ...editedMetadata,
      [from]: {
        ...current,
        [relType]: next
      }
    };
  }

  function createMetadataForSelected() {
    if (!selectedComponent) return;
    ensureMetadata(selectedComponent);
  }

  async function handleImportJson(file: File | null) {
    if (!file) return;
    try {
      const text = await file.text();
      const parsed: unknown = JSON.parse(text);
      if (!parsed || typeof parsed !== 'object') {
        throw new Error('Invalid metadata JSON');
      }
      editedMetadata = parsed as Record<string, ComponentMetadata>;
      fileStatusKind = 'success';
      fileStatusMessage = 'Imported metadata JSON.';
    } catch (e) {
      fileStatusKind = 'error';
      fileStatusMessage = `Import failed: ${e instanceof Error ? e.message : String(e)}`;
    }
  }

  async function loadFromFileApi() {
    if (!fileApiUrl) return;
    fileStatusKind = 'info';
    fileStatusMessage = 'Loading metadata from file...';
    try {
      const res = await fetch(fileApiUrl);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      editedMetadata = data;
      fileStatusKind = 'success';
      fileStatusMessage = 'Loaded metadata from file.';
      dispatch('fileLoaded', { success: true, message: fileStatusMessage });
    } catch (e) {
      fileStatusKind = 'error';
      fileStatusMessage = `Load failed: ${e instanceof Error ? e.message : String(e)}`;
      dispatch('fileLoaded', { success: false, message: fileStatusMessage });
    }
  }

  async function saveToFileApi() {
    if (!fileApiUrl) return;
    fileStatusKind = 'info';
    fileStatusMessage = 'Saving metadata to file...';
    try {
      const res = await fetch(fileApiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ metadata: editedMetadata })
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
      fileStatusKind = 'success';
      fileStatusMessage = 'Saved metadata to file.';
      dispatch('fileSaved', { success: true, message: fileStatusMessage });
    } catch (e) {
      fileStatusKind = 'error';
      fileStatusMessage = `Save failed: ${e instanceof Error ? e.message : String(e)}`;
      dispatch('fileSaved', { success: false, message: fileStatusMessage });
    }
  }
  
  async function handleSync() {
    connectionStatus = 'connecting';
    statusMessage = 'Connecting to backend...';
    
    try {
      const ttl = generateTTLForRegistry(componentNames, editedMetadata);
      
      const response = await fetch(`${backendUrl}/api/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ttl_content: ttl,
          base_iri: 'http://myapp.com/ui/',
          force: true
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      }
      
      const data = await response.json();
      connectionStatus = 'connected';
      statusMessage = `Connected! ${data.node_count} nodes loaded.`;
      dispatch('sync', { success: true, message: statusMessage });
    } catch (error) {
      connectionStatus = 'error';
      statusMessage = `Error: ${error instanceof Error ? error.message : String(error)}`;
      dispatch('sync', { success: false, message: statusMessage });
    }
  }
  
  function handleReset() {
    editedMetadata = { ...metadata };
    isDirty = false;
  }

  function handleGraphSelect(e: CustomEvent<string>) {
    selectComponent(e.detail);
    relFrom = e.detail;
  }

  function openOntology() {
    viewMode = 'ontology';
  }

  function openStudio() {
    viewMode = 'studio';
  }

  function editSelectedFromOntology() {
    viewMode = 'studio';
    inspectorTab = 'controls';
  }
  
  // Get current metadata for selected component
  $: currentMeta = selectedComponent ? editedMetadata[selectedComponent] : null;

  onMount(() => {
    if (persistTheme) {
      const stored = localStorage.getItem(THEME_STORAGE_KEY);
      if (stored === 'system' || stored === 'light' || stored === 'dark') {
        themeMode = stored;
      } else {
        themeMode = theme;
      }
    } else {
      themeMode = theme;
    }

    effectiveTheme = computeEffectiveTheme();

    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const onChange = () => {
      if (themeMode === 'system') {
        effectiveTheme = computeEffectiveTheme();
      }
    };
    media.addEventListener('change', onChange);

    if (!selectedComponent && componentNames.length > 0) {
      selectComponent(componentNames[0]);
    }

    return () => {
      media.removeEventListener('change', onChange);
    };
  });

  $: if (selectedComponent) {
    seedPreviewFromVariantsOrSchema();
  }
</script>

<div class="design-studio" data-ogen-theme={effectiveTheme}>
  <header class="studio-header">
    <h1>Ogen Design Studio</h1>
    <div class="actions">
      <div class="theme-toggle">
        <label class="sr-only" for="ds-theme">Theme</label>
        <select id="ds-theme" value={themeMode} on:change={(e) => setThemeMode(e.currentTarget.value as 'system' | 'light' | 'dark')}>
          <option value="system">System</option>
          <option value="light">Light</option>
          <option value="dark">Dark</option>
        </select>
      </div>

      <button class="btn-secondary" on:click={openStudio} disabled={viewMode === 'studio'}>
        Studio
      </button>
      <button class="btn-secondary" on:click={openOntology} disabled={viewMode === 'ontology'}>
        Ontology Graph
      </button>

      <button class="btn-secondary" on:click={handleExportJson}>
        Export JSON
      </button>
      <label class="btn-secondary btn-file">
        Import JSON
        <input type="file" accept="application/json" on:change={(e) => handleImportJson(e.currentTarget.files?.[0] ?? null)} />
      </label>
      <button class="btn-secondary" on:click={handleExportTtl}>
        Export TTL
      </button>

      {#if fileApiUrl}
        <button class="btn-secondary" on:click={loadFromFileApi}>
          Load File
        </button>
        <button class="btn-secondary" on:click={saveToFileApi}>
          Save File
        </button>
      {/if}

      <button class="btn-secondary" on:click={handleReset} disabled={!isDirty}>
        Reset
      </button>
      <button class="btn-primary" on:click={handleSave} disabled={!isDirty}>
        Save
      </button>
      <button class="btn-sync" on:click={handleSync}>
        Sync to Backend
      </button>
    </div>
  </header>
  
  {#if statusMessage}
    <div class="status-bar" class:success={connectionStatus === 'connected'} class:error={connectionStatus === 'error'}>
      {statusMessage}
    </div>
  {/if}

  {#if fileStatusMessage}
    <div class="status-bar" class:success={fileStatusKind === 'success'} class:error={fileStatusKind === 'error'}>
      {fileStatusMessage}
    </div>
  {/if}
  
  <div class="studio-content">
    {#if viewMode === 'ontology'}
      <div class="ontology-layout">
        <OntologyGraph
          metadata={editedMetadata}
          registryKeys={componentNames}
          theme={effectiveTheme}
          selected={selectedComponent}
          on:select={handleGraphSelect}
        />

        <div class="ontology-side">
          <h2>Selected</h2>
          {#if selectedComponent}
            {@const isInRegistry = componentNames.includes(selectedComponent)}
            {@const hasMeta = !!currentMeta}

            <div class="ontology-card">
              <div class="ontology-name">{selectedComponent}</div>
              <div class="ontology-label">
                {#if currentMeta}{currentMeta.label}{:else}{selectedComponent}{/if}
              </div>
              <div class="ontology-desc">
                {#if currentMeta}{currentMeta.comment}{:else}No metadata yet.{/if}
              </div>

              <div class="ontology-badges">
                <span class="badge" class:green={isInRegistry && hasMeta} class:gray={isInRegistry && !hasMeta} class:red={!isInRegistry}>
                  {#if isInRegistry && hasMeta}green{:else if isInRegistry}gray{:else}red{/if}
                </span>
              </div>

              <div class="ontology-actions">
                {#if !hasMeta}
                  <button class="btn-secondary" on:click={createMetadataForSelected}>
                    Create Metadata
                  </button>
                {/if}
                <button class="btn-primary" on:click={editSelectedFromOntology}>Edit In Studio</button>
              </div>
            </div>
          {:else}
            <div class="ontology-empty">Click a node to inspect it.</div>
          {/if}

          <h2 style="margin-top: 20px;">Graph Actions</h2>

          <div class="ontology-form">
            <div class="row">
              <label for="ds-add-registry">Add metadata for registry component</label>
              <div class="row-inline">
                <select id="ds-add-registry" bind:value={registryToAdd}>
                  <option value="">Select...</option>
                  {#each registryAddOptions as opt}
                    <option value={opt}>{opt}</option>
                  {/each}
                </select>
                <button class="btn-secondary" on:click={addRegistryMetadata} disabled={!registryToAdd}>Add</button>
              </div>
            </div>

            <div class="row">
              <label for="ds-add-placeholder">Add placeholder component (metadata-only / red)</label>
              <div class="row-inline">
                <input id="ds-add-placeholder" type="text" placeholder="NewComponent" bind:value={placeholderToAdd} />
                <button class="btn-secondary" on:click={addPlaceholderMetadata} disabled={!placeholderToAdd.trim()}>Add</button>
              </div>
            </div>

            <div class="row">
              <label for="ds-rel-type">Create relation edge</label>
              <div class="row-inline">
                <select id="ds-rel-type" bind:value={relType}>
                  <option value="hasPart">hasPart</option>
                  <option value="requires">requires</option>
                  <option value="recommends">recommends</option>
                  <option value="conflictsWith">conflictsWith</option>
                  <option value="dependsOn">dependsOn</option>
                </select>
              </div>
              <div class="row-inline">
                <select aria-label="from" bind:value={relFrom}>
                  <option value="">from...</option>
                  {#each graphNodeIds as id}
                    <option value={id}>{id}</option>
                  {/each}
                </select>
                <select aria-label="to" bind:value={relTo}>
                  <option value="">to...</option>
                  {#each graphNodeIds as id}
                    <option value={id}>{id}</option>
                  {/each}
                </select>
              </div>
              <button class="btn-secondary" on:click={addRelationEdge} disabled={!relFrom || !relTo || relFrom === relTo}>Add Edge</button>
            </div>
          </div>
        </div>
      </div>
    {:else}
    <div class="studio-body">
      <aside class="nav">
        <div class="nav-search">
          <input
            type="text"
            placeholder="Find components"
            value={navQuery}
            on:input={(e) => (navQuery = e.currentTarget.value)}
          />
          <button class="btn-secondary" on:click={() => {
            const name = prompt('New component name');
            if (name) {
              ensureMetadata(name.trim());
              selectComponent(name.trim());
            }
          }}>
            +
          </button>
        </div>

        <div class="nav-section">
          <div class="nav-title">Application</div>
          <ul>
            {#each filteredAppComponents as name}
              <li>
                <button
                  class="nav-item"
                  class:selected={selectedComponent === name}
                  on:click={() => selectComponent(name)}
                >
                  <span class="nav-dot" data-status={componentNames.includes(name) && editedMetadata[name] ? 'green' : componentNames.includes(name) ? 'gray' : 'red'}></span>
                  <span class="nav-label">{name}</span>
                </button>
              </li>
            {/each}
          </ul>
        </div>

        <div class="nav-section">
          <div class="nav-title">Design System</div>
          <ul>
            {#each filteredDesignComponents as name}
              <li>
                <button
                  class="nav-item"
                  class:selected={selectedComponent === name}
                  on:click={() => selectComponent(name)}
                >
                  <span class="nav-dot" data-status={componentNames.includes(name) && editedMetadata[name] ? 'green' : componentNames.includes(name) ? 'gray' : 'red'}></span>
                  <span class="nav-label">{name}</span>
                </button>
              </li>
            {/each}
          </ul>
        </div>
      </aside>

      <main class="canvas">
        <div class="canvas-header">
          <div class="canvas-title">{selectedComponent ?? 'Select a component'}</div>
          <div class="canvas-meta">{currentMeta?.label ?? ''}</div>
        </div>
        <div class="canvas-frame">
          <ComponentPreview
            componentName={selectedComponent}
            component={selectedComponent ? registry[selectedComponent] : null}
            metadata={currentMeta}
            variants={currentVariants}
            props={previewProps}
            externalSlotText={previewSlotText}
            showHeader={false}
            showControls={false}
            showProps={false}
          />
        </div>
      </main>

      <aside class="inspector">
        <div class="inspector-tabs">
          <button class:selected={inspectorTab === 'controls'} on:click={() => (inspectorTab = 'controls')}>Controls</button>
          <button class:selected={inspectorTab === 'metadata'} on:click={() => (inspectorTab = 'metadata')}>Metadata</button>
          <button class:selected={inspectorTab === 'graph'} on:click={() => (inspectorTab = 'graph')}>Graph</button>
          <button class:selected={inspectorTab === 'ttl'} on:click={() => (inspectorTab = 'ttl')}>TTL</button>
        </div>

        <div class="inspector-body">
          {#if inspectorTab === 'controls'}
            <div class="control-section">
            <div class="control-row">
              <label for="control-viewport">Viewport</label>
              <select id="control-viewport" bind:value={previewViewport}>
                  <option value="desktop">Desktop</option>
                  <option value="tablet">Tablet</option>
                  <option value="mobile">Mobile</option>
                </select>
              </div>

              {#if currentVariants.length > 0}
                <div class="control-row">
                  <label for="control-variant">Variant</label>
                  <select id="control-variant" bind:value={previewVariantIndex} on:change={seedPreviewFromVariantsOrSchema}>
                    {#each currentVariants as v, i}
                      <option value={i}>{v.name}</option>
                    {/each}
                  </select>
                </div>
              {/if}

            <div class="control-row">
              <label for="control-slot">Slot Text</label>
              <input id="control-slot" type="text" bind:value={previewSlotText} />
            </div>
            </div>

            <div class="control-section">
              <div class="control-title">Props</div>
              {#if currentMeta?.propSchema && Object.keys(currentMeta.propSchema).length > 0}
                {#each Object.entries(currentMeta.propSchema) as [key, schema]}
                  <div class="control-row">
                    <label for={`control-prop-${key}`}>{key}</label>
                    {#if schema.enum && schema.enum.length > 0}
                      <select
                        id={`control-prop-${key}`}
                        value={String(previewProps[key] ?? schema.default ?? '')}
                        on:change={(e) => updatePreviewProp(key, e.currentTarget.value)}
                      >
                        {#each schema.enum as opt}
                          <option value={String(opt)}>{String(opt)}</option>
                        {/each}
                      </select>
                    {:else if schema.type === 'boolean'}
                      <select
                        id={`control-prop-${key}`}
                        value={String(Boolean(previewProps[key] ?? schema.default ?? false))}
                        on:change={(e) => updatePreviewProp(key, e.currentTarget.value === 'true')}
                      >
                        <option value="true">True</option>
                        <option value="false">False</option>
                      </select>
                    {:else}
                      <input
                        id={`control-prop-${key}`}
                        type="text"
                        value={String(previewProps[key] ?? schema.default ?? '')}
                        on:input={(e) => updatePreviewProp(key, e.currentTarget.value)}
                      />
                    {/if}
                  </div>
                {/each}
              {:else}
                <div class="empty">No propSchema available.</div>
              {/if}
            </div>
          {:else if inspectorTab === 'metadata'}
            <div class="metadata-panel">
              {#if currentMeta}
                <div class="form-group">
                  <label for="label">Label</label>
                  <input 
                    id="label"
                    type="text" 
                    value={currentMeta.label}
                    on:input={(e) => updateMetadata('label', e.currentTarget.value)}
                  />
                </div>

                <div class="form-group">
                  <label for="comment">Description</label>
                  <textarea 
                    id="comment"
                    rows="3"
                    value={currentMeta.comment}
                    on:input={(e) => updateMetadata('comment', e.currentTarget.value)}
                  ></textarea>
                </div>

                <div class="form-group">
                  <label for="keywords">Keywords (comma-separated)</label>
                  <input 
                    id="keywords"
                    type="text" 
                    value={currentMeta.keywords?.join(', ') ?? ''}
                    on:input={(e) => updateKeywords(e.currentTarget.value)}
                  />
                </div>

                <div class="form-group">
                  <label for="category">Category</label>
                  <select 
                    id="category"
                    value={currentMeta.category}
                    on:change={(e) => updateMetadata('category', e.currentTarget.value)}
                  >
                    <option value="Atom">Atom</option>
                    <option value="Molecule">Molecule</option>
                    <option value="Organism">Organism</option>
                    <option value="Template">Template</option>
                    <option value="Container">Container</option>
                  </select>
                </div>

                <div class="form-group">
                  <label for="hasPart">Has Part (comma-separated)</label>
                  <input 
                    id="hasPart"
                    type="text" 
                    value={currentMeta.hasPart?.join(', ') ?? ''}
                    on:input={(e) => updateRelation('hasPart', e.currentTarget.value)}
                  />
                </div>

                <div class="form-group">
                  <label for="requires">Requires (comma-separated)</label>
                  <input 
                    id="requires"
                    type="text" 
                    value={currentMeta.requires?.join(', ') ?? ''}
                    on:input={(e) => updateRelation('requires', e.currentTarget.value)}
                  />
                </div>

                <div class="form-group">
                  <label for="recommends">Recommends (comma-separated)</label>
                  <input 
                    id="recommends"
                    type="text" 
                    value={currentMeta.recommends?.join(', ') ?? ''}
                    on:input={(e) => updateRelation('recommends', e.currentTarget.value)}
                  />
                </div>

                <div class="form-group">
                  <label for="ariaLabel">ARIA Label</label>
                  <input 
                    id="ariaLabel"
                    type="text" 
                    value={currentMeta.ariaLabel ?? ''}
                    on:input={(e) => updateMetadata('ariaLabel', e.currentTarget.value)}
                  />
                </div>

                <div class="form-group">
                  <label for="role">Role</label>
                  <input 
                    id="role"
                    type="text" 
                    value={currentMeta.role ?? ''}
                    on:input={(e) => updateMetadata('role', e.currentTarget.value)}
                  />
                </div>
              {:else}
                <div class="no-selection">
                  <p>Select a component from the list to edit its metadata.</p>
                </div>
              {/if}
            </div>
          {:else if inspectorTab === 'graph'}
            <OntologyGraph
              metadata={editedMetadata}
              registryKeys={componentNames}
              theme={effectiveTheme}
              selected={selectedComponent}
              on:select={handleGraphSelect}
            />
          {:else}
            <div class="ttl-preview">
              <h2>TTL Preview</h2>
              <pre><code>{ttlPreview}</code></pre>
            </div>
          {/if}
        </div>
      </aside>
    </div>
    {/if}
  </div>
</div>

<style>
  .design-studio {
    --ds-text: #cdd6f4;
    --ds-muted: #a6adc8;
    --ds-bg: #0f111a;
    --ds-header-bg: #1a1a2e;
    --ds-panel: #11111b;
    --ds-panel-2: #181825;
    --ds-surface: rgba(255, 255, 255, 0.04);
    --ds-surface-2: rgba(255, 255, 255, 0.06);
    --ds-border: rgba(255, 255, 255, 0.12);
    --ds-border-soft: rgba(255, 255, 255, 0.08);
    --ds-accent: #10a37f;
    --ds-accent-2: rgba(16, 163, 127, 0.22);
    --ds-danger: #b91c1c;
    --ds-gray: #6c7086;
    --ds-warning-bg: #fef3cd;
    --ds-warning-text: #856404;
    --ds-success-bg: #d4edda;
    --ds-success-text: #155724;
    --ds-error-bg: #f8d7da;
    --ds-error-text: #721c24;
    --ds-preview-bg: linear-gradient(180deg, #ffffff 0%, #f6f6f9 100%);
    --ds-preview-text: #111111;

    color: var(--ds-text);
    background: var(--ds-bg);
  }

  .design-studio[data-ogen-theme='light'] {
    --ds-text: #111827;
    --ds-muted: #4b5563;
    --ds-bg: #f7f7fb;
    --ds-header-bg: #ffffff;
    --ds-panel: #ffffff;
    --ds-panel-2: #f3f4f6;
    --ds-surface: rgba(17, 24, 39, 0.04);
    --ds-surface-2: rgba(17, 24, 39, 0.06);
    --ds-border: rgba(17, 24, 39, 0.14);
    --ds-border-soft: rgba(17, 24, 39, 0.10);
    --ds-warning-bg: #fff4cc;
    --ds-warning-text: #7a5d00;
    --ds-success-bg: #e6f6ea;
    --ds-success-text: #0f5132;
    --ds-error-bg: #fce8e8;
    --ds-error-text: #842029;
    --ds-preview-bg: linear-gradient(180deg, #ffffff 0%, #f6f6f9 100%);
    --ds-preview-text: #111111;
  }

  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }

  .theme-toggle select {
    background: var(--ds-surface-2);
    border: 1px solid var(--ds-border);
    color: var(--ds-text);
    padding: 6px 10px;
    border-radius: 10px;
    font-size: 13px;
  }
  .design-studio {
    display: flex;
    flex-direction: column;
    height: 100vh;
    font-family: system-ui, -apple-system, sans-serif;
  }
  
  .studio-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 24px;
    background: var(--ds-header-bg);
    color: var(--ds-text);
    border-bottom: 1px solid var(--ds-border-soft);
  }
  
  .studio-header h1 {
    margin: 0;
    font-size: 20px;
  }
  
  .actions {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .btn-file {
    position: relative;
    overflow: hidden;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .btn-file input {
    position: absolute;
    inset: 0;
    opacity: 0;
    cursor: pointer;
  }
  
  button {
    padding: 8px 16px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: opacity 0.2s;
  }
  
  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .btn-primary {
    background: var(--ds-accent);
    color: #ffffff;
  }
  
  .btn-secondary {
    background: var(--ds-surface-2);
    color: var(--ds-text);
    border: 1px solid var(--ds-border);
  }
  
  .btn-sync {
    background: #6366f1;
    color: #ffffff;
  }
  
  .status-bar {
    padding: 8px 24px;
    background: var(--ds-warning-bg);
    color: var(--ds-warning-text);
    font-size: 14px;
  }
  
  .status-bar.success {
    background: var(--ds-success-bg);
    color: var(--ds-success-text);
  }
  
  .status-bar.error {
    background: var(--ds-error-bg);
    color: var(--ds-error-text);
  }
  
  .studio-content {
    flex: 1;
    overflow: hidden;
  }

  .studio-body {
    display: grid;
    grid-template-columns: 260px 1fr 320px;
    height: 100%;
  }

  .nav {
    background: var(--ds-panel);
    border-right: 1px solid var(--ds-border-soft);
    padding: 12px;
    overflow: auto;
  }

  .nav-search {
    display: flex;
    gap: 8px;
    margin-bottom: 12px;
  }

  .nav-search input {
    flex: 1;
    padding: 8px 10px;
    border: 1px solid var(--ds-border);
    border-radius: 10px;
    background: var(--ds-surface-2);
    color: var(--ds-text);
  }

  .nav-section + .nav-section {
    margin-top: 14px;
  }

  .nav-title {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--ds-muted);
    margin-bottom: 8px;
  }

  .nav-section ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .nav-item {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 10px;
    border-radius: 8px;
    border: 1px solid transparent;
    background: transparent;
    color: var(--ds-text);
    cursor: pointer;
    text-align: left;
  }

  .nav-item:hover {
    background: var(--ds-surface);
  }

  .nav-item.selected {
    background: var(--ds-accent-2);
    border-color: rgba(16, 163, 127, 0.4);
  }

  .nav-dot {
    width: 10px;
    height: 10px;
    border-radius: 999px;
    background: var(--ds-gray);
  }

  .nav-dot[data-status='green'] {
    background: var(--ds-accent);
  }

  .nav-dot[data-status='gray'] {
    background: var(--ds-gray);
  }

  .nav-dot[data-status='red'] {
    background: var(--ds-danger);
  }

  .canvas {
    background: var(--ds-bg);
    border-right: 1px solid var(--ds-border-soft);
    display: flex;
    flex-direction: column;
  }

  .canvas-header {
    padding: 16px;
    border-bottom: 1px solid var(--ds-border-soft);
  }

  .canvas-title {
    font-size: 16px;
    font-weight: 600;
    color: var(--ds-text);
  }

  .canvas-meta {
    margin-top: 4px;
    font-size: 12px;
    color: var(--ds-muted);
  }

  .canvas-frame {
    flex: 1;
    padding: 18px;
  }

  .inspector {
    background: var(--ds-panel);
    display: flex;
    flex-direction: column;
  }

  .inspector-tabs {
    display: flex;
    gap: 6px;
    padding: 8px 10px;
    background: var(--ds-panel-2);
    border-bottom: 1px solid var(--ds-border-soft);
  }

  .inspector-tabs button {
    background: transparent;
    color: var(--ds-text);
    border: 1px solid var(--ds-border);
    padding: 6px 10px;
    border-radius: 8px;
    font-size: 12px;
  }

  .inspector-tabs button.selected {
    background: var(--ds-accent-2);
    border-color: rgba(16, 163, 127, 0.5);
  }

  .inspector-body {
    padding: 12px;
    overflow: auto;
    flex: 1;
  }

  .control-section {
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--ds-border-soft);
  }

  .control-title {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--ds-muted);
    margin-bottom: 8px;
  }

  .control-row {
    display: grid;
    grid-template-columns: 1fr;
    gap: 6px;
    margin-bottom: 10px;
  }

  .control-row label {
    font-size: 12px;
    color: var(--ds-muted);
  }

  .control-row input,
  .control-row select {
    padding: 8px 10px;
    border: 1px solid var(--ds-border);
    border-radius: 8px;
    background: var(--ds-surface-2);
    color: var(--ds-text);
    font-size: 13px;
  }

  .ontology-layout {
    grid-column: 1 / -1;
    display: grid;
    grid-template-columns: 1fr 320px;
    height: 100%;
    overflow: hidden;
  }

  .ontology-side {
    background: var(--ds-panel);
    border-left: 1px solid var(--ds-border-soft);
    padding: 16px;
    overflow: auto;
  }

  .ontology-side h2 {
    margin: 0 0 12px;
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--ds-muted);
  }

  .ontology-card {
    border: 1px solid var(--ds-border);
    border-radius: 12px;
    padding: 12px;
    background: var(--ds-surface);
  }

  .ontology-name {
    font-size: 13px;
    color: var(--ds-text);
    font-weight: 600;
  }

  .ontology-label {
    margin-top: 6px;
    font-size: 12px;
    color: var(--ds-muted);
  }

  .ontology-desc {
    margin-top: 10px;
    font-size: 13px;
    line-height: 1.35;
    color: var(--ds-text);
    opacity: 0.95;
  }

  .ontology-empty {
    font-size: 13px;
    color: var(--ds-muted);
  }

  .ontology-badges {
    margin-top: 10px;
  }

  .badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    padding: 2px 8px;
    border-radius: 999px;
    border: 1px solid var(--ds-border);
    color: var(--ds-text);
    background: var(--ds-surface-2);
  }

  .badge.green {
    border-color: rgba(16, 163, 127, 0.55);
    background: rgba(16, 163, 127, 0.20);
  }

  .badge.gray {
    border-color: rgba(108, 112, 134, 0.8);
    background: rgba(108, 112, 134, 0.22);
  }

  .badge.red {
    border-color: rgba(185, 28, 28, 0.8);
    background: rgba(185, 28, 28, 0.22);
  }

  .ontology-actions {
    margin-top: 12px;
    display: flex;
    gap: 8px;
  }

  .ontology-form {
    margin-top: 10px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .ontology-form label {
    display: block;
    font-size: 12px;
    color: var(--ds-muted);
    margin-bottom: 6px;
  }

  .row-inline {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .ontology-form input,
  .ontology-form select {
    width: 100%;
    padding: 8px 10px;
    border: 1px solid var(--ds-border);
    border-radius: 10px;
    font-size: 13px;
    background: var(--ds-surface-2);
    color: var(--ds-text);
  }
  
  
  .form-group {
    margin-bottom: 16px;
  }
  
  .form-group label {
    display: block;
    margin-bottom: 4px;
    font-size: 14px;
    font-weight: 500;
    color: var(--ds-text);
  }
  
  .form-group input,
  .form-group textarea,
  .form-group select {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid var(--ds-border);
    border-radius: 6px;
    font-size: 14px;
    font-family: inherit;
    background: var(--ds-panel);
    color: var(--ds-text);
  }
  
  .form-group input:focus,
  .form-group textarea:focus,
  .form-group select:focus {
    outline: none;
    border-color: var(--ds-accent);
  }
  
  .no-selection {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #888;
  }
  

  .ttl-preview {
    overflow-y: auto;
    flex: 1;
  }

  .ttl-preview h2 {
    padding: 16px;
    margin: 0;
    font-size: 14px;
    text-transform: uppercase;
    color: var(--ds-muted);
    background: var(--ds-panel-2);
  }

  .ttl-preview pre {
    margin: 0;
    padding: 16px;
    font-size: 12px;
    font-family: 'Fira Code', 'Monaco', monospace;
    white-space: pre-wrap;
    word-break: break-all;
  }
</style>
