<script>
   import { devices, measurements } from '../store'
   import _ from 'lodash'
   import MeasurementInfo from './MeasurementInfo.svelte'
</script>

<div class="px-2">
   <h4>Measurements</h4>

   {#each _.entries($measurements) as [port, measurement]}
      <MeasurementInfo {measurement} />
   {/each}
</div>
