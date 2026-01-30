<script lang="ts">
  import { onMount } from 'svelte';
  import { DesignStudioUI } from '@ogen/design-studio';
  import type { ComponentMetadata, StoryMap } from '@ogen/design-studio';
  
  import { designSystem, designSystemMetadata } from '$lib/ds';

  let metadata: Record<string, ComponentMetadata> = designSystemMetadata;
  let stories: StoryMap = {
    SubmitButton: [
      { name: 'Primary', props: { label: 'Submit', variant: 'primary' } },
      { name: 'Secondary', props: { label: 'Cancel', variant: 'secondary' } }
    ],
    EmailInput: [
      { name: 'Default', props: { label: 'Email', placeholder: 'user@example.com', type: 'email' } }
    ]
  };
  let isLoading = true;
  const fileApiUrl = '/api/design-studio/metadata';
  
  onMount(async () => {
    // Load persisted metadata from file API (dev convenience). Falls back to ds.ts.
    try {
      const res = await fetch(fileApiUrl);
      if (res.ok) {
        metadata = await res.json();
      }
    } catch {
      // ignore
    }

    isLoading = false;
  });
  
  function handleSave(event: CustomEvent<{ metadata: Record<string, ComponentMetadata>; ttl: string }>) {
    const { metadata: newMetadata, ttl } = event.detail;

    // Save to localStorage for chat page to consume
    localStorage.setItem('ogen_design_system_metadata', JSON.stringify(newMetadata));
    localStorage.setItem('ogen_design_system_hash', JSON.stringify(newMetadata));

    console.log('Saved metadata:', newMetadata);
    console.log('Generated TTL:', ttl);
    
    alert('Metadata saved successfully!');
  }
  
  function handleSync(event: CustomEvent<{ success: boolean; message: string }>) {
    const { success, message } = event.detail;
    
    if (success) {
      console.log('Sync successful:', message);
    } else {
      console.error('Sync failed:', message);
    }
  }

  function persistForChat(newMetadata: Record<string, ComponentMetadata>) {
    localStorage.setItem('ogen_design_system_metadata', JSON.stringify(newMetadata));
    localStorage.setItem('ogen_design_system_hash', JSON.stringify(newMetadata));
  }

  function handleFileSaved(event: CustomEvent<{ success: boolean; message: string }>) {
    if (event.detail.success) {
      persistForChat(metadata);
    }
  }

  function handleFileLoaded(event: CustomEvent<{ success: boolean; message: string }>) {
    if (event.detail.success) {
      persistForChat(metadata);
    }
  }
</script>

<svelte:head>
  <title>Design Studio | Ogen UI</title>
</svelte:head>

{#if isLoading}
  <div class="loading">
    <p>Loading components...</p>
  </div>
{:else}
  <DesignStudioUI 
    registry={designSystem}
    {metadata}
    {stories}
    backendUrl="http://localhost:8000"
    {fileApiUrl}
    on:save={handleSave}
    on:sync={handleSync}
    on:fileSaved={handleFileSaved}
    on:fileLoaded={handleFileLoaded}
  />
{/if}

<style>
  .loading {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100vh;
    font-size: 18px;
    color: #666;
  }
</style>
