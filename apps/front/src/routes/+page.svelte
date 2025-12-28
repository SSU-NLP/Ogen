<script lang="ts">
  import { onMount } from 'svelte';
  import { OgenRuntime, UIRenderer, type OgenState } from '@ogen/svelte';
  import { designSystem } from '$lib/ds';

  let query: string = "";
  let uiState: OgenState = { status: 'idle', tree: null, error: null };
  let engine: OgenRuntime;

  onMount(() => {
    engine = new OgenRuntime('http://localhost:8000/generate-ui');
    return engine.subscribe(state => uiState = state);
  });

  const handleGenerate = () => {
    if (!query.trim()) return;
    engine.execute(query);
  };
</script>
  
<div class="layout">
  <header>
    <h1>🎨 Design System Renderer</h1>
    <div class="input-box">
      <input 
        bind:value={query} 
        placeholder="Make a Login Form..." 
        on:keydown={(e) => e.key === 'Enter' && handleGenerate()}
      />
      <button on:click={handleGenerate}>Generate</button>
    </div>
  </header>

  <main>
    {#if uiState.tree}
      <UIRenderer 
        node={uiState.tree} 
        components={designSystem} 
      />
    {:else}
      <div class="empty">Waiting for Input...</div>
    {/if}
  </main>
</div>

<style>
  /* 스타일은 자유롭게 */
  .layout { padding: 40px; max-width: 800px; margin: 0 auto; }
  .input-box { display: flex; gap: 10px; margin-bottom: 20px; }
  input { flex: 1; padding: 10px; }
  .empty { border: 2px dashed #ccc; padding: 40px; text-align: center; color: #888; }
</style>