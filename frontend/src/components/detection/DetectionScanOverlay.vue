<template>
  <div v-if="active" class="scan-overlay"><div class="scan-line" /></div>
</template>

<script setup lang="ts">
defineProps<{ active?: boolean }>()
</script>
