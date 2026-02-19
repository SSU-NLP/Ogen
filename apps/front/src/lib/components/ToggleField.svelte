<script lang="ts">
  export let label: string = "";
  export let checked: boolean = false;
</script>

<label class="toggle-field">
  <input type="checkbox" bind:checked />
  <span>{label}</span>
</label>

<style>
  .toggle-field { display: inline-flex; gap: 8px; align-items: center; font-size: 14px; color: #374151; }
  input { width: 16px; height: 16px; }
</style>
