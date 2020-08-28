<template>
  <div :id="id"></div>
</template>

<script>
import Plotly from 'plotly.js-dist'
import _ from 'lodash'

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
    devicesInPlot() {
      return this.$store.getters.devicesInPlot(this.name)
    },
    devicesDatapoints() {
      return this.$store.getters.devicesDatapoints(this.name)
    },
    plotData() {
      return this.$store.getters.getPlotByName(this.name)
    },
  },
  watch: {
    devicesInPlot() {
      this.$forceUpdate()
    },
    devicesDatapoints() {
      this.$forceUpdate()
    },
    plotData() {
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
        }
      }),
      {
        title: _.upperFirst(this.name) + ' plot',
      }
    )
  },
}
</script>
