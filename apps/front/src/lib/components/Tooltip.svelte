<script lang="ts">
  export let text: string = "Tooltip";
</script>

<span class="tooltip">
  <slot />
  <span class="tooltip-text">{text}</span>
</span>

<style>
  .tooltip { position: relative; display: inline-flex; }
  .tooltip-text {
    position: absolute;
    bottom: calc(100% + 6px);
    left: 50%;
    transform: translateX(-50%);
    background: #111827;
    color: #fff;
    padding: 6px 8px;
    border-radius: 6px;
    font-size: 12px;
    white-space: nowrap;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.2s;
  }
  .tooltip:hover .tooltip-text { opacity: 1; }
</style>
