<template>
  <div id="app" class="flex min-h-screen">
    <div class="w-64">
      <h3 class="text-center text-lg py-3">Devices</h3>
      <device-list />
    </div>
    <div class="bg-red-400 flex-1">
      <div class="grid grid-cols-2 gap-2">
        <temperature-plot />
        <amp-phase-plot />
        <freq-diss-plot class="col-span-2" />
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
import TemperaturePlot from './components/TemperaturePlot.vue'
import AmpPhasePlot from './components/AmpPhasePlot.vue'
import FreqDissPlot from './components/FreqDissPlot.vue'

export default {
  name: 'App',
  components: {
    DeviceList,
    DeviceActions,
    TemperaturePlot,
    AmpPhasePlot,
    FreqDissPlot,
  },
}
</script>
