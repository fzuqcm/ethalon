<template>
  <div id="temperature-plot"></div>
</template>

<script>
import Plotly from 'plotly.js-dist'
import { lineTrace } from '@/plotly'

export default {
  mounted() {
    this.$forceUpdate()
  },
  updated() {
    Plotly.newPlot('temperature-plot', [lineTrace([], [])])
  },
}
</script>
