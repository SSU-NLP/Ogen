<script lang="ts">
  export let label: string = "";
</script>

<div class="group">
  {#if label}<label>{label}</label>{/if}
  <div class="row"><slot /></div>
</div>

<style>
  .group { display: flex; flex-direction: column; gap: 6px; }
  label { font-size: 14px; color: #374151; font-weight: 600; }
  .row { display: flex; gap: 8px; }
</style>
