<script lang="ts">
    export let label: string = "";
    export let style: string = "";
  </script>
  
  <section class="ogen-container" {style}>
    {#if label}
      <h3 class="label">{label}</h3>
    {/if}
    <slot />
  </section>
  
  <style>
    .ogen-container {
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      padding: 20px;
      background: #fff;
      box-shadow: 0 2px 8px rgba(0,0,0,0.05);
      display: flex;
      flex-direction: column;
      gap: 16px;
      margin-bottom: 10px;
    }
    .label { margin: 0 0 10px 0; font-size: 14px; color: #888; text-transform: uppercase; letter-spacing: 1px; }
  </style>