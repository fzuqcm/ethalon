<template>
  <div id="amp-phase-plot"></div>
</template>

<script>
import Plotly from 'plotly.js-dist'
import { lineTrace } from '@/plotly'

export default {
  mounted() {
    this.$forceUpdate()
  },
  updated() {
    Plotly.newPlot('amp-phase-plot', [lineTrace([], [])])
  },
}
</script>
