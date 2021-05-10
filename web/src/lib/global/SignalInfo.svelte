<script>
   import { devices, ports } from '$lib/store'
   import DeviceInfo from './DeviceInfo.svelte'

   export let signal
   export let onClick
</script>

<div class="rounded-lg mt-4 border">
   <DeviceInfo device={$devices[signal.device]} />

   <div class="p-2 cursor-pointer" class:bg-green-200={$ports.includes(signal.port)} on:click={() => onClick()}>
      <p>Port: {signal.port}</p>
      <p>Calib. freq: {signal.calib_freq}</p>
   </div>
</div>
