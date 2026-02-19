<script lang="ts">
  export let options: string[] = [];
  export let group: string = "";
</script>

<div class="group">
  {#each options as opt}
    <label><input type="radio" bind:group /> {opt}</label>
  {/each}
</div>

<style>
  .group { display: grid; gap: 6px; font-size: 14px; color: #374151; }
  label { display: flex; gap: 8px; align-items: center; }
</style>
