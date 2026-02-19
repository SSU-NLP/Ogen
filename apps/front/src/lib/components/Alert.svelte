<script lang="ts">
  export let tone: 'info' | 'success' | 'warning' | 'danger' = 'info';
  export let message: string = "";
</script>

<div class={`alert ${tone}`}>
  <slot />{message}
</div>

<style>
  .alert { padding: 10px 12px; border-radius: 8px; font-size: 14px; }
  .info { background: #e0f2fe; color: #075985; }
  .success { background: #dcfce7; color: #166534; }
  .warning { background: #fef3c7; color: #92400e; }
  .danger { background: #fee2e2; color: #991b1b; }
</style>
