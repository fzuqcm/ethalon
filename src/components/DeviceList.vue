<template>
  <div class="min-h-full">
    <div class="p-2 grid grid-col-1 gap-2">
      <div
        class="flex cursor-pointer btn"
        :class="{ 'btn primary': $store.state.areAllDevicesSelected }"
        @click="$store.commit('selectAllDevices')"
      >
        <span>Select all</span>
      </div>
      <div
        v-for="d in $store.state.devices"
        :key="d.serialNumber"
        class="flex cursor-pointer btn"
        :class="{ 'btn primary': d.isSelected }"
        @click="d.isSelected = !d.isSelected"
        @contextmenu.prevent="$store.commit('setEditedDevice', d)"
      >
        <span>{{ d.name }}</span>
      </div>
    </div>
  </div>
</template>
