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

export const NOTIFICATION_TIMEOUT = 3000
export const CSV_DELIMITER = ','
export const BIG_FONT_SIZE = 24
export const NORMAL_FONT_SIZE = 16

async function measureDataPoint(device, { start, stop, step }) {
  const serial = window.serialport
  const parser = new serial.parsers.Readline()
  const port = new serial(device.path, { baudRate: 115200 })

  port.write(`${start};${stop};${step}\n`, function(err) {
    if (err) {
      return console.log('Error on write: ', err.message)
    }
  })

  port.pipe(parser)

  return new Promise(resolve => {
    const bufferMagnitude = []
    const bufferPhase = []

    parser.on('data', data => {
      const point = data.split(';')

      if (data.includes('s')) {
        port.close()

        const maxMagnitude = _.max(bufferMagnitude)
        const maxMagnitudeIndex = bufferMagnitude.indexOf(maxMagnitude)
        const phase = _.toSafeInteger(bufferPhase[maxMagnitudeIndex])
        const frequency = start + step * maxMagnitudeIndex

        return resolve({
          frequency,
          phase,
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
    calibratedFrequency: 0,
    plots: {
      phase: true,
      frequency: true,
      dissipation: true,
      temperature: true,
    },
  }
}

export default new Vuex.Store({
  state: {
    logs: [],
    devices: [],
    dataPoints: [],
    areAllDevicesSelected: true,
    editedDevice: null,
    fontSize: NORMAL_FONT_SIZE,
  },
  mutations: {
    toggleFontSize(state) {
      if (state.fontSize === NORMAL_FONT_SIZE) {
        state.fontSize = BIG_FONT_SIZE
      } else {
        state.fontSize = NORMAL_FONT_SIZE
      }

      document.documentElement.style.fontSize = state.fontSize + 'px'
    },
    setDevices(state, devices) {
      state.devices = devices
    },
    setEditedDevice(state, editedDevice) {
      state.editedDevice = editedDevice
    },
    setMeasuring(state, isMeasuring) {
      state.isMeasuring = isMeasuring
    },
    log(state, message) {
      const entry = {
        type: 'info',
        isRead: false,
        id: _.uniqueId(),
        message,
      }

      state.logs.push(entry)

      setTimeout(() => {
        entry.isRead = true
      }, NOTIFICATION_TIMEOUT)
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
    addDataPoints(state, dataPoints) {
      state.dataPoints.push({
        timestamp: moment(),
        devices: dataPoints,
      })
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
        }

        devices.sort((a, b) => a.name > b.name)
        context.commit('setDevices', devices)
        context.commit('log', 'Scan was completed')
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
      context.commit(
        'log',
        `Device ${context.state.editedDevice.name} has been saved`
      )
    },
    async calibrateDevices(context) {
      const message = {
        start: 10 ** 7 - 10 ** 5,
        stop: 10 ** 7 + 10 ** 5,
        step: 10 ** 3,
      }

      for (const device of context.state.devices) {
        const dataPoint = await measureDataPoint(device, message)

        device.calibratedFrequency = dataPoint.frequency
      }

      context.commit('setDevices', [...context.state.devices])
      context.commit('log', 'All devices has been calibrated')
    },
    async startMeasuring(context) {
      for (const device of context.state.devices) {
        if (device.calibratedFrequency === 0) {
          context.commit('log', `Device ${device.name} is not calibrated`)
          return
        }
      }

      context.commit('setMeasuring', true)
      context.commit('log', 'Measuring has been started')
      context.dispatch('measure')
    },
    async stopMeasuring(context) {
      context.commit('setMeasuring', false)
      context.commit('log', 'Measuring has been stopped')
    },
    async measure(context) {
      const promises = []
      for (const device of context.state.devices) {
        const freq = device.calibratedFrequency
        const message = {
          start: freq - 10 ** 5,
          stop: freq + 10 ** 5,
          step: 40,
        }

        promises.push(measureDataPoint(device, message))
      }

      Promise.all(promises).then(values => {
        context.commit('addDataPoints', values)

        if (context.state.isMeasuring) {
          context.dispatch('measure')
        }
      })
    },
    async exportMeasurements(context) {
      if (!context.state.isMeasuring) {
        const rows = []
        let cols = ['Date', 'Time', 'Relative time']
        for (const device of context.state.devices) {
          for (const column of ['temperature', 'frequency', 'dissipation']) {
            cols.push(`${device.name} ${column}`)
          }
        }
        rows.push(cols.join(CSV_DELIMITER).replace(/\s/g, '_'))

        let firstCols = null
        for (const dataPoint of context.state.dataPoints) {
          cols = []
          cols.push(dataPoint.timestamp.format('YYYY-MM-DD'))
          cols.push(dataPoint.timestamp.format('HH:mm:ss.SSS'))
          cols.push(
            firstCols
              ? moment(
                  dataPoint.timestamp -
                    moment(firstCols[0] + ' ' + firstCols[1])
                ).format('X.SSS')
              : '0.000'
          )

          for (const values of dataPoint.devices) {
            cols.push(values.temperature)
            cols.push(values.frequency)
            cols.push(values.dissipation)
          }

          rows.push(cols.join(CSV_DELIMITER))

          if (!firstCols) {
            firstCols = cols
          }
        }

        const csvContent = rows.join('\n')

        dialog
          .showSaveDialog({
            defaultPath:
              moment().format('YYYY-MM-DD_HH-mm-ss') + '_fundamental.csv',
          })
          .then(({ filePath }) => {
            console.log(filePath)
            fs.writeFileSync(filePath, csvContent, 'utf-8')

            context.commit('log', 'Export was saved to ' + filePath)
          })
          .catch(() => {
            context.commit('log', 'Export was NOT saved')
          })
      } else {
        context.commit(
          'log',
          'Export was not initialized due to active measurement'
        )
      }
    },
  },
  getters: {
    devices: state => {
      return state.devices
    },
    getPlotByName: state => plotName => {
      const devices = state.devices.map(device => {
        return {
          x: [],
          y: [],
          name: device.name,
        }
      })

      let startedAt = null
      for (const dataPoint of state.dataPoints) {
        if (!startedAt) {
          startedAt = dataPoint.timestamp
        }
        for (const i in dataPoint.devices) {
          devices[i].x.push(
            moment(dataPoint.timestamp - startedAt).format('X.SSS')
          )
          devices[i].y.push(dataPoint.devices[i][plotName])
        }
      }

      return devices
    },
    selectedDevices: state => {
      return state.devices.filter(d => d.isSelected)
    },
  },
  modules: {},
})
