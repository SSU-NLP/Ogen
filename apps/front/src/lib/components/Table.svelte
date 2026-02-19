<script lang="ts">
  export let columns: string[] = [];
  export let rows: Array<Record<string, string>> = [];
</script>

<table class="table">
  <thead>
    <tr>
      {#each columns as col}
        <th>{col}</th>
      {/each}
    </tr>
  </thead>
  <tbody>
    {#each rows as row}
      <tr>
        {#each columns as col}
          <td>{row[col] ?? ''}</td>
        {/each}
      </tr>
    {/each}
  </tbody>
</table>

<style>
  .table { width: 100%; border-collapse: collapse; font-size: 14px; }
  th, td { border-bottom: 1px solid #e5e7eb; padding: 8px; text-align: left; }
  th { color: #6b7280; font-weight: 600; }
</style>
