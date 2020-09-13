<template>
  <div
    v-if="$store.state.editedDevice !== null"
    @close="$store.commit('setEditedDevice', null)"
    class="fixed inset-0 z-10 flex items-center justify-center"
    style="background: rgba(200, 200, 200, 0.5)"
  >
    <div class="bg-white shadow-xl border rounded p-8" style="width: 32rem">
      <form @submit.prevent>
        <label class="label">
          Name
          <input
            class="input"
            v-model="$store.state.editedDevice.name"
            @keypress.enter="$store.dispatch('saveDevice')"
          />
        </label>
        <label class="label">
          Calibrated frequecy
        </label>
        <span class="input">
          {{ $store.state.editedDevice.calibratedFrequency }} Hz
        </span>
        <label class="label">
          Port
        </label>
        <span class="input">{{ $store.state.editedDevice.path }}</span>
      </form>
      <!-- <slot /> -->
      <button
        class="btn primary mt-6 mr-4"
        @click="$store.dispatch('saveDevice')"
      >
        OK
      </button>
      <button class="btn mt-6" @click="$store.commit('setEditedDevice', null)">
        Cancel
      </button>
    </div>
  </div>
</template>
