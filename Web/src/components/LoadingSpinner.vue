<script setup lang="ts">
defineProps<{ show?: boolean }>()
</script>

<template>
  <div v-if="show" class="flex justify-center py-12">
    <n-spin size="medium">
      <template #description>
        <span class="text-sm text-gray-400 dark:text-gray-500">加载中…</span>
      </template>
    </n-spin>
  </div>
</template>
