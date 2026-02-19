<script lang="ts">
  export let value: number = 0;
</script>

<div class="bar">
  <div class="fill" style={`width:${Math.min(100, Math.max(0, value))}%`}></div>
</div>

<style>
  .bar { width: 100%; height: 8px; background: #e5e7eb; border-radius: 999px; overflow: hidden; }
  .fill { height: 100%; background: #10b981; }
</style>
