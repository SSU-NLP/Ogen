<script lang="ts">
  export let label: string = "";
  export let placeholder: string = "";
  export let rows: number = 4;
  export let value: string = "";
</script>

<div class="field">
  {#if label}
    <label>{label}</label>
  {/if}
  <textarea {rows} {placeholder} bind:value></textarea>
</div>

<style>
  .field { display: flex; flex-direction: column; gap: 6px; }
  label { font-size: 14px; color: #374151; font-weight: 600; }
  textarea {
    padding: 10px 12px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    font-size: 14px;
    resize: vertical;
  }
</style>
