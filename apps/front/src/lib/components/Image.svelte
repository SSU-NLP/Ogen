<script lang="ts">
  export let src: string = "";
  export let alt: string = "";
  export let width: string = "100%";
</script>

<img {src} {alt} style={`width:${width};`} />

<style>
  img { border-radius: 10px; display: block; }
</style>
