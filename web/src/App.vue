<template>
  <!-- <pre>
    {{ $store.state.devices }}
    {{ $store.state.measurements }}
    {{ $store.state.measurements }}
  </pre> -->
  <pre>
  <!-- {{$store.state.firstTime}} -->
    {{$store.getters.selectedPorts}}
  </pre>

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
  <button @click="$store.commit('setOffset', 0)">Set offset 0</button>
  <button @click="$store.commit('setOffset', 2642)">Set offset 1000</button>
  <button @click="$store.commit('setIsPlotPaused', !$store.state.isPlotPaused)">
    {{ $store.state.isPlotPaused ? "Play" : "Pause" }}
  </button>

  <div class="flex">
    <div class="w-64">
      <div
        v-for="[port, m] in measurementPairs"
        :key="port"
        class="p-1 block border-b"
      >
        <label :for="port" class="flex">
          <input
            v-model="m.isSelected"
            type="checkbox"
            :name="port"
            :id="port"
            class="mx-2 my-2"
          />
          <div>
            <p><b>Name:</b> {{ m.name }}</p>
            <p><b>Port:</b> {{ m.port }}</p>
            <p><b>Res. Freq.:</b> {{ m.calibFreq }}</p>
            <p><b>Device:</b></p>
            <p class="ml-4"><b>Name:</b> {{ m.device.name }}</p>
            <p class="ml-4"><b>SN:</b> {{ m.device.serialNumber }}</p>
          </div>
        </label>
      </div>
    </div>

    <SignalPlot
      :data="plotData.freq"
      :options="{
        title: 'Frequency vs Time',
        width: 760,
        height: 500,
        series: [plotTimeSeries, ...plotSeries],
        scales: { x: { time: false }, f: { auto: true } },
        axes: [
          plotTimeAxis,
          {
            label: 'Frequency',
            values: (self, vals) => vals,
          },
        ],
        cursor: {
          drag: { x: true, y: true },
        },
      }"
    />
  </div>
</template>

<script lang="ts">
import _ from "lodash";
import { defineComponent } from "vue";
import { mapGetters } from "vuex";
import SignalPlot from "./components/CustomUplot.vue";
import { socket } from "./utils";
import "uplot/dist/uPlot.min.css";

export default defineComponent({
  name: "App",
  components: {
    SignalPlot,
  },
  computed: {
    measurementPairs() {
      return _.toPairs(this.$store.state.measurements);
    },
    socket() {
      return socket;
    },
    ...mapGetters(["plotData", "plotTimeSeries", "plotSeries", "plotTimeAxis"]),
  },
});
</script>
