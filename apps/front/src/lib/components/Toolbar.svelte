<script lang="ts">
  export let title: string = "";
</script>

<div class="toolbar">
  <div class="title">{title}</div>
  <div class="actions"><slot /></div>
</div>

<style>
  .toolbar { display: flex; align-items: center; justify-content: space-between; padding: 10px 12px; border: 1px solid #e5e7eb; border-radius: 10px; background: #fff; }
  .title { font-size: 14px; font-weight: 600; }
  .actions { display: flex; gap: 8px; }
</style>
