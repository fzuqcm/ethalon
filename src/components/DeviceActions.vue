<template>
  <div class="border-l min-h-full p-2">
    <div class="grid grid-cols-2 gap-2">
      <button class="btn primary col-span-2">START</button>
      <hr class="col-span-2" />
      <button class="btn" @click="$store.commit('addToPlot', 'temperature')">
        + <br>temperature
      </button>
      <button class="btn" @click="$store.commit('addToPlot', 'dissipation')">
        + <br>dissipation
      </button>
      <button class="btn" @click="$store.commit('addToPlot', 'phase')">
        + <br>phase
      </button>
      <button class="btn" @click="$store.commit('addToPlot', 'magnitude')">
        + <br>magnitude
      </button>
      <hr class="col-span-2" />
      <button
        class="btn"
        @click="$store.commit('removeFromPlot', 'temperature')"
      >
        - <br>temperature
      </button>
      <button
        class="btn"
        @click="$store.commit('removeFromPlot', 'dissipation')"
      >
        - <br>dissipation
      </button>
      <button class="btn" @click="$store.commit('removeFromPlot', 'phase')">
        - <br>phase
      </button>
      <button class="btn" @click="$store.commit('removeFromPlot', 'magnitude')">
        - <br>magnitude
      </button>
    </div>
  </div>
</template>

<script>
export default {
  methods: {},
}
</script>
