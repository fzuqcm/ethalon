<template>
  <div id="app" class="flex min-h-screen">
    <div class="w-64">
      <!-- <h3 class="text-center text-lg py-3">Devices</h3> -->
      <device-list />
    </div>
    <div class="flex-1">
      <div class="grid grid-cols-2">
        <measurement-plot name="magnitude" />
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
  mounted() {
    this.$store.dispatch('scanSerialPorts')
  },
}
</script>
