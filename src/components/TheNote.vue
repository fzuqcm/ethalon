<template>
  <div v-if="$store.state.showNote" class="absolute inset-0 z-10 w-full">
    <textarea
      v-model="note"
      class="bg-gray-100 w-full h-full p-4 font-mono focus:outline-none"
    ></textarea>
  </div>
</template>

<script>
export default {
  computed: {
    note: {
      get() {
        return this.$store.state.note
      },
      set(value) {
        this.$store.commit('setNote', value)
      },
    },
  },
}
</script>
