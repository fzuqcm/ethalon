<template>
  <div :id="id"></div>
</template>

<script>
import Plotly from 'plotly.js-dist'
import _ from 'lodash'
import { NORMAL_FONT_SIZE } from '@/store'

export default {
  props: {
    name: {
      type: String,
      required: true,
    },
  },
  computed: {
    id() {
      return this.name + '-plot'
    },
    plotData() {
      return this.$store.getters.getPlotByName(this.name)
    },
    fontSize() {
      return this.$store.state.fontSize
    },
  },
  watch: {
    plotData() {
      this.$forceUpdate()
    },
    fontSize() {
      this.$forceUpdate()
    },
  },
  mounted() {
    this.$forceUpdate()
  },
  updated() {
    Plotly.newPlot(
      this.id,
      this.plotData.map(deviceData => {
        return {
          ...deviceData,
          type: 'scatter',
          line: {
            width: this.$store.state.fontSize === NORMAL_FONT_SIZE ? 2 : 4,
          },
        }
      }),
      {
        title: _.upperFirst(this.name) + ' plot',
        font: { size: this.$store.state.fontSize },
      },
      { responsive: true }
    )
  },
}
</script>
