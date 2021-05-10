<script>
   export let device
</script>

<div class="p-2 border-b">
   {#if device}
      <p>{device.name}</p>
      <p>SN: {device.serial_number}</p>
   {:else}
      <p>Loading...</p>
   {/if}
</div>
