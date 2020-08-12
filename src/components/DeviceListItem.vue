<template>
  <div
    class="flex cursor-pointer btn"
    :class="{ 'btn primary': isSelected }"
    @click="$emit('pick')"
    @dblclick="$emit('edit')"
  >
    <span>{{ label }}</span>
  </div>
</template>

<script>
export default {
  props: ['label', 'isSelected'],
}
</script>
