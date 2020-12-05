<template>
  <div class="border-b-2 flex">
    <button @click.prevent="scan">New</button>
    <button @click.prevent="$socket.emit('start')">Start</button>
    <button @click.prevent="$socket.emit('stop')">Stop</button>
    <button @click.prevent="$store.commit('toggleIsPlotPaused')">
      {{ $store.state.isPlotPaused ? 'Resume' : 'Pause' }} plot
    </button>
    <button @click.prevent="$socket.emit('getMeasurements')">Get</button>
    <button @click.prevent="$store.commit('toggleIsUiBigger')" class="ml-auto">
      Toggle bigger UI
    </button>
  </div>
</template>

<script>
export default {
  data() {
    return {
      clickedTimes: 0,
    }
  },
  sockets: {
    getMeasurements(all) {
      console.log(all)
    },
  },
  methods: {
    scan() {
      this.$store.commit('setDevices', [])
      this.$socket.emit('scan')
    },
  },
}
</script>
