<script lang="ts">
  export let text: string = "";
</script>

<footer class="footer">
  {text}
  <slot />
</footer>

<style>
  .footer { padding: 16px; text-align: center; color: #6b7280; border-top: 1px solid #e5e7eb; background: #fff; }
</style>
