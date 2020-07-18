<template>
  <div
    class="flex cursor-pointer btn"
    :class="{ 'btn primary': isSelected }"
    @click="$emit('pick')"
  >
    <!-- <span -->
    <!--   class="h-4 w-4 mr-3 border bg-white" -->
    <!--   :class="{ 'bg-blue-500': isSelected }" -->
    <!-- ></span> -->
    <span>{{ label }}</span>
    <!-- <span class="ml-auto h-6 w-6 border">V</span> -->
  </div>
</template>

<script>
export default {
  props: ['label', 'isSelected'],
}
</script>
