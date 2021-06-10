import { io } from 'socket.io-client'
import { devices, measurements, signals } from './store'

let $devices = {}
devices.subscribe((data) => {
   // eslint-disable-next-line no-unused-vars
   $devices = data
})

let $measurements = {}
measurements.subscribe((data) => {
   // eslint-disable-next-line no-unused-vars
   $measurements = data
})

let $signals = {}
signals.subscribe((data) => {
   // eslint-disable-next-line no-unused-vars
   $signals = data
})

export const socket = io('http://localhost:5000/', {
   transports: ['websocket'],
})
