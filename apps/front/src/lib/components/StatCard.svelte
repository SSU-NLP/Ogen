<script lang="ts">
  export let label: string = "";
  export let value: string = "";
</script>

<div class="stat">
  <div class="label">{label}</div>
  <div class="value">{value}</div>
</div>

<style>
  .stat { padding: 12px; border: 1px solid #e5e7eb; border-radius: 12px; background: #fff; }
  .label { font-size: 12px; color: #6b7280; }
  .value { font-size: 20px; font-weight: 700; }
</style>
