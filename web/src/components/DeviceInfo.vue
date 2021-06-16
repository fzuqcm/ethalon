<template>
  <div class="p-1 block space-y-2">
    <label :for="m.port" class="flex hover:bg-gray-100 rounded-md">
      <input
        v-model="m.isSelected"
        type="checkbox"
        :name="m.port"
        :id="m.port"
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
            class="inline-block w-8 h-2 ml-2 mb-0.5"
            :style="'background-color: ' + COLORS[i]"
          />
        </p>
      </div>
    </label>
    <div class="flex space-x-2">
      <button @click="handleOpen('edit')" class="w-full bg-gray-400">
        Edit
      </button>
      <button @click="handleOpen('markers')" class="w-full bg-gray-400">
        Markers
      </button>
      <button @click="handleOpen('device')" class="w-full bg-gray-400">
        Device
      </button>
    </div>
    <div v-if="open === 'edit'" class="space-y-2">
      <input v-model="values.name" type="text" />
      <input v-model="values.deviceName" type="text" />
      <button class="w-full">Save</button>
    </div>
    <ul v-if="open === 'markers'">
      <li
        v-for="(marker, i) in m.data.markers"
        :key="marker.timestamp"
        class="flex"
      >
        <div class="flex-1">{{ marker.timestamp }}: {{ marker.name }}</div>
        <button @click="removeMarker(i, m)">&times;</button>
      </li>
      <li v-if="!m.data.markers.length">No markers</li>
    </ul>
    <div v-if="open === 'device'">
      <p class="ml-4"><b>Name:</b> {{ m.device.name }}</p>
      <p class="ml-4"><b>SN:</b> {{ m.device.serialNumber }}</p>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from "vue";
import { Measurement, socket, COLORS } from "../utils";

export default defineComponent({
  props: {
    m: {
      type: Object as PropType<Measurement>,
      required: true,
    },
    i: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      open: "",
      data: {
        name: this.m.data.name,
      },
      device: {
        name: this.m.device.name,
      },
      COLORS,
    };
  },
  methods: {
    removeMarker(index: number, m: Measurement) {
      this.$store.commit("removeMarker", { port: m.port, index });
      socket.emit("marker", { [m.port]: m.data.markers });
    },
    processData() {
      socket.emit("measurementData", { [this.m.port]: this.data });
    },
    handleOpen(name: string) {
      if (this.open === name) {
        this.open = "";
      } else {
        this.open = name;
      }
    },
  },
});
</script>
