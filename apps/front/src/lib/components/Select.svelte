<script lang="ts">
  export let label: string = "";
  export let options: string[] = [];
  export let value: string = "";
</script>

<div class="field">
  {#if label}
    <label>{label}</label>
  {/if}
  <select bind:value>
    {#each options as opt}
      <option value={opt}>{opt}</option>
    {/each}
  </select>
</div>

<style>
  .field { display: flex; flex-direction: column; gap: 6px; }
  label { font-size: 14px; color: #374151; font-weight: 600; }
  select {
    padding: 10px 12px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    font-size: 14px;
    background: #fff;
  }
</style>
