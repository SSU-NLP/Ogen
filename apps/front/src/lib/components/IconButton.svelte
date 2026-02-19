<script lang="ts">
  export let icon: string = "★";
  export let label: string = "";
  export let variant: 'primary' | 'secondary' | 'ghost' = 'ghost';
  export let size: 'sm' | 'md' | 'lg' = 'md';
</script>

<button class={`icon-btn ${variant} ${size}`} aria-label={label || icon}>
  <span aria-hidden="true">{icon}</span>
</button>

<style>
  .icon-btn {
    border: none;
    border-radius: 8px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }
  .sm { width: 28px; height: 28px; font-size: 14px; }
  .md { width: 36px; height: 36px; font-size: 16px; }
  .lg { width: 44px; height: 44px; font-size: 18px; }
  .primary { background: #2563eb; color: #fff; }
  .secondary { background: #e5e7eb; color: #111827; }
  .ghost { background: transparent; color: #111827; border: 1px solid #e5e7eb; }
</style>
