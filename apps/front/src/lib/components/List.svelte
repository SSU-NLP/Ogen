<script lang="ts">
  export let items: string[] = [];
</script>

<ul class="list">
  {#each items as item}
    <li>{item}</li>
  {/each}
  <slot />
</ul>

<style>
  .list { list-style: none; padding: 0; margin: 0; display: grid; gap: 8px; }
  li { padding: 8px 10px; border: 1px solid #e5e7eb; border-radius: 8px; }
</style>
