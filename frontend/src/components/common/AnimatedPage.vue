<template>
  <Transition name="slide-up" appear>
    <div class="animated-page">
      <slot />
    </div>
  </Transition>
</template>

<script setup lang="ts">
</script>

<style scoped>
.animated-page { min-height: 0; }
</style>
