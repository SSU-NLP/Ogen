<script lang="ts">
  export let items: string[] = [];
</script>

<nav class="breadcrumbs">
  {#each items as item, i}
    <span>{item}</span>
    {#if i < items.length - 1}<span class="sep">/</span>{/if}
  {/each}
</nav>

<style>
  .breadcrumbs { display: flex; gap: 6px; font-size: 12px; color: #6b7280; }
  .sep { color: #9ca3af; }
</style>
