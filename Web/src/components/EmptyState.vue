<script setup lang="ts">
defineProps<{
  title?: string
  description?: string
}>()
</script>

<template>
  <div class="py-12 text-center">
    <p v-if="title" class="text-lg font-semibold text-gray-500 dark:text-gray-400 mb-2">
      {{ title }}
    </p>
    <n-empty :description="description || '暂无数据'" />
  </div>
</template>
