import Vue from 'vue'
import App from './App.vue'
import store from './store'
import './assets/tailwind.css'
import knexConfig from '../knexfile.js'

Vue.config.productionTip = false

new Vue({
  store,
  render: h => h(App),
}).$mount('#app')

export const knex = require('knex')(knexConfig.development)
