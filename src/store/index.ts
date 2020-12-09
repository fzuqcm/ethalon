import { UI_BIGGER_BY } from '@/constants'
import { MeasuredData, Device, State } from '@/interfaces'
import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

export function deviceFactory(device: Partial<Device>) {
  device.data = {
    freq: [],
    diss: [],
    temp: [],
  }
  device.measurePoints = {
    freq: [],
    ampl: [],
    phas: [],
  }
}

export default new Vuex.Store({
  state: {
    timestamps: [],
    devices: [],
    isUiBigger: false,
    isPlotPaused: false,
    isMeasuring: false,
  } as State,
  mutations: {
    toggleIsUiBigger(state) {
      state.isUiBigger = !state.isUiBigger
      document.documentElement.style.fontSize =
        16 + Number(state.isUiBigger) * UI_BIGGER_BY + 'px'
    },
    toggleIsPlotPaused(state) {
      state.isPlotPaused = !state.isPlotPaused
    },
    setIsPlotPaused(state, isPlotPaused) {
      state.isPlotPaused = isPlotPaused
    },
    setDevices(state, devices: Partial<Device>[]) {
      devices.forEach(deviceFactory)
      state.devices = devices as Device[]
      state.timestamps = []
      state.isMeasuring = false
    },
    processMeasuredData(state, data: MeasuredData) {
      if (data.forDevices.length != state.devices.length) {
        throw new Error('Wrong data input format')
      }

      state.timestamps.push(data.timestamp)
      state.devices.forEach((device, idx) => {
        const { dataPoint, measurePoints } = data.forDevices[idx]
        device.data.freq.push(dataPoint.freq)
        device.data.diss.push(dataPoint.diss)
        device.data.temp.push(dataPoint.temp)
        device.measurePoints = measurePoints
      })
    },
  },
  actions: {},
  modules: {},
})
