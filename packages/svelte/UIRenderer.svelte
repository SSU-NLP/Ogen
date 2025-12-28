<script lang="ts">
    import UIEngine from './UIRenderer.svelte';
  
    export let node: any; 
    export let components: Record<string, any> = {}; 

    $: Component = components[node.type] || components['default'] || null;
    $: props = node.props || {};
    $: safeProps = {
      ...props,
      label: node.label || props.label || node.type
    };
  </script>
  
  {#if Component}
    <svelte:component this={Component} {...safeProps}>
      {#if node.children && node.children.length > 0}
        {#each node.children as child}
          <UIEngine node={child} {components} />
        {/each}
      {/if}
    </svelte:component>
  {:else}
    <div style="border: 1px dashed red; padding: 10px; color: red;">
      🚫 Missing Component: {node.type}
    </div>
  {/if}