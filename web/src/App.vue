<template>
  <TheButtonBar />

  <div class="flex">
    <div class="w-64">
      <div
        v-for="([port, m], i) in measurementPairs"
        :key="port"
        class="p-1 block border-b"
      >
        <label :for="port" class="flex hover:bg-gray-100">
          <input
            v-model="m.isSelected"
            type="checkbox"
            :name="port"
            :id="port"
            class="mx-2 my-2"
          />
          <div>
            <p><b>Name:</b> {{ m.data.name }}{{ i }}</p>
            <p><b>Port:</b> {{ m.port }}</p>
            <p><b>RF:</b> {{ m.calibFreq }}</p>
            <p><b>Offset:</b> {{ m.offset.freq }}</p>
            <p>
              <b>Color:</b>
              <span
                class="inline-block w-8 h-2 mb-0.5"
                :style="'background-color: ' + COLORS[i]"
              />
            </p>
            <p><b>Device:</b></p>
            <p class="ml-4"><b>Name:</b> {{ m.device.name }}</p>
            <p class="ml-4"><b>SN:</b> {{ m.device.serialNumber }}</p>
          </div>
        </label>
        <button class="w-full bg-gray-400">Edit</button>
        <pre>{{ m.markers }}</pre>
      </div>
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
import { socket, COLORS } from "./utils";
import "uplot/dist/uPlot.min.css";

export default defineComponent({
  name: "App",
  components: {
    SignalPlot,
    TheButtonBar,
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
  }
});
</script>
