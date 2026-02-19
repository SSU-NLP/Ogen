<script lang="ts">
  export let title: string = "";
</script>

<div class="topnav">
  <div class="title">{title}</div>
  <div class="actions"><slot /></div>
</div>

<style>
  .topnav { display: flex; align-items: center; justify-content: space-between; padding: 12px; border-bottom: 1px solid #e5e7eb; background: #fff; }
  .title { font-weight: 600; }
  .actions { display: flex; gap: 8px; }
</style>
