<script lang="ts">
  export let title: string = "";
  export let open: boolean = true;
</script>

{#if open}
  <div class="backdrop">
    <div class="modal">
      {#if title}<h3>{title}</h3>{/if}
      <div class="content"><slot /></div>
    </div>
  </div>
{/if}

<style>
  .backdrop { position: relative; padding: 16px; background: rgba(17,24,39,0.04); }
  .modal { max-width: 420px; margin: 0 auto; background: #fff; border-radius: 12px; padding: 16px; border: 1px solid #e5e7eb; }
  h3 { margin: 0 0 10px; }
</style>
