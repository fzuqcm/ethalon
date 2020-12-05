export interface DeviceData {
  freq: number[]
  diss: number[]
  temp: number[]
}

export interface MeasurePoints {
  ampl: number[]
  phas: number[]
  freq: number[]
}

export interface Device {
  id: number
  name: string
  serial_number: string
  path: string
  data: DeviceData
  measurePoints: MeasurePoints
}

export interface State {
  timestamps: number[]
  devices: Device[]
  isUiBigger: boolean
  isPlotPaused: boolean
  isMeasuring: boolean
}

export interface DataPoint {
  freq: number
  diss: number
  temp: number
}

export interface MeasuredForDevice {
  dataPoint: DataPoint
  measurePoints: MeasurePoints
}

export interface MeasuredData {
  forDevices: MeasuredForDevice[]
  timestamp: number
}
