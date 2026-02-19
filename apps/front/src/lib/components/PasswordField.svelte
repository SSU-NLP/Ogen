<script lang="ts">
  export let label: string = "Password";
  export let placeholder: string = "Enter password";
</script>

<div class="field">
  <label>{label}</label>
  <input type="password" {placeholder} />
</div>

<style>
  .field { display: flex; flex-direction: column; gap: 6px; }
  label { font-size: 14px; color: #374151; font-weight: 600; }
  input { padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 8px; }
</style>
