import duration from 'dayjs/plugin/duration'
import utc from 'dayjs/plugin/utc'
import dayjs from 'dayjs'
import '$lib/socket/on'

// import { browser } from '$app/env'
// if (browser) {
//    localStorage.debug = 'socket.io-client:socket'
// }

dayjs.extend(duration)
dayjs.extend(utc)
