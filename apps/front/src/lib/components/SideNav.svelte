<script lang="ts">
  export let items: string[] = [];
</script>

<nav class="sidenav">
  {#each items as item}
    <div class="nav-item">{item}</div>
  {/each}
</nav>

<style>
  .sidenav { display: grid; gap: 8px; padding: 12px; border: 1px solid #e5e7eb; border-radius: 12px; background: #fff; }
  .nav-item { padding: 6px 8px; border-radius: 8px; background: #f3f4f6; font-size: 13px; }
</style>
