<template>
  <div :id="`plot-${name}`"></div>
</template>

<script lang="ts">
import Vue from 'vue'
import uPlot, { Options } from 'uplot'
import { State } from '@/interfaces'
import { PLOT_HEIGHT, PLOT_MARGIN } from '@/constants'
import { seriesTimestamp, axesTimestamps, seriesDevices } from '@/utils'

export default Vue.extend({
  props: ['name', 'label'],
  data() {
    return {
      plot: (null as unknown) as uPlot,
    }
  },
  computed: {
    values(): number[] {
      return this.$store.state.timestamps
    },
  },
  watch: {
    values() {
      const state = this.$store.state as State

      if (state.timestamps.length >= 2 && !state.isPlotPaused) {
        if (state.timestamps.length === 2) {
          this.renderPlot()
        }

        this.plot.setData([
          state.timestamps,
          ...state.devices.map(device => device.data[this.name as never]),
        ] as never)
      }
    },
  },
  mounted() {
    this.renderPlot()
  },
  methods: {
    renderPlot() {
      const state = this.$store.state as State
      const plotEl = document.getElementById(`plot-${this.name}`) as HTMLElement
      const opts: Options = {
        title: this.label,
        width: plotEl.offsetWidth - PLOT_MARGIN,
        height: PLOT_HEIGHT,
        series: [
          {
            label: 'Time',
            value: seriesTimestamp(state.timestamps[0]),
          },
          ...seriesDevices(state.devices),
        ],
        axes: [
          {
            label: 'Time',
            values: axesTimestamps(state.timestamps[0]),
          },
          {
            label: this.label,
          },
        ],
        scales: {
          x: {
            time: false,
          },
        },
      }

      if (this.plot) {
        this.plot.destroy()
      }

      this.plot = new uPlot(opts, undefined, plotEl)
    },
  },
})
</script>
