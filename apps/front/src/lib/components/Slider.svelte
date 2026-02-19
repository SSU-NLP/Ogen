<script lang="ts">
  export let label: string = "";
  export let value: number = 0;
  export let min: number = 0;
  export let max: number = 100;
</script>

<div class="slider-field">
  {#if label}<label>{label}</label>{/if}
  <input type="range" bind:value {min} {max} />
</div>

<style>
  .slider-field { display: flex; flex-direction: column; gap: 6px; }
  label { font-size: 14px; color: #374151; font-weight: 600; }
  input { width: 100%; }
</style>
