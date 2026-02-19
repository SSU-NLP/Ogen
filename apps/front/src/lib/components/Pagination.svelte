<script lang="ts">
  export let page: number = 1;
  export let total: number = 10;
</script>

<div class="pagination">
  <button disabled={page === 1}>Prev</button>
  <span>{page} / {total}</span>
  <button disabled={page === total}>Next</button>
</div>

<style>
  .pagination { display: flex; align-items: center; gap: 8px; }
  button { padding: 6px 10px; border-radius: 6px; border: 1px solid #e5e7eb; background: #fff; }
</style>
