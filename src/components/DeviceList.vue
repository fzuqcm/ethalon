<template>
  <div class="border-r min-h-full">
    <div class="p-2 grid grid-col-1 gap-2">
      <device-list-item
        name="Select all"
        :isSelected="$store.state.areAllDevicesSelected"
        @pick="$store.commit('selectAllDevices')"
      />
      <device-list-item
        v-for="d in $store.state.devices"
        :key="d.serialNumber"
        :name="d.name"
        :isSelected="d.isSelected"
        @pick="d.isSelected = !d.isSelected"
        @edit="$store.commit('setEditedDevice', d)"
      />
    </div>
  </div>
</template>

<script>
import DeviceListItem from './DeviceListItem.vue'

export default {
  components: {
    DeviceListItem,
  },
}
</script>
