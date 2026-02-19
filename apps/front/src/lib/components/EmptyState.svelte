<script lang="ts">
  export let title: string = "No data";
  export let description: string = "";
</script>

<div class="empty">
  <h3>{title}</h3>
  <p>{description}</p>
  <slot />
</div>

<style>
  .empty { padding: 24px; border: 1px dashed #d1d5db; border-radius: 12px; text-align: center; }
  p { color: #6b7280; }
</style>
