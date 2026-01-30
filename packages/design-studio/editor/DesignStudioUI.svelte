<script lang="ts">
  import type { ComponentMetadata, ComponentRegistry, StoryMap } from '../types';
  import { generateTTL } from '../generator';
  import { createEventDispatcher, onMount } from 'svelte';
  import ComponentPreview from './ComponentPreview.svelte';
  import OntologyGraph from './OntologyGraph.svelte';
  
  // Props
  export let registry: ComponentRegistry = {};
  export let metadata: Record<string, ComponentMetadata> = {};
  export let stories: StoryMap = {};
  export let backendUrl: string = 'http://localhost:8000';
  /** Optional file persistence endpoint (demo convenience). */
  export let fileApiUrl: string | null = null;
  
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
  let activeTab: 'preview' | 'graph' | 'ttl' = 'preview';
  let viewMode: 'studio' | 'ontology' = 'studio';
  let fileStatusMessage = '';
  let fileStatusKind: 'success' | 'error' | 'info' = 'info';
  let componentNames: string[] = [];

  let hasInitialized = false;

  $: componentNames = Object.keys(registry ?? {}).filter((k) => k !== 'default');
  
  // Reactive: Update TTL preview
  $: ttlPreview = generateTTL(editedMetadata);
  
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
    const ttl = generateTTL(editedMetadata);
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
      const ttl = generateTTL(editedMetadata);
      
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
  }

  function openOntology() {
    viewMode = 'ontology';
  }

  function openStudio() {
    viewMode = 'studio';
  }

  function editSelectedFromOntology() {
    viewMode = 'studio';
    activeTab = 'preview';
  }
  
  // Get current metadata for selected component
  $: currentMeta = selectedComponent ? editedMetadata[selectedComponent] : null;

  onMount(() => {
    if (!selectedComponent && componentNames.length > 0) {
      selectComponent(componentNames[0]);
    }
  });
</script>

<div class="design-studio">
  <header class="studio-header">
    <h1>Ogen Design Studio</h1>
    <div class="actions">
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
          selected={selectedComponent}
          on:select={handleGraphSelect}
        />

        <div class="ontology-side">
          <h2>Selected</h2>
          {#if selectedComponent && currentMeta}
            <div class="ontology-card">
              <div class="ontology-name">{selectedComponent}</div>
              <div class="ontology-label">{currentMeta.label}</div>
              <div class="ontology-desc">{currentMeta.comment}</div>
              <button class="btn-primary" on:click={editSelectedFromOntology}>Edit In Studio</button>
            </div>
          {:else}
            <div class="ontology-empty">Click a node to inspect it.</div>
          {/if}
        </div>
      </div>
    {:else}
    <!-- Component List -->
    <aside class="component-list">
      <h2>Components</h2>
      <ul>
        {#each componentNames as name}
          <li>
            <button 
              class="component-item"
              class:selected={selectedComponent === name}
              on:click={() => selectComponent(name)}
            >
              <span class="component-name">{name}</span>
              <span class="component-category">
                {editedMetadata[name]?.category ?? 'Unknown'}
              </span>
            </button>
          </li>
        {/each}
      </ul>
    </aside>
    
    <!-- Metadata Editor -->
    <main class="metadata-editor">
      {#if currentMeta}
        <h2>Edit: {selectedComponent}</h2>
        
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
        
        <h3>Ontology Relations</h3>
        
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
        
        <h3>Accessibility</h3>
        
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
    </main>
    
    <!-- Right Panel -->
    <aside class="right-panel">
      <div class="tab-bar">
        <button class:selected={activeTab === 'preview'} on:click={() => (activeTab = 'preview')}>Preview</button>
        <button class:selected={activeTab === 'ttl'} on:click={() => (activeTab = 'ttl')}>TTL</button>
      </div>

      {#if activeTab === 'preview'}
        <ComponentPreview
          componentName={selectedComponent}
          component={selectedComponent ? registry[selectedComponent] : null}
          metadata={currentMeta}
          variants={selectedComponent ? stories[selectedComponent] ?? [] : []}
        />
      {:else}
        <div class="ttl-preview">
          <h2>TTL Preview</h2>
          <pre><code>{ttlPreview}</code></pre>
        </div>
      {/if}
    </aside>
    {/if}
  </div>
</div>

<style>
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
    background: #1a1a2e;
    color: white;
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
    background: #10a37f;
    color: white;
  }
  
  .btn-secondary {
    background: #4a4a5a;
    color: white;
  }
  
  .btn-sync {
    background: #6366f1;
    color: white;
  }
  
  .status-bar {
    padding: 8px 24px;
    background: #fef3cd;
    color: #856404;
    font-size: 14px;
  }
  
  .status-bar.success {
    background: #d4edda;
    color: #155724;
  }
  
  .status-bar.error {
    background: #f8d7da;
    color: #721c24;
  }
  
  .studio-content {
    display: grid;
    grid-template-columns: 250px 1fr 420px;
    flex: 1;
    overflow: hidden;
  }

  .ontology-layout {
    grid-column: 1 / -1;
    display: grid;
    grid-template-columns: 1fr 320px;
    height: 100%;
    overflow: hidden;
  }

  .ontology-side {
    background: #11111b;
    border-left: 1px solid rgba(255, 255, 255, 0.08);
    padding: 16px;
    overflow: auto;
  }

  .ontology-side h2 {
    margin: 0 0 12px;
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #a6adc8;
  }

  .ontology-card {
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 12px;
    padding: 12px;
    background: rgba(255, 255, 255, 0.04);
  }

  .ontology-name {
    font-size: 13px;
    color: #cdd6f4;
    font-weight: 600;
  }

  .ontology-label {
    margin-top: 6px;
    font-size: 12px;
    color: #a6adc8;
  }

  .ontology-desc {
    margin-top: 10px;
    font-size: 13px;
    line-height: 1.35;
    color: #cdd6f4;
    opacity: 0.95;
  }

  .ontology-empty {
    font-size: 13px;
    color: #a6adc8;
  }
  
  .component-list {
    background: #f5f5f5;
    border-right: 1px solid #e0e0e0;
    overflow-y: auto;
  }
  
  .component-list h2 {
    padding: 16px;
    margin: 0;
    font-size: 14px;
    text-transform: uppercase;
    color: #666;
  }
  
  .component-list ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  
  .component-item {
    width: 100%;
    display: flex;
    justify-content: space-between;
    padding: 12px 16px;
    background: none;
    border: none;
    border-bottom: 1px solid #e0e0e0;
    text-align: left;
    cursor: pointer;
    transition: background 0.2s;
  }
  
  .component-item:hover {
    background: #e8e8e8;
  }
  
  .component-item.selected {
    background: #10a37f;
    color: white;
  }
  
  .component-name {
    font-weight: 500;
  }
  
  .component-category {
    font-size: 12px;
    opacity: 0.7;
  }
  
  .metadata-editor {
    padding: 24px;
    overflow-y: auto;
  }
  
  .metadata-editor h2 {
    margin: 0 0 24px;
    font-size: 18px;
  }
  
  .metadata-editor h3 {
    margin: 24px 0 16px;
    font-size: 14px;
    text-transform: uppercase;
    color: #666;
  }
  
  .form-group {
    margin-bottom: 16px;
  }
  
  .form-group label {
    display: block;
    margin-bottom: 4px;
    font-size: 14px;
    font-weight: 500;
    color: #333;
  }
  
  .form-group input,
  .form-group textarea,
  .form-group select {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #ccc;
    border-radius: 6px;
    font-size: 14px;
    font-family: inherit;
  }
  
  .form-group input:focus,
  .form-group textarea:focus,
  .form-group select:focus {
    outline: none;
    border-color: #10a37f;
  }
  
  .no-selection {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #888;
  }
  
  .right-panel {
    background: #1e1e2e;
    color: #cdd6f4;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  .tab-bar {
    display: flex;
    gap: 4px;
    padding: 8px;
    background: #181825;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }

  .tab-bar button {
    background: transparent;
    color: #cdd6f4;
    border: 1px solid rgba(255, 255, 255, 0.12);
    padding: 6px 10px;
    border-radius: 8px;
    font-size: 13px;
  }

  .tab-bar button.selected {
    background: rgba(16, 163, 127, 0.22);
    border-color: rgba(16, 163, 127, 0.5);
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
    color: #888;
    background: #181825;
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
