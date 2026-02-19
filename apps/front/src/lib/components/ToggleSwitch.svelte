<script lang="ts">
  export let label: string = "";
  export let checked: boolean = false;
</script>

<label class="switch">
  <input type="checkbox" bind:checked />
  <span class="slider"></span>
  {#if label}<span class="text">{label}</span>{/if}
</label>

<style>
  .switch { display: inline-flex; align-items: center; gap: 8px; }
  .switch input { display: none; }
  .slider {
    width: 40px; height: 22px; border-radius: 999px; background: #d1d5db; position: relative; transition: background 0.2s;
  }
  .slider::after {
    content: ""; width: 18px; height: 18px; border-radius: 50%; background: #fff; position: absolute; top: 2px; left: 2px; transition: transform 0.2s;
  }
  input:checked + .slider { background: #10b981; }
  input:checked + .slider::after { transform: translateX(18px); }
  .text { font-size: 14px; color: #374151; }
</style>
