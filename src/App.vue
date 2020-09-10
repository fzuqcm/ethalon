<template>
  <div id="app" class="flex min-h-screen">
    <div class="w-48">
      <device-list />
    </div>
    <div class="flex-1 relative">
      <div v-if="logs.length > 0" class="absolute top-0 z-10 w-full">
        <button
          class="btn px-2 py-1 mt-2 mx-auto block text-left"
          style="width: 24rem"
          v-for="log in logs"
          :key="log.id"
          @click="log.isRead = true"
        >
          <span class="bg-blue-500 rounded px-1 text-sm">{{
            log.type | upper
          }}</span>
          {{ log.message }}
        </button>
      </div>
      <div class="grid grid-cols-2">
        <measurement-plot name="frequency" />
        <measurement-plot name="dissipation" />
        <measurement-plot name="phase" />
        <measurement-plot name="temperature" />
      </div>
    </div>
    <div class="w-48">
      <device-actions />
    </div>
    <full-modal
      v-if="$store.state.editedDevice !== null"
      @close="$store.commit('setEditedDevice', null)"
      @ok="$store.dispatch('saveDevice')"
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
    },
  },
  filters: {
    upper(text) {
      return text.toUpperCase()
    },
  },
  mounted() {
    this.$store.commit('log', 'Application has started')
    this.$store.dispatch('scanSerialPorts')
  },
}
</script>
