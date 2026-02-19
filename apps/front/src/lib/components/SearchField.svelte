<script lang="ts">
  export let placeholder: string = "Search";
</script>

<div class="field">
  <input type="text" {placeholder} />
  <button>Go</button>
</div>

<style>
  .field { display: flex; gap: 8px; }
  input { flex: 1; padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 8px; }
  button { padding: 10px 12px; border-radius: 8px; border: none; background: #2563eb; color: #fff; }
</style>
