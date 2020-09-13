<template>
  <div id="app" class="flex min-h-screen">
    <div class="w-48">
      <the-device-list />
    </div>
    <div class="flex-1 relative">
      <the-notifications />
      <the-note />
      <div class="grid grid-cols-2">
        <measurement-plot name="frequency" />
        <measurement-plot name="dissipation" />
        <measurement-plot name="phase" />
        <measurement-plot name="temperature" />
      </div>
    </div>
    <div class="w-48">
      <the-device-actions />
    </div>
    <the-edit-modal />
  </div>
</template>

<script>
import TheDeviceList from './components/TheDeviceList.vue'
import TheDeviceActions from './components/TheDeviceActions.vue'
import MeasurementPlot from './components/MeasurementPlot.vue'
import TheEditModal from './components/TheEditModal.vue'
import TheNote from './components/TheNote.vue'
import TheNotifications from './components/TheNotifications.vue'

export default {
  name: 'App',
  components: {
    TheDeviceList,
    TheDeviceActions,
    MeasurementPlot,
    TheEditModal,
    TheNote,
    TheNotifications,
  },
  mounted() {
    this.$store.commit('log', 'Application has started')
    this.$store.dispatch('scanSerialPorts')
  },
}
</script>
