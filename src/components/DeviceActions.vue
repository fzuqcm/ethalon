<template>
  <div class="border-l min-h-full p-2">
    <div class="grid grid-cols-2 gap-2">
      <button class="btn primary col-span-2" v-on:click="scanports">
        SCAN
      </button>
      <button class="btn primary col-span-2" v-on:click="initialize">
        START
      </button>
      <hr class="col-span-2" />
      <button @click="$store.commit('addToPlot', 'temperature')" class="btn">
        + <br />temperature
      </button>
      <button @click="$store.commit('addToPlot', 'dissipation')" class="btn">
        + <br />dissipation
      </button>
      <button @click="$store.commit('addToPlot', 'phase')" class="btn">
        + <br />phase
      </button>
      <button @click="$store.commit('addToPlot', 'magnitude')" class="btn">
        + <br />magnitude
      </button>
      <hr class="col-span-2" />
      <button
        @click="$store.commit('removeFromPlot', 'temperature')"
        class="btn"
      >
        - <br />temperature
      </button>
      <button
        @click="$store.commit('removeFromPlot', 'dissipation')"
        class="btn"
      >
        - <br />dissipation
      </button>
      <button @click="$store.commit('removeFromPlot', 'phase')" class="btn">
        - <br />phase
      </button>
      <button @click="$store.commit('removeFromPlot', 'magnitude')" class="btn">
        - <br />magnitude
      </button>
    </div>
  </div>
</template>

<script>
const INIT_SEQUENCE = `${10 ** 6};${5 * 10 ** 7};${10 ** 3}\n`

const DEVICE_MATCH = {
  manufacturer: 'Teensyduino',
}

const DEVICE_TEMPLATE = {
  path: 'IMPLEMENT',
  label: 'IMPLEMENT',
  selected: false,
  running: false,
  plots: {
    phase: true,
    magnitude: true,
    dissipation: true,
    temperature: true,
  },
  datapoints: {
    phase: [],
    magnitude: [],
    dissipation: [],
    temperature: [],
  },
}

const DATA_1_KEY = 'magnitude'
const DATA_2_KEY = 'phase'

const DATAPOINT_TEMPLATE = {
  magnitude: null,
  phase: null,
  dissipation: null,
  temperature: null,
}

const BUFFER_FLUSH_THRESHOLD = 500

export default {
  methods: {
    scanports: function() {
      const serial = window.serialport

      serial.list().then(ports => {
        for (let port of ports) {

          let match = Object.keys(DEVICE_MATCH).every(
            key => DEVICE_MATCH[key] === port[key]
          )

          if (!match) continue

          let device = {
            ...DEVICE_TEMPLATE,
            ...{ label: port.path, path: port.path },
          }

          this.$store.commit('addDevice', device)
        }
      })
    },

    initialize: function() {
      const serial = window.serialport
      const Readline = serial.parsers.Readline
      const parser = new Readline()

      let selected = this.$store.getters.selectedDevices

      for (let device of selected) {
        if (device.running) {
          console.log(`Device ${device.label} already initialized, skipping...`)
          continue
        }

        const path = device.path
        const port = new serial(path, { baudRate: 115200 })

        port.write(INIT_SEQUENCE, function(err) {
          if (err) {
            return console.log('Error on write: ', err.message)
          }
          console.log(`Init sequence written to ${device.label}`)
        })

        this.$store.commit('tagRunning', device.path)

        port.pipe(parser)

        let buffer = []

        parser.on('data', data => {
          let datapoint = { ...DATAPOINT_TEMPLATE }
          let point = data.split(';')
          datapoint[DATA_1_KEY] = point[0]
          datapoint[DATA_2_KEY] = point[1]

          buffer.push(datapoint)

          if (buffer.length >= BUFFER_FLUSH_THRESHOLD) {
            this.$store.commit('addDataPoints', { device, buffer })
            buffer = []
          }
        })
      }
    },
  },
}
</script>
