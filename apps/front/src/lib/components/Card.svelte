<script lang="ts">
  export let title: string = "";
  export let subtitle: string = "";
</script>

<div class="card">
  {#if title}
    <div class="card-header">
      <h3>{title}</h3>
      {#if subtitle}<p>{subtitle}</p>{/if}
    </div>
  {/if}
  <div class="card-body">
    <slot />
  </div>
</div>

<style>
  .card { border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px; background: #fff; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
  .card-header h3 { margin: 0; font-size: 16px; }
  .card-header p { margin: 4px 0 0; color: #6b7280; font-size: 12px; }
  .card-body { margin-top: 12px; }
</style>
