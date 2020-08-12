<template>
  <div class="border-r min-h-full">
    <div class="p-2 grid grid-col-1 gap-2">
      <device-list-item
        label="Select all"
        :isSelected="$store.state.selectAllDevices"
        @pick="$store.commit('selectAllDevices')"
      />
      <device-list-item
        v-for="d in $store.state.devices"
        :key="d.label"
        :label="d.label"
        :isSelected="d.selected"
        @pick="d.selected = !d.selected"
        @edit="editDevice(d)"
      />
      <full-modal v-if="device !== null" @close="device = null">
        <form>
          <label>
            <input v-model="device.label" />
          </label>
        </form>
      </full-modal>
    </div>
  </div>
</template>

<script>
import DeviceListItem from './DeviceListItem.vue'
import FullModal from './FullModal.vue'

export default {
  components: {
    DeviceListItem,
    FullModal,
  },
  data() {
    return {
      device: null,
    }
  },
  methods: {
    editDevice(device) {
      this.device = device
    },
  },
}
</script>
