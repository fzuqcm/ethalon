import Vue from 'vue'
import Vuex from 'vuex'
// import SerialPort from 'serialport'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    devices: [
      { sel: false, label: 'QCM 01', x: [], y: [] },
      { sel: true, label: 'QCM 02', x: [], y: [] },
    ],
    selectAllDevices: true,
  },
  mutations: {
    selectAllDevices(state) {
      state.selectAllDevices = !state.selectAllDevices
      state.devices.forEach(d => {
        d.sel = state.selectAllDevices
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
  modules: {},
})
