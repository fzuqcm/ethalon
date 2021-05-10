<script>
   import { signals } from '$lib/store'
   import _ from 'lodash'
   import DevicePlot from '$lib/plots/DevicePlot.svelte'
   import SignalPlot from '$lib/plots/SignalPlot.svelte'
</script>

<SignalPlot name="freq" title="Frequency" />
<SignalPlot name="diss" title="Dissipation" />
<SignalPlot name="temp" title="Temperature" />

{#each _.entries($signals) as [port, signal]}
   <DevicePlot {signal} />
{/each}
