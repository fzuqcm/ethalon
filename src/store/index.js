import Vue from 'vue'
import Vuex from 'vuex'
import { knex } from '../main'
import _ from 'lodash'
import { remote } from 'electron'
// import { dialog } from 'electron'
import fs from 'fs'
import path from 'path'
import moment from 'moment'

const dialog = remote.dialog

Vue.use(Vuex)

export const NOTIFICATION_TIMEOUT = 3000
export const SIMULATION_TIMEOUT = 600
export const CSV_DELIMITER = ','
export const BIG_FONT_SIZE = 24
export const NORMAL_FONT_SIZE = 16
export const DISSIPATION_PERCENT = 0.707
export const CALIBRATION_MESSAGE = {
  start: 10 ** 7 - 10 ** 5,
  stop: 10 ** 7 + 10 ** 5,
  step: 10 ** 3,
}

async function measureDataPoint(device, { start, stop, step }) {
  device.start(start, stop, step)

  const getFreq = index => start + step * index

  return new Promise(resolve => {
    const bufferMagnitude = []
    const bufferPhase = []

    device.data(data => {
      const point = data.split(';')

      if (data.includes('s')) {
        device.stop()

        const maxMagnitude = _.max(bufferMagnitude)
        const maxMagnitudeIndex = bufferMagnitude.indexOf(maxMagnitude)
        const phase = _.toSafeInteger(bufferPhase[maxMagnitudeIndex])
        const frequency = start + step * maxMagnitudeIndex

        let minIndex = maxMagnitudeIndex
        let maxIndex = maxMagnitudeIndex
        let m = 0
        let c = 0
        let minLeading = 0
        let maxLeading = 0

        while (bufferMagnitude[minIndex] > DISSIPATION_PERCENT * maxMagnitude) {
          if (minIndex < 1) {
            break
          }

          minIndex = minIndex - 1
        }

        m =
          (bufferMagnitude[minIndex + 1] - bufferMagnitude[minIndex]) /
          (getFreq(minIndex + 1) - getFreq(minIndex))
        c = bufferMagnitude[minIndex] - getFreq(minIndex) * m
        minLeading = (DISSIPATION_PERCENT * maxMagnitude - c) / m

        while (bufferMagnitude[maxIndex] > DISSIPATION_PERCENT * maxMagnitude) {
          if (maxIndex >= bufferMagnitude.length) {
            break
          }

          maxIndex = maxIndex + 1
        }

        m =
          (bufferMagnitude[maxIndex - 1] - bufferMagnitude[maxIndex]) /
          (getFreq(maxIndex - 1) - getFreq(maxIndex))
        c = bufferMagnitude[maxIndex] - getFreq(maxIndex) * m
        maxLeading = (DISSIPATION_PERCENT * maxMagnitude - c) / m

        let bandwidth = Math.abs(maxLeading - minLeading)
        let qualityFactor = getFreq(maxMagnitudeIndex) / bandwidth

        return resolve({
          frequency,
          phase,
          temperature: Number(point[0]),
          dissipation: 1 / qualityFactor,
        })
      }

      bufferMagnitude.push(Number(point[0]))
      bufferPhase.push(Number(point[1]))
    })
  })
}

class Device {
  constructor(name, path, serialNumber) {
    this.name = name
    this.path = path
    this.serialNumber = serialNumber
    this.isSelected = true
    this.calibratedFrequency = 0
    this.plots = {
      phase: true,
      frequency: true,
      dissipation: true,
      temperature: true,
    }
  }

  start() {
    throw new Error('Not implemented')
  }

  data() {
    throw new Error('Not implemented')
  }

  stop() {
    throw new Error('Not implemented')
  }
}

class SerialDevice extends Device {
  constructor(...props) {
    super(...props)
    const serial = window.serialport

    this.parser = new serial.parsers.Readline()
    this.port = new serial(this.device.path, { baudRate: 115200 })
    this.port.pipe(this.parser)
  }

  start(start, stop, step) {
    this.port.write(`${start};${stop};${step}\n`, function(err) {
      if (err) {
        return console.log('Error on write: ', err.message)
      }
    })
  }

  data(callback) {
    this.parser.on('data', callback)
  }

  stop() {
    this.port.close()
  }

  async calibrate() {
    const dataPoint = await measureDataPoint(this, CALIBRATION_MESSAGE)

    this.calibratedFrequency = dataPoint.frequency
  }
}

class SimulatedDevice extends Device {
  constructor(...props) {
    super(...props)
    this.testFiles = fs.readdirSync(this.path)
    this.testFiles.sort()
    this.counter = 0
    this.calibratedFrequency = 9983500
  }

  start() {
    // this.port.write(`${start};${stop};${step}\n`, function(err) {
    //   if (err) {
    //     return console.log('Error on write: ', err.message)
    //   }
    // })
  }

  data(callback) {
    const fsPath = path.join(this.path, this.testFiles[this.counter++])
    // console.log(fsPath)
    const testFile = fs.readFileSync(fsPath, { encoding: 'utf-8' })
    // console.log(testFile)
    const testValues = testFile.split('\n')

    for (const testValue of testValues) {
      if (testValue.includes('s')) {
        setTimeout(() => callback(testValue), SIMULATION_TIMEOUT)
        return
      }
      callback(testValue)
    }

    // let counter = 0
    // this.interval = setInterval(() => {
    //   // console.log(testValues[counter])
    //   callback(testValues[counter++])

    //   if (counter >= testValues.length) {
    //     console.log('Something is broken in simulated device')
    //   }
    // }, SIMULATION_TIMEOUT)
  }

  stop() {
    // clearInterval(this.interval)
  }

  async calibrate() {
    await setTimeout(() => {
      this.calibratedFrequency = 9983500
    }, SIMULATION_TIMEOUT)
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
    showNote: false,
    note: '',
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
    toggleShowNote(state) {
      state.showNote = !state.showNote
    },
    setNote(state, note) {
      state.note = note
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
        console.log(ports)
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

          devices.push(new SerialDevice(name, port.path, port.serialNumber))
        }

        // devices.sort((a, b) => a.name > b.name)
        context.commit('setDevices', devices)
        context.commit('log', 'Scan was completed')
      })
    },
    async addSimulatedDevice(context) {
      context.commit('setDevices', [
        ...context.state.devices,
        new SimulatedDevice('Simulated', 'test_outputs', 'simulation'),
      ])
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
      // const message = {
      //   start: 10 ** 7 - 10 ** 5,
      //   stop: 10 ** 7 + 10 ** 5,
      //   step: 10 ** 3,
      // }

      for (const device of context.state.devices) {
        await device.calibrate()
        // const dataPoint = await measureDataPoint(device, message)

        // device.calibratedFrequency = dataPoint.frequency
      }

      context.commit('setDevices', [...context.state.devices])
      context.commit('log', 'All devices has been calibrated')
    },
    async startMeasuring(context) {
      for (const device of context.state.devices) {
        if (!device.calibratedFrequency) {
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
          start: freq - 10 ** 4,
          stop: freq + 10 ** 4,
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
      // console.log(plotName)
      const devices = state.devices
        // .filter(device => device.plots[plotName])
        .map(device => {
          if (!device.plots[plotName]) {
            return null
          }

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
          if (!devices[i]) {
            continue
          }

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
