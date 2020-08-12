<template>
  <div class="border-l min-h-full p-2">
    <div class="grid grid-cols-2 gap-2">
      <button v-on:click="checkports" class="btn primary col-span-2">START</button>
    </div>
  </div>
</template>

<script>
//import serialport from 'serialport'
//const INIT_SEQUENCE=`${10 ** 6};${ 5 * (10 ** 7) };${10 ** 3}\n`

export default {

  methods: {
    checkports: function () {
      console.log(`Vue: window.serialport: ${window.serialport}`)
      const serial = window.serialport
      serial.list().then(ports => {
        console.log(ports)
      })
    }
}
}
</script>
