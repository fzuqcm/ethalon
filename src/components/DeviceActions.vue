<template>
  <div class="min-h-full p-2">
    <div class="grid grid-cols-2 gap-2">
      <button
        class="btn primary col-span-2"
        v-on:click="$store.dispatch('startMeasuring')"
      >
        START
      </button>
      <button
        class="btn primary col-span-2"
        v-on:click="$store.dispatch('stopMeasuring')"
      >
        STOP
      </button>
      <button
        class="btn primary col-span-2"
        @click="$store.dispatch('exportMeasurements')"
      >
        Export
      </button>
      <button
        class="btn primary col-span-2"
        @click="$store.dispatch('calibrateDevices')"
      >
        Calibrate
      </button>
      <button
        class="btn primary col-span-2"
        @click="$store.dispatch('scanSerialPorts')"
      >
        Scan
      </button>
      <button class="btn col-span-2" @click="$store.commit('toggleFontSize')">
        Font size
      </button>
      <hr class="col-span-2" />
      <button @click="$store.commit('addToPlot', 'frequency')" class="btn">
        + <br />freq
      </button>
      <button @click="$store.commit('addToPlot', 'dissipation')" class="btn">
        + <br />diss
      </button>
      <button @click="$store.commit('addToPlot', 'phase')" class="btn">
        + <br />phase
      </button>
      <button @click="$store.commit('addToPlot', 'temperature')" class="btn">
        + <br />temp
      </button>
      <hr class="col-span-2" />
      <button class="btn" @click="$store.commit('removeFromPlot', 'frequency')">
        - <br />freq
      </button>
      <button
        @click="$store.commit('removeFromPlot', 'dissipation')"
        class="btn"
      >
        - <br />diss
      </button>
      <button class="btn" @click="$store.commit('removeFromPlot', 'phase')">
        - <br />phase
      </button>
      <button
        class="btn"
        @click="$store.commit('removeFromPlot', 'temperature')"
      >
        - <br />temp
      </button>
    </div>
  </div>
</template>
