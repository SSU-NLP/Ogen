<script lang="ts">
  export let title: string = "";
  export let subtitle: string = "";
</script>

<section class="hero">
  <h2>{title}</h2>
  <p>{subtitle}</p>
  <slot />
</section>

<style>
  .hero { padding: 24px; border-radius: 16px; background: #f3f4f6; }
  h2 { margin: 0 0 8px; }
  p { margin: 0; color: #6b7280; }
</style>
