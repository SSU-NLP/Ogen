<script lang="ts">
  export let label: string = "";
  export let type: string = "text";
  export let placeholder: string = "";
</script>

<div class="input-group">
  {#if label}
    <label>{label}</label>
  {/if}
  <input {type} {placeholder} />
</div>

<style>
  .input-group { display: flex; flex-direction: column; gap: 6px; }
  label { font-size: 14px; font-weight: 600; color: #333; }
  input {
    padding: 10px 12px;
    border: 1px solid #ccc;
    border-radius: 6px;
    font-size: 16px;
    transition: border-color 0.2s;
  }
  input:focus { border-color: #007bff; outline: none; }
</style>