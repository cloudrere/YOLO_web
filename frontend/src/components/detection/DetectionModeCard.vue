<template>
  <router-link :to="to" class="detect-mode-card">
    <div class="mode-icon">{{ icon }}</div>
    <h3>{{ title }}</h3>
    <p>{{ desc }}</p>
    <div class="mode-arrow">{{ action }} →</div>
  </router-link>
</template>

<script setup lang="ts">
defineProps<{
  to: string
  icon: string
  title: string
  desc: string
  action: string
}>()
</script>
