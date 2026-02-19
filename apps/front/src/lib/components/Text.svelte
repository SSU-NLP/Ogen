<script lang="ts">
  export let text: string = "";
</script>

<p class="text">{text}<slot /></p>

<style>
  .text { margin: 0; color: #4b5563; font-size: 14px; line-height: 1.5; }
</style>
