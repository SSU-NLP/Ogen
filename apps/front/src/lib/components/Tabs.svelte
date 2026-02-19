<script lang="ts">
  export let tabs: string[] = [];
  export let active: string = "";
</script>

<div class="tabs">
  {#each tabs as tab}
    <button class:selected={tab === active}>{tab}</button>
  {/each}
</div>

<style>
  .tabs { display: flex; gap: 8px; }
  button { padding: 6px 10px; border-radius: 8px; border: 1px solid #e5e7eb; background: #fff; }
  .selected { background: #2563eb; color: #fff; border-color: #2563eb; }
</style>
