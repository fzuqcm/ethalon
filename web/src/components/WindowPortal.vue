<template>
  <div v-if="open">
    <!-- <slot /> -->
    <SignalPlot :height="height" :width="width" name="Testik" />
    <!-- <UploadVue :data="undefined" :options="" /> -->
  </div>
</template>

<script lang="ts">
import { defineComponent } from "@vue/runtime-core";
import SignalPlot from "./SignalPlot.vue";
import UplotVue from 'uplot-vue';

export default defineComponent({
  components: { SignalPlot, UplotVue },
  name: "WindowPortal",
  props: {
    open: {
      type: Boolean,
      default: false,
    },
    title: {
      type: String,
      default: "Window",
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
  data(): { windowRef: Window | null } {
    return {
      windowRef: null,
    };
  },
  watch: {
    open(newOpen) {
      if (newOpen) {
        this.openPortal();
      } else {
        this.closePortal();
      }
    },
  },
  methods: {
    openPortal() {
      this.windowRef = window.open(
        "",
        "",
        `width=${this.width},height=${this.height},left=${this.left},top=${this.top}`
      ) as Window;

      Array.from(window.document.head.children).forEach((element) => {
        (this.windowRef as Window).document.head.appendChild(element.cloneNode(true));
      });

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
  },
  mounted() {
    if (this.open) {
      this.openPortal();
    }
  },
  beforeUnmount() {
    if (this.windowRef) {
      this.closePortal();
    }
  },
});
</script>
