<script>
   import { onMount } from 'svelte'
   import { COLORS, PLOT_HEIGHT, PLOT_MARGIN } from '../constants'
   import { isPaused } from '../store'

   export let signal
   let plot

   onMount(async () => {
      const module = await import('uplot')
      const uPlot = module.default
      const el = document.getElementById(`plot-${signal.measurement}`)

      plot = new uPlot(
         {
            title: signal.name,
            width: el.offsetWidth - PLOT_MARGIN,
            height: PLOT_HEIGHT,
            series: [
               { label: 'Frequency' },
               { label: 'Amplitude', stroke: COLORS[0], scale: 'ampl' },
               { label: 'Phase', stroke: COLORS[1], scale: 'phas' },
            ],
            axes: [
               {
                  label: 'Frequency',
                  values: (self, vals) => vals.map(v => v.toExponential(3)),
               },
               {
                  label: 'Amplitude',
                  side: 3,
                  scale: 'ampl',
               },
               {
                  label: 'Phase',
                  side: 1,
                  scale: 'phas',
                  grid: { show: false },
               },
            ],
            scales: {
               x: {
                  time: false,
               },
            },
         },
         undefined,
         el
      )
   })

   $: if (signal.measurePoints && !$isPaused && plot) {
      plot.setData([
         signal.measurePoints.freq,
         signal.measurePoints.phas,
         signal.measurePoints.ampl,
      ])
   }
</script>

<div id={`plot-${signal.measurement}`} />
