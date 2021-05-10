<script>
   import { onMount } from 'svelte'
   import _ from 'lodash'
   import { COLORS, PLOT_HEIGHT, PLOT_MARGIN } from '../constants'
   import { signals, isPaused, measurements, rerenderPlot } from '../store'
   import dayjs from 'dayjs'
import { dataset_dev } from 'svelte/internal';

   export let name
   export let title
   let plot
   let uPlot
   let mounted = false

   onMount(async () => {
      const module = await import('uplot')
      uPlot = module.default
      mounted = true
      renderPlot()
   })

   function renderPlot() {
      if (!uPlot || !mounted) {
         return
      }

      if (plot) {
         plot.destroy()
      }

      const el = document.getElementById(`plot-${name}`)

      plot = new uPlot(
         {
            title,
            width: el.offsetWidth - PLOT_MARGIN,
            height: PLOT_HEIGHT,
            series: [
               {
                  label: 'Time',
                  value: (self, val) => dayjs(val).format('HH:mm:ss.SSS'),
                  // value: seriesTimestamp($timestamps[0]),
               },
               ..._.entries($measurements).map(([port, measurement], i) => {
                  return {
                     label: measurement.name,
                     stroke: COLORS[i],
                     value: (self, val) => val ? val.toExponential(6) : val,
                  }
               }),
            ],
            axes: [
               {
                  label: 'Time',
                  values: (self, vals) => vals.map((v) => dayjs(v).format('HH:mm:ss')),
                  // values: axesTimestamps($timestamps[0]),
               },
               {
                  label: title,
                  values: (self, vals) => vals.map((v) => v.toExponential(3)),
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
   }

   $: {
      $rerenderPlot
      rerenderPlot.set(false)
      renderPlot()
   }
   $: ($signals || $measurements) && setData()

   function setData() {
      if (!uPlot || !mounted || !plot) {
         return
      }

      const newData = []
      const prefix = {}
      const mValues = _.values($measurements)
      const time = _.unionBy(...mValues.map((x) => x.time))

      _.entries($measurements).map(([id, measurement]) => {
         const idx = measurement.time[0]
         if (!idx) {
            return
         }

         prefix[id] = _.fill(Array(time.indexOf(idx)), undefined)
      })

      _.entries($measurements).forEach(([id, measurement]) => {
         if ((measurement[name] || []).length > 2) {
            if (newData.length === 0) {
               newData.push(time)
            }

            newData.push(_.concat(prefix[id], measurement[name]))
         }
      })

      if (!$isPaused) {
         plot.setData(newData)
         // console.warn(newData[3])
      }
   }
</script>

<div id={`plot-${name}`} />
