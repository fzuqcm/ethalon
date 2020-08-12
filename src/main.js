import Vue from 'vue'
import App from './App.vue'
import store from './store'
import './assets/tailwind.css'

Vue.config.productionTip = false

//const serialport = require('serialport')
//
//
//serialport.list().then((ports) => {
//  console.log('ports', ports)
//}).catch(err => {
//})

new Vue({
  store,
  render: h => h(App),
}).$mount('#app')

export const knex = require('knex')({
  client: 'sqlite3',
  connection: () => ({
    filename: process.env.SQLITE_FILENAME,
  }),
})
