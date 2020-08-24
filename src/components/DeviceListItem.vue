<template>
  <div
    class="flex cursor-pointer btn"
    :class="{ 'btn primary': isSelected }"
    @click="$emit('pick')"
    @contextmenu.prevent="$emit('edit')"
  >
    <span>{{ name }}</span>
  </div>
</template>

<script>
export default {
  props: ['name', 'isSelected'],
}
</script>
