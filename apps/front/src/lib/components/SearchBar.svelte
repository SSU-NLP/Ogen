<script lang="ts">
  export let placeholder: string = "Search";
  export let value: string = "";
</script>

<div class="search">
  <input type="text" bind:value {placeholder} />
  <button>Search</button>
</div>

<style>
  .search { display: flex; gap: 8px; }
  input { flex: 1; padding: 8px 10px; border: 1px solid #d1d5db; border-radius: 8px; }
  button { padding: 8px 12px; border-radius: 8px; border: none; background: #2563eb; color: #fff; }
</style>
