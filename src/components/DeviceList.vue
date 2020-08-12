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
