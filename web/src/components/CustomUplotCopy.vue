<template>
  <div v-if="open">
    <div ref="targetRef"></div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { optionsUpdateState, dataMatch } from "./uPlot.wrappers";
import uPlot from "uplot";

export default defineComponent({
  name: "UplotVue",
  props: {
    options: { type: Object, required: true },
    data: { type: Array, required: true },
    target: {
      validator(target) {
        return (
          target == null ||
          target instanceof HTMLElement ||
          typeof target === "function"
        );
      },
      default: undefined,
      required: false,
    },
    open: {
      type: Boolean,
      default: false
    },
    height: {
      type: Number,
      default: 600,
    },
    width: {
      type: Number,
      default: 800,
    },
    left: {
      type: Number,
      default: 200,
    },
    top: {
      type: Number,
      default: 200,
    },
  },
  data(): { _chart: uPlot | null; windowRef: Window | null } {
    // eslint-disable-next-line
    return { _chart: null, windowRef: null };
  },
  watch: {
    open(newOpen) {
      if (newOpen) {
        this.openPortal();
      } else {
        this.closePortal();
      }
    },
    options(options, prevOptions) {
      const optionsState = optionsUpdateState(prevOptions, options);
      if (!this._chart || optionsState === "create") {
        this._destroy();
        this._create();
      } else if (optionsState === "update") {
        // @ts-ignore
        this._chart.setSize({ width: options.width, height: options.height });
      }
    },
    target() {
      this._destroy();
      this._create();
    },
    data(data, prevData) {
      if (!this._chart) {
        this._create();
      } else if (!dataMatch(prevData, data)) {
        // @ts-ignore
        this._chart.setData(data);
      }
    },
  },
  mounted() {
    this._create();

    if (this.open) {
      this.openPortal()
    }
  },
  beforeUnmount() {
    this._destroy();
  },
  methods: {
    _destroy() {
      if (this._chart) {
        this.$emit("delete", this._chart);
        // @ts-ignore
        this._chart.destroy();
        this._chart = null;
      }
    },
    openPortal() {
      this.windowRef = window.open(
        "",
        "__self", // @ts-ignore
        `width=${this.width},height=${this.height},left=${this.left},top=${this.top}`
      ) as Window;

      console.log(this.windowRef);
      

      Array.from(window.document.head.children).forEach((element) => {
        (this.windowRef as Window).document.head.appendChild(
          element.cloneNode(true)
        );
      });
      
      // Array.from(window.document.scripts).forEach((element) => {
      //   (this.windowRef as Window).document.body.appendChild(
      //     element.cloneNode(true)
      //   );
      // });

      this.windowRef.addEventListener("beforeunload", this.closePortal);
      // magic!
      this.windowRef.document.body.appendChild(this.$el);
    },
    
    closePortal() {
      if (this.windowRef) {
        this.windowRef.close();
        this.windowRef = null;
        this.$emit("close");
      }
    },
    _create() {
      // @ts-ignore
      this._chart = new uPlot( // @ts-ignore
        this.options, // @ts-ignore
        this.$props.data, // @ts-ignore
        this.$el
      );
      this.$emit("create", this._chart);
    },
  },
});
</script>
