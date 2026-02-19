<script lang="ts">
  export let label: string = "";
</script>

<div class="divider">
  <span>{label}</span>
</div>

<style>
  .divider { display: flex; align-items: center; gap: 10px; color: #9ca3af; font-size: 12px; }
  .divider::before,
  .divider::after {
    content: "";
    flex: 1;
    height: 1px;
    background: #e5e7eb;
  }
</style>
