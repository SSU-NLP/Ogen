<script lang="ts">
  export let name: string = "User";
  export let src: string = "";
  export let size: 'sm' | 'md' | 'lg' = 'md';
</script>

<div class={`avatar ${size}`}>
  {#if src}
    <img src={src} alt={name} />
  {:else}
    <span>{name[0] || 'U'}</span>
  {/if}
</div>

<style>
  .avatar { border-radius: 50%; background: #e5e7eb; color: #111827; display: inline-flex; align-items: center; justify-content: center; overflow: hidden; }
  .sm { width: 28px; height: 28px; font-size: 12px; }
  .md { width: 36px; height: 36px; font-size: 14px; }
  .lg { width: 48px; height: 48px; font-size: 18px; }
  img { width: 100%; height: 100%; object-fit: cover; }
</style>
