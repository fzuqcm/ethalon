<template>
  <div :id="`plot-${device.serial_number}`"></div>
</template>

<script lang="ts">
import Vue from 'vue'
import uPlot from 'uplot'
import { COLORS, PLOT_HEIGHT, PLOT_MARGIN } from '@/constants'
import { MeasurePoints, State } from '@/interfaces'

export default Vue.extend({
  props: {
    device: Object,
  },
  data() {
    return {
      plot: (null as unknown) as uPlot,
    }
  },
  computed: {
    values() {
      return this.device.measurePoints.freq
    },
  },
  watch: {
    values(newValues: number[]) {
      const measurePoints = this.device.measurePoints as MeasurePoints
      const state = this.$store.state as State

      if (newValues.length >= 2 && !state.isPlotPaused) {
        this.plot.setData([
          measurePoints.freq,
          measurePoints.ampl,
          measurePoints.phas,
        ] as never)
      }
    },
  },
  mounted() {
    this.renderPlot()
  },
  methods: {
    renderPlot() {
      const sn = this.device.serial_number
      const el = document.getElementById('plot-' + sn) as HTMLElement
      this.plot = new uPlot(
        {
          title: this.device.name,
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
    },
  },
})
</script>
