<template>
  <div v-if="logs.length > 0" class="absolute top-0 z-20 w-full">
    <button
      class="btn px-2 py-1 mt-2 mx-auto block text-left"
      style="width: 24rem"
      v-for="log in logs"
      :key="log.id"
      @click="log.isRead = true"
    >
      <span class="bg-blue-500 rounded px-1 text-sm">
        {{ log.type | upper }}
      </span>
      {{ log.message }}
    </button>
  </div>
</template>

<script>
export default {
  computed: {
    logs() {
      return this.$store.state.logs.filter(l => !l.isRead)
    },
  },
  filters: {
    upper(text) {
      return text.toUpperCase()
    },
  },
}
</script>
