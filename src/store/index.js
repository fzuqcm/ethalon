import Vue from 'vue'
import Vuex from 'vuex'
// import SerialPort from 'serialport'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    devices: [],
    devicess: [
      {
        path: '',
        selected: true,
        label: 'QCM 01',
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
      },
      {
        selected: true,
        label: 'QCM 02',
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
      },
    ],
    selectAllDevices: true,
  },
  mutations: {
    addDevice(state, device) {
      state.devices.push(device)
    },
    tagRunning(state, devicePath) {
      state.devices.find(device => device.path === devicePath).running = true
    },
    selectAllDevices(state) {
      state.selectAllDevices = !state.selectAllDevices
      state.devices.forEach(d => {
        d.selected = state.selectAllDevices
      })
    },
    addToPlot(state, name) {
      state.devices.forEach(d => {
        if (d.selected) {
          d.plots[name] = true
        }
      })
    },
    removeFromPlot(state, name) {
      state.devices.forEach(d => {
        if (d.selected) {
          d.plots[name] = false
        }
      })
    },
    addDataPoints(state, payload) {
      const device = payload.device
      const buffer = payload.buffer

      console.log(`Adding ${buffer.length} datapoints to ${payload.device.path}`)
      for (let datapoint of buffer) {
        for (let key of ['phase', 'magnitude', 'dissipation', 'temperature']) {
          if (datapoint[key] == null) continue
          device.datapoints[key].push(datapoint[key])
        }
      }
    },
    generateData(state) {
      state.devices.forEach(d => {
        ;['temperature', 'dissipation', 'phase', 'magnitude'].forEach(name => {
          d.datapoints[name] = Array.from({ length: 40 }, Math.random)
        })
      })
    },
  },
  actions: {
    scanSerialPorts() {
      // SerialPort.list().then(portInfos => {
      //   portInfos.forEach(console.log)
      // })
    },
  },
  getters: {
    devices: state => {
      return state.devices
    },
    deviceByPath: state => path => {
      return state.devices.find(device => device.path === path)
    },
    devicesInPlot: state => plotName => {
      return state.devices.filter(device => device.plots[plotName])
    },
    devicesDatapoints: state => plotName => {
      return state.devices.filter(device => device.datapoints[plotName])
    },
    selectedDevices: state => {
      return state.devices.filter(d => d.selected)
    },
  },
  modules: {},
})

// freq, temp, amplitude, dissipation
