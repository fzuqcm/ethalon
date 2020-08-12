export const plotMixin = {
  computed: {
    id() {
      console.log(this)
      return 'yaabs'
    },
  },
  methods: {
    lineTrace(x, y) {
      return {
        x,
        y,
        type: 'scatter',
      }
    },
  },
}
