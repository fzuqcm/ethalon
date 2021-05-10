import _ from 'lodash'
import { socket } from '../socket'
import { devices, measurements, rerenderPlot, signals } from '../store'

let $signals = {}
signals.subscribe((data) => {
   $signals = data
})

let $measurements = {}
measurements.subscribe((data) => {
   $measurements = data
})

socket.on('sync', (data) => {
   console.log('sync', data)
})

socket.on('scan', (data) => {
   console.log('scan', data)
})

socket.on('data', (data) => {
   _.entries(data).forEach(([port, { signal_point, measure_points }]) => {
      const signal = $signals[port]
      if (!signal) {
         return
      }

      const measurement = $measurements[signal.measurement]
      if (!measurement) {
         return
      }

      measurement.freq.push(signal_point.freq)
      measurement.diss.push(signal_point.diss)
      measurement.temp.push(signal_point.temp)
      measurement.time.push(signal_point.time)
      signal.measurePoints = measure_points
   })

   measurements.set($measurements)
   signals.set($signals)
})

socket.on('setup', signals.set)
socket.on('signals', signals.set)
socket.on('devices', devices.set)
socket.on('measurements', (data) => {
   measurements.set(data)
   rerenderPlot.set(true)
})
