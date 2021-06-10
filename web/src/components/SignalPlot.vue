<template>
  <UplotVue :data="data" :options="options" />
</template>

<script lang="ts">
import { defineComponent } from "@vue/runtime-core";
import _ from "lodash";
import uPlot, { Options } from "uplot";
import "uplot/dist/uPlot.min.css";
import dayjs from "dayjs";
import UplotVue from "./CustomUplot.vue";

interface Data {
  id: string;
  plot: uPlot | null;
  options: Options | null;
  data?: any
}

const COLORS = [
  "blue",
  "red",
  "green",
  "blueviolet",
  "brown",
  "darkcyan",
  "deepskyblue",
  "indigo",
  "chocolate",
  "crimson",
];

export default defineComponent({
  name: "SignalPlot",
  components: { UplotVue },
  props: {
    name: {
      type: String,
      required: true,
    },
    height: {
      type: Number,
      default: 200,
    },
    width: {
      type: Number,
      default: 200,
    },
  },
  data(): Data {
    return {
      id: "",
      plot: null,
      options: null
    }
  },
  created() {
    const device = this.$store.state.devices[0];
    const against = 0;
    this.id = "plot-" + _.uniqueId();
    this.options = {
      title: this.name,
      width: this.width,
      height: this.height,
      cursor: {
        drag: { x: true, y: true },
      },
      series: [
        {
          label: "Time",
          value: (self, value) => {
            return value;
          },
        },
        {
          label: device?.name,
          stroke: COLORS[0],
        },
        //   ...seriesDevices(state.devices),
      ],
      axes: [
        {
          label: "Time",
          values: (self: uPlot, values: number[]) => {
            const millisDiffer = values[values.length - 1] - against;
            let format = "ss.SSS";
            if (millisDiffer > 3600 * 1000) {
              format = "HH:mm";
            } else if (millisDiffer > 60 * 1000) {
              format = "mm:ss";
            }
            return values.map((value) =>
              dayjs.utc(value - against).format(format)
            );
          },
        },
        {
          label: this.name,
        },
      ],
      scales: {
        x: {
          time: false,
        },
      },
    };
  },
  beforeMount() {
    this.data = [[...new Array(100000)].map((_, i) => i), [...new Array(100000)].map((_, i) => i % 1000)];
  },
  mounted() {
    this.renderPlot();
  },
  methods: {
    renderPlot() {
      console.log("render plot");

      // find div with proper id
      const el = document.getElementById(this.id) as HTMLElement;
      const device = this.$store.state.devices[0];
      const against = 0;

      const opts: Options = {
        title: this.name,
        width: this.width - 50 || el.clientWidth - 15,
        height: this.height - 50,
        cursor: {
          drag: { x: true, y: true },
        },
        series: [
          {
            label: "Time",
            value: (self, value) => {
              return value;
            },
          },
          {
            label: device?.name,
            stroke: COLORS[0],
          },
          //   ...seriesDevices(state.devices),
        ],
        axes: [
          {
            label: "Time",
            values: (self: uPlot, values: number[]) => {
              const millisDiffer = values[values.length - 1] - against;
              let format = "ss.SSS";
              if (millisDiffer > 3600 * 1000) {
                format = "HH:mm";
              } else if (millisDiffer > 60 * 1000) {
                format = "mm:ss";
              }
              return values.map((value) =>
                dayjs.utc(value - against).format(format)
              );
            },
          },
          {
            label: this.name,
          },
        ],
        scales: {
          x: {
            time: false,
          },
        },
      };

      // if already present, destroy previous plot to prevent memory leaks
      if (this.plot) {
        this.plot.destroy();
      }

      // render new plot
      this.plot = new uPlot(opts, undefined, el);
      //   this.plot.
    },
  },
});
</script>
