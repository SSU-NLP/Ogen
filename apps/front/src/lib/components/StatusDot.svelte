<script lang="ts">
  export let status: 'online' | 'offline' | 'busy' = 'online';
</script>

<span class={`dot ${status}`}></span>

<style>
  .dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
  .online { background: #10b981; }
  .offline { background: #9ca3af; }
  .busy { background: #ef4444; }
</style>
