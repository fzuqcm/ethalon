<template>
  <div id="freq-diss-plot"></div>
</template>

<script>
import Plotly from 'plotly.js-dist'
import { lineTrace } from '@/plotly'

export default {
  mounted() {
    this.$forceUpdate()
  },
  updated() {
    Plotly.newPlot('freq-diss-plot', [lineTrace([], [])])
  },
}
</script>
