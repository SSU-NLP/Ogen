<script lang="ts">
  export let label: string = "";
  export let value: string = "";
  export let group: string = "";
</script>

<label class="radio">
  <input type="radio" value={value} bind:group={group} />
  <span>{label}</span>
</label>

<style>
  .radio { display: inline-flex; align-items: center; gap: 8px; font-size: 14px; color: #374151; }
  input { width: 16px; height: 16px; }
</style>
