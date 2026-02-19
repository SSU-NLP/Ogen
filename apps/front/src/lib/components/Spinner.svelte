<script lang="ts">
  export let size: number = 24;
</script>

<div class="spinner" style={`width:${size}px;height:${size}px;`}></div>

<style>
  .spinner {
    border: 3px solid #e5e7eb;
    border-top-color: #2563eb;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
