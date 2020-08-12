<template>
  <div id="app" class="flex min-h-screen">
    <div class="w-64">
      <h3 class="text-center text-lg py-3">Devices</h3>
      <device-list />
    </div>
    <div class="flex-1">
      <div class="grid grid-cols-2">
        <measurement-plot name="temperature" />
        <measurement-plot name="dissipation" />
        <measurement-plot name="phase" />
        <measurement-plot name="magnitude" />
      </div>
    </div>
    <div class="w-64">
      <h3 class="text-center text-lg py-3">Actions</h3>
      <device-actions />
    </div>
  </div>
</template>

<script>
import DeviceList from './components/DeviceList.vue'
import DeviceActions from './components/DeviceActions.vue'
import MeasurementPlot from './components/MeasurementPlot.vue'

export default {
  name: 'App',
  components: {
    DeviceList,
    DeviceActions,
    MeasurementPlot,
  },
  mounted() {
    this.$store.commit('generateData')
  },
}
</script>
