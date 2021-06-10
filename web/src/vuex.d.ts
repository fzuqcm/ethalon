// import { ComponentCustomProperties } from 'vue'
import { Store } from 'vuex'
import { DictStr, Measurement } from './utils'

declare module '@vue/runtime-core' {
  interface State {
    measurements: DictStr<Measurement>
    isPlotPaused: boolean
    firstTime: number
  }

  interface ComponentCustomProperties {
    $store: Store<State>
  }
}