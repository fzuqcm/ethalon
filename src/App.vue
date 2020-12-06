<template>
  <div id="app">
    <the-button-bar />
    <div
      v-if="$store.state.devices.length > 0"
      class="my-10 grid grid-col-1 gap-10"
    >
      <data-plot name="freq" label="Frequency" />
      <data-plot name="diss" label="Dissipation" />
      <data-plot name="temp" label="Temperature" />
      <div class="grid grid-cols-2 gap-4">
        <device-plot
          v-for="device in $store.state.devices"
          :key="device.serial_number"
          :device="device"
        />
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue'
import { Device, MeasuredData } from './interfaces'
import DataPlot from '@/components/DataPlot.vue'
import TheButtonBar from '@/components/TheButtonBar.vue'
import DevicePlot from '@/components/DevicePlot.vue'

export default Vue.extend({
  components: {
    DataPlot,
    TheButtonBar,
    DevicePlot,
  },
  sockets: {
    measuredData: function (data: MeasuredData) {
      this.$store.commit('processMeasuredData', data)
    },
    devices: function (rawDevices: Partial<Device>[]) {
      this.$store.commit('setDevices', rawDevices)
    },
  },
  methods: {
    socketEmit(name: string) {
      this.$socket.emit(name)
    },
  },
})
</script>
