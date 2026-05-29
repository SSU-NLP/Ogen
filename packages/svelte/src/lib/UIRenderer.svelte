<script lang="ts">
    import type { ComponentMetadata } from './ttl-generator';

    export let node: any;
    export let components: Record<string, any> = {};
    export let metadata: Record<string, ComponentMetadata> = {};

    $: Component = components[node?.type] || components['default'] || null;

    function applyDefaults(type: string, props: Record<string, any>): Record<string, any> {
      const meta = metadata[type];
      const schema = meta?.propSchema;
      if (!schema) return props;

      const next = { ...props };
      for (const [key, spec] of Object.entries(schema)) {
        if (next[key] === undefined && spec?.default !== undefined) {
          next[key] = spec.default;
        }
      }
      return next;
    }

    $: props = applyDefaults(node?.type, node?.props || {});
    $: meta = metadata[node?.type];
    $: safeProps = {
      ...props,
      label: node?.label || props.label || meta?.label || node?.type
    };
  </script>
  
  {#if Component}
    <svelte:component this={Component} {...safeProps}>
      {#if node.children && node.children.length > 0}
        {#each node.children as child}
          <svelte:self node={child} {components} {metadata} />
        {/each}
      {/if}
    </svelte:component>
  {:else}
    <div style="border: 1px dashed red; padding: 10px; color: red;">
      🚫 Missing Component: {node.type}
    </div>
  {/if}
