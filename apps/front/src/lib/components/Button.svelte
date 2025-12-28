<script lang="ts">
  export let label: string = "Button";
  export let variant: 'primary' | 'secondary' = 'primary';
</script>

<button class={variant}>
  {label}
</button>

<style>
  button {
    padding: 10px 20px;
    border: none;
    border-radius: 6px;
    font-size: 16px;
    font-weight: bold;
    cursor: pointer;
    transition: opacity 0.2s;
  }
  button:hover { opacity: 0.9; }
  .primary { background: #007bff; color: white; }
  .secondary { background: #6c757d; color: white; }
</style>