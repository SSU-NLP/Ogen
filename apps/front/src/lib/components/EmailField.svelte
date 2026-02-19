<script lang="ts">
  export let label: string = "Email";
  export let placeholder: string = "user@example.com";
</script>

<div class="field">
  <label>{label}</label>
  <input type="email" {placeholder} />
</div>

<style>
  .field { display: flex; flex-direction: column; gap: 6px; }
  label { font-size: 14px; color: #374151; font-weight: 600; }
  input { padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 8px; }
</style>
