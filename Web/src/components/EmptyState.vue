<script setup lang="ts">
defineProps<{
  title?: string
  description?: string
}>()
</script>

<template>
  <div
    class="py-14 px-6 text-center rounded-2xl border border-dashed
           border-en-border bg-en-surface"
  >
    <p
      v-if="title"
      class="text-base font-semibold text-gray-700 dark:text-gray-200 mb-1"
    >
      {{ title }}
    </p>
    <n-empty :description="description || '暂无数据'" />
  </div>
</template>
