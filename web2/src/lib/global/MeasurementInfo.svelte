<script>
   // import { devices } from '$lib/store'
   // import DeviceInfo from './DeviceInfo.svelte'

   export let measurement
</script>

<div class="rounded-lg mt-4 border">
   <!-- <DeviceInfo device={$devices[measurement.device]} /> -->

   <div class="p-2">
      <p class="truncate">{measurement.name}</p>
      <p>{measurement.started_at}</p>
   </div>
</div>
