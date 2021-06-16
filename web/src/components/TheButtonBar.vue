<template>
  <div class="p-2 space-x-2 bg-gray-100 flex">
    <button @click.prevent="socket.emit('scan')">Scan</button>
    <button
      @click.prevent="socket.emit('calibrate', $store.getters.selectedPorts)"
    >
      Calibrate
    </button>
    <button @click.prevent="socket.emit('start', $store.getters.selectedPorts)">
      Start
    </button>
    <button @click.prevent="socket.emit('stop', $store.getters.selectedPorts)">
      Stop
    </button>
    <form
      @submit.prevent="$store.commit('setOffset', offset)"
      class="inline-block"
    >
      <input v-model.number="offset" type="number" class="w-48" />
      <button type="submit" class="ml-2">Set offset</button>
    </form>
    <button
      @click="$store.commit('setIsPlotPaused', !$store.state.isPlotPaused)"
    >
      {{ $store.state.isPlotPaused ? "Play" : "Pause" }}
    </button>

    <form @submit.prevent="emitMarker" class="ml-auto inline-block space-x-2">
      <select v-model="marker.name" class="w-32">
        <option value="test">Test</option>
      </select>
      <input v-model.number="marker.timestamp" type="number" class="w-32" />
      <button type="submit">Marker</button>
    </form>
  </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { DictStr, Marker, Measurement, socket } from "../utils";

export default defineComponent({
  data() {
    return {
      offset: 0,
      socket,
      marker: {
        name: "",
        timestamp: 0,
      },
    };
  },
  methods: {
    emitMarker() {
      const markers: DictStr<Marker[]> = {};
      this.$store.getters.selectedMeasurements.forEach((m: Measurement) => {
        this.$store.commit("addMarker", { port: m.port, marker: this.marker });
        markers[m.port] = m.data.markers;
      });

      socket.emit("marker", markers);
    },
  },
});
</script>
