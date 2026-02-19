<script lang="ts">
  export let options: string[] = [];
</script>

<div class="group">
  {#each options as opt}
    <label><input type="checkbox" /> {opt}</label>
  {/each}
</div>

<style>
  .group { display: grid; gap: 6px; font-size: 14px; color: #374151; }
  label { display: flex; gap: 8px; align-items: center; }
</style>
