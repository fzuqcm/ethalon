<script>
   import { ports, signals } from '../store'
   import _ from 'lodash'
   import SignalInfo from './SignalInfo.svelte'
</script>

<div class="px-2">
   <h4>Signals</h4>

   {#each _.entries($signals) as [port, signal]}
      <SignalInfo {signal} onClick={() => {
         if ($ports.includes(port)) {
            ports.set($ports.filter(p => p !== port))
         } else {
            ports.set([...$ports, port])
         }
      }} />
   {/each}
</div>
