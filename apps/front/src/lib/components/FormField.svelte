<script lang="ts">
  export let label: string = "";
  export let hint: string = "";
</script>

<div class="field">
  {#if label}<label>{label}</label>{/if}
  <slot />
  {#if hint}<div class="hint">{hint}</div>{/if}
</div>

<style>
  .field { display: flex; flex-direction: column; gap: 6px; }
  label { font-size: 14px; color: #374151; font-weight: 600; }
  .hint { font-size: 12px; color: #6b7280; }
</style>
