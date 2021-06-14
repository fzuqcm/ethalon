<template>
  <div class="flex-1"></div>
</template>

<script lang="ts">
import { defineComponent, PropType } from "vue";
import { optionsUpdateState } from "./uPlot.wrappers";
import uPlot, { Options } from "uplot";

export default defineComponent({
  name: "UplotVue",
  props: {
    options: {
      type: Object as PropType<Options>,
      required: true,
    },
    data: {
      type: Array as unknown as PropType<[number[], ...number[][]]>,
      required: true,
    },
  },
  data(): { _chart: uPlot | null; width: number } {
    return { _chart: null, width: 0 };
  },
  watch: {
    options(options, prevOptions) {
      const optionsState = optionsUpdateState(prevOptions, options);
      if (!this._chart || optionsState === "create") {
        this._destroy();
        this._create();
      } else if (optionsState === "update") {
        this._chart.setSize({ width: this.width, height: options.height });
      }
    },
    data(data) {
      if (!this._chart) {
        this._create();
      }

      if (!this.$store.state.isPlotPaused) {
        (this._chart as uPlot).setData(data);
      }
    },
  },
  mounted() {
    this.width = this.$el.offsetWidth;
    this._create();
  },
  beforeUnmount() {
    this._destroy();
  },
  methods: {
    _destroy() {
      if (this._chart) {
        this.$emit("delete", this._chart);
        this._chart.destroy();
        this._chart = null;
      }
    },
    _create() {
      this.options.width = this.width;
      this._chart = new uPlot(this.$props.options, this.$props.data, this.$el);
      this.$emit("create", this._chart);
    },
  },
});
</script>
