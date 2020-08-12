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
  },
  watch: {
    devicesInPlot() {
      this.$forceUpdate()
    },
  },
  mounted() {
    this.$forceUpdate()
  },
  updated() {
    Plotly.newPlot(
      this.id,
      this.devicesInPlot.map(device => {
        const data = device.datapoints[this.name]
        return {
          x: Object.keys(data),
          y: data,
          type: 'scatter',
          name: device.label,
        }
      }),
      {
        title: _.upperFirst(this.name) + ' plot',
      }
    )
  },
}
</script>
