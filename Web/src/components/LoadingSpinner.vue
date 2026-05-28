<script setup lang="ts">
defineProps<{ show?: boolean }>()
</script>

<template>
  <n-spin v-if="show" size="medium" class="flex justify-center py-12">
    <template #description>加载中...</template>
  </n-spin>
</template>
