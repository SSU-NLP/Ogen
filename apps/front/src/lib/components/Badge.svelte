<script lang="ts">
  export let label: string = "Badge";
  export let tone: 'neutral' | 'success' | 'warning' | 'danger' = 'neutral';
</script>

<span class={`badge ${tone}`}>{label}</span>

<style>
  .badge { display: inline-flex; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; }
  .neutral { background: #e5e7eb; color: #111827; }
  .success { background: #d1fae5; color: #065f46; }
  .warning { background: #fef3c7; color: #92400e; }
  .danger { background: #fee2e2; color: #991b1b; }
</style>
