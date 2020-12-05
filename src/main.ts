import Vue from 'vue'
import App from './App.vue'
import store from './store'
import VueSocketIO, { VueSocketOptions } from 'vue-socket.io'
import 'uplot/dist/uPlot.min.css'
import './assets/tailwind.css'
import duration from 'dayjs/plugin/duration'
import utc from 'dayjs/plugin/utc'
import dayjs from 'dayjs'

dayjs.extend(duration)
dayjs.extend(utc)

Vue.use(
  new VueSocketIO({
    connection: 'http://localhost:8000/',
    options: { transports: ['websocket'] },
  } as VueSocketOptions)
)

Vue.config.productionTip = false

new Vue({
  store,
  render: h => h(App),
}).$mount('#app')
