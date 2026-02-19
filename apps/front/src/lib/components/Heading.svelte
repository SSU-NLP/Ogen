<script lang="ts">
  export let text: string = "Heading";
  export let level: 1 | 2 | 3 | 4 = 2;
</script>

{#if level === 1}
  <h1>{text}</h1>
{:else if level === 2}
  <h2>{text}</h2>
{:else if level === 3}
  <h3>{text}</h3>
{:else}
  <h4>{text}</h4>
{/if}

<style>
  h1,h2,h3,h4 { margin: 0; color: #111827; }
</style>
