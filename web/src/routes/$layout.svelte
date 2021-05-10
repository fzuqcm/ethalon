<script>
   import '../app.postcss'
   import 'uplot/dist/uPlot.min.css'
   import MeasurementList from '$lib/global/MeasurementList.svelte'
   import SignalList from '$lib/global/SignalList.svelte'
   import { isPaused, measurements, ports } from '$lib/store'
   import { socket } from '$lib/socket'
   import '$lib/init'
</script>

<main class="flex mt-4">
   <div class="w-64">
      <MeasurementList />
   </div>

   <div class="flex-1">
      <div class="flex">
         <button on:click={() => socket.emit('scan')}>Scan</button>
         <button on:click={() => socket.emit('calibrate', $ports)}>Calibrate</button>
         <button on:click={() => socket.emit('start', $ports)}>Start</button>
         <button on:click={() => socket.emit('stop', $ports)}>Stop</button>
         <button on:click={() => isPaused.set(!$isPaused)}>{$isPaused ? 'Play' : 'Pause'}</button>
         <button
            on:click={() =>
               socket.emit('offset', {
                  [Object.keys($measurements)[0]]: { freq: 10 ** 7 },
               })}
         >
            Test
         </button>
      </div>

      <slot />
   </div>

   <div class="w-64">
      <SignalList />
   </div>
</main>

<style lang="postcss">
   button {
      @apply px-4 py-2 rounded-lg uppercase text-white bg-green-500 hover:bg-green-600 text-sm font-semibold mr-2;
   }
</style>
