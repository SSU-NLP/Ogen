<script lang="ts">
  export let label: string = "Link";
  export let href: string = "#";
</script>

<a class="link" {href}>{label}</a>

<style>
  .link { color: #2563eb; text-decoration: none; font-weight: 600; }
  .link:hover { text-decoration: underline; }
</style>
