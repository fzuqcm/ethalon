<template>
  <TheButtonBar />

  <div class="flex">
    <div class="w-64">
      <DeviceInfo
        v-for="([port, m], i) in measurementPairs"
        :key="port"
        :m="m"
        :i="i"
      />
    </div>

    <SignalPlot
      :data="plotData.freq"
      :options="{
        title: 'Frequency vs Time',
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
import TheButtonBar from "./components/TheButtonBar.vue";
import DeviceInfo from "./components/DeviceInfo.vue";
import { socket, COLORS, Measurement } from "./utils";
import "uplot/dist/uPlot.min.css";

export default defineComponent({
  name: "App",
  components: {
    SignalPlot,
    TheButtonBar,
    DeviceInfo,
  },
  data() {
    return {
      COLORS,
      markerTime: 0,
    };
  },
  computed: {
    measurementPairs() {
      return _.toPairs(this.$store.state.measurements);
    },
    socket() {
      return socket;
    },
    ...mapGetters(["plotData", "plotTimeSeries", "plotSeries", "plotTimeAxis"]),
    x() {
      return _.values(this.$store.state.measurements).map((m) => m.time);
    },
  },
  methods: {
    removeMarker(index: number, m: Measurement) {
      this.$store.commit("removeMarker", { port: m.port, index });
      socket.emit("marker", { [m.port]: m.data.markers });
    },
  },
});
</script>
