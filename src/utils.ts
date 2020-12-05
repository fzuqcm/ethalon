import dayjs from 'dayjs'
import uPlot, { Series } from 'uplot'
import { COLORS } from './constants'
import { Device } from './interfaces'

export const seriesTimestamp = (against: number) => {
  return (self: uPlot, value: number) => {
    const millisDiffer = value - against
    const differ = dayjs.utc(millisDiffer).format('HH:mm:ss.SSS')
    const time = dayjs(value).format('HH:mm:ss.SSS')
    return `${time} (+${differ})`
  }
}

export const seriesDevices = (devices: Device[]) => {
  return devices.map(
    (device, idx) =>
      ({
        label: device.name,
        stroke: COLORS[idx],
      } as Series)
  )
}

export const axesTimestamps = (against: number) => {
  return (self: uPlot, values: number[]) => {
    const millisDiffer = values[values.length - 1] - against
    let format = 'ss.SSS'
    if (millisDiffer > 3600 * 1000) {
      format = 'HH:mm'
    } else if (millisDiffer > 60 * 1000) {
      format = 'mm:ss'
    }
    return values.map(value => dayjs.utc(value - against).format(format))
  }
}
