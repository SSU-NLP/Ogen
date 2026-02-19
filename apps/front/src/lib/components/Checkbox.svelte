<script lang="ts">
  export let label: string = "";
  export let checked: boolean = false;
</script>

<label class="checkbox">
  <input type="checkbox" bind:checked />
  <span>{label}</span>
</label>

<style>
  .checkbox { display: inline-flex; align-items: center; gap: 8px; font-size: 14px; color: #374151; }
  input { width: 16px; height: 16px; }
</style>
