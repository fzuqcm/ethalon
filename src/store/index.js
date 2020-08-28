import Vue from 'vue'
import Vuex from 'vuex'
import { knex } from '../main'
import _ from 'lodash'
import { remote } from 'electron'
// import { dialog } from 'electron'
import fs from 'fs'
import moment from 'moment'

const dialog = remote.dialog

Vue.use(Vuex)

async function measureDataPoint(device, message) {
  const serial = window.serialport
  const parser = new serial.parsers.Readline()

  // if (device.isBusy) {
  //   console.log(`Device ${device.name} is busy, skipping...`)
  //   continue
  // }

  const port = new serial(device.path, { baudRate: 115200 })
  port.write(message, function(err) {
    if (err) {
      return console.log('Error on write: ', err.message)
    }
    console.log(`Device ${device.label} has started to be busy`)
  })

  // context.commit('tagRunning', device.path)

  port.pipe(parser)

  return new Promise(resolve => {
    const bufferMagnitude = []
    const bufferPhase = []

    parser.on('data', data => {
      // console.log(data)
      const point = data.split(';')
      if (data.includes('s')) {
        port.close()
        return resolve({
          magnitude: _.toSafeInteger(_.max(bufferMagnitude)),
          phase: _.toSafeInteger(_.max(bufferPhase)),
          temperature: Number(point[0]),
          dissipation: 0,
        })
      }

      bufferMagnitude.push(Number(point[0]))
      bufferPhase.push(Number(point[1]))
    })
  })
}

const createDeviceTemplate = () => {
  return {
    name: '',
    path: '',
    serialNumber: '',
    isSelected: true,
    isMeasuring: false,
    calibratedFrequency: 0,
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
}

export default new Vuex.Store({
  state: {
    devices: [],
    areAllDevicesSelected: true,
    editedDevice: null,
  },
  mutations: {
    // addDevice(state, device) {
    //   state.devices.push(device)
    // },
    setDevices(state, devices) {
      state.devices = devices
    },
    setEditedDevice(state, editedDevice) {
      state.editedDevice = editedDevice
    },
    setMeasuring(state, isMeasuring) {
      state.isMeasuring = isMeasuring
    },
    tagRunning(state, devicePath) {
      state.devices.find(device => device.path === devicePath).running = true
    },
    selectAllDevices(state) {
      state.areAllDevicesSelected = !state.areAllDevicesSelected
      state.devices.forEach(d => {
        d.isSelected = state.areAllDevicesSelected
      })
    },
    addToPlot(state, name) {
      state.devices.forEach(d => {
        if (d.isSelected) {
          d.plots[name] = true
        }
      })
    },
    removeFromPlot(state, name) {
      state.devices.forEach(d => {
        if (d.isSelected) {
          d.plots[name] = false
        }
      })
    },
    addDataPoints(state, { dataPoint, device }) {
      // const device = payload.device
      // const buffer = payload.buffer

      // console.log(
      //   `Adding ${buffer.length} datapoints to ${device.path}`
      // )
      console.log(`Device ${device.name} has new data point`, dataPoint)
      for (let key of ['phase', 'magnitude', 'dissipation', 'temperature']) {
        if (dataPoint[key] == null) continue
        device.datapoints[key].push(dataPoint[key])
      }
      // device.datapoints.magnitude.push(res.magnitude)
      // device.datapoints.phase.push(res.phase)
      // device.datapoints.temperature.push(res.temperature)
      // device.datapoints.dissipation.push(res.dissipation)
    },
  },
  actions: {
    async scanSerialPorts(context) {
      const serial = window.serialport

      serial.list().then(async ports => {
        const devices = []
        for (const port of ports) {
          if (port.manufacturer !== 'Teensyduino') {
            continue
          }

          let name = ''
          let row = await knex
            .select(['name', 'serial_number'])
            .from('device')
            .where('serial_number', port.serialNumber)
            .first()

          if (!row) {
            name = 'QCM ' + port.serialNumber
            await knex('device').insert({
              name,
              serial_number: port.serialNumber,
            })
          } else {
            name = row.name
          }

          devices.push({
            ...createDeviceTemplate(),
            path: port.path,
            serialNumber: port.serialNumber,
            name,
          })

          console.log(port)
          console.log(row)
        }

        devices.sort((a, b) => a.name > b.name)
        context.commit('setDevices', devices)
      })
    },
    async saveDevice(context) {
      if (!context.state.editedDevice) {
        return
      }

      await knex('device')
        .where('serial_number', context.state.editedDevice.serialNumber)
        .update({
          name: context.state.editedDevice.name,
        })

      context.commit('setEditedDevice', null)
      // context.state.devices.sort((a, b) => a.name < b.name)
    },
    async calibrateDevices(context) {
      const MESSAGE = `${10 ** 7 - 10 ** 5};${10 ** 7 + 10 ** 5};${10 ** 3}\n`

      for (const device of context.state.devices) {
        const dataPoint = await measureDataPoint(device, MESSAGE)
        console.log(dataPoint)
        device.calibratedFrequency = 10006000
      }

      context.commit('setDevices', [...context.state.devices])
    },
    async startMeasuring(context) {
      for (const device of context.state.devices) {
        if (device.calibratedFrequency === 0) {
          alert(`Device ${device.name} is not calibrated`)
          return
        }
      }

      context.commit('setMeasuring', true)
      context.dispatch('measure')
    },
    async exportMeasurements(context) {
      if (!context.state.isMeasuring) {
        let csvContent = 'Date,Time,Relative_Time'
        for (const device of context.state.devices) {
          for (const x of [
            'temperature',
            'resonance frequency',
            'dissipation',
          ]) {
            csvContent += `,${device.name}_${x}`.replace(' ', '_')
          }
        }

        dialog
          .showSaveDialog({
            defaultPath:
              moment().format('YYYY-MMM-DD_HH-mm-ss') + '_fundamental.csv',
          })
          .then(({ filePath }) => {
            console.log(filePath)
            fs.writeFileSync(filePath, csvContent, 'utf-8')
          })
      }
    },
    async stopMeasuring(context) {
      context.commit('setMeasuring', false)
    },
    async measure(context) {
      const promises = []
      for (const device of context.state.devices) {
        const freq = device.calibratedFrequency
        const message = `${freq - 10 ** 5};${freq + 10 ** 5};40\n`
        promises.push(measureDataPoint(device, message))
      }

      Promise.all(promises).then(values => {
        for (const i in values) {
          context.commit('addDataPoints', {
            dataPoint: values[i],
            device: context.state.devices[i],
          })
        }

        if (context.state.isMeasuring) {
          context.dispatch('measure')
        }
      })
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
    measuringDevices: state => state.devices.filter(d => d.isMeasuring),
    selectedDevices: state => {
      return state.devices.filter(d => d.isSelected)
    },
  },
  modules: {},
})
