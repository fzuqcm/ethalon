<template>
  <div
    class="fixed inset-0 z-10 flex items-center justify-center"
    style="background: rgba(200, 200, 200, 0.5)"
  >
    <div class="bg-white shadow-xl border rounded p-8" style="width: 32rem">
      <slot />
      <!-- <button class="btn primary mt-6 mr-4" @click="$emit('ok')">OK</button> -->
      <button class="btn mt-6" @click="$emit('close')">Close</button>
    </div>
  </div>
</template>
