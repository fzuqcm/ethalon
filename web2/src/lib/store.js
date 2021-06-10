import { writable } from 'svelte/store'

export const devices = writable({})

export const measurements = writable({})

export const signals = writable({})

export const isPaused = writable(false)

export const rerenderPlot = writable(false)

export const ports = writable([])
