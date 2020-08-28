<template>
  <div id="app" class="flex min-h-screen">
    <div class="w-64">
      <!-- <h3 class="text-center text-lg py-3">Devices</h3> -->
      <device-list />
    </div>
    <div class="flex-1 relative">
      <div v-if="logs.length > 0" class="absolute top-0 z-10">
        <p class="btn px-2 py-1 mt-2"
          v-for="log in logs"
          :key="log.message + Math.random()"
        >
          {{ log.message }}
        </p>
      </div>
      <div class="grid grid-cols-2">
        <measurement-plot name="frequency" />
        <measurement-plot name="dissipation" />
        <measurement-plot name="phase" />
        <measurement-plot name="temperature" />
      </div>
    </div>
    <div class="w-64">
      <!-- <h3 class="text-center text-lg py-3">Actions</h3> -->
      <device-actions />
    </div>
    <full-modal
      v-if="$store.state.editedDevice !== null"
      @close="$store.commit('setEditedDevice', null)"
    >
      <form @submit.prevent>
        <label class="label">
          Name
          <input
            class="input"
            v-model="$store.state.editedDevice.name"
            @keypress.enter="$store.dispatch('saveDevice')"
          />
        </label>
        <label class="label">
          Calibrated frequecy
        </label>
        <span class="input">
          {{ $store.state.editedDevice.calibratedFrequency }} Hz
        </span>
        <label class="label">
          Port
        </label>
        <span class="input">{{ $store.state.editedDevice.path }}</span>
      </form>
    </full-modal>
  </div>
</template>

<script>
import DeviceList from './components/DeviceList.vue'
import DeviceActions from './components/DeviceActions.vue'
import MeasurementPlot from './components/MeasurementPlot.vue'
import FullModal from './components/FullModal.vue'

export default {
  name: 'App',
  components: {
    DeviceList,
    DeviceActions,
    MeasurementPlot,
    FullModal,
  },
  computed: {
    logs() {
      return this.$store.state.logs.filter(l => !l.isRead)
    }
  },
  mounted() {
    this.$store.commit('log', 'Application has started')
    this.$store.dispatch('scanSerialPorts')
  },
}
</script>
