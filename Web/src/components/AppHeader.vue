<script setup lang="ts">
import { useAppStore } from '../stores/app'
import { Sun, Moon } from '@vicons/carbon'

const store = useAppStore()
</script>

<template>
  <div class="flex items-center justify-between">
    <div class="flex items-center gap-3">
      <h1 class="text-xl font-bold text-gray-900 dark:text-gray-100">
        EverydayNews
      </h1>
      <span class="text-sm text-gray-500 dark:text-gray-400">
        热搜归档
      </span>
    </div>
    <div class="flex items-center gap-4">
      <span
        v-if="store.meta"
        class="text-xs text-gray-400 dark:text-gray-500 hidden sm:inline"
      >
        {{ store.meta.dateRange[0] }} ~ {{ store.meta.dateRange[1] }}
        · {{ store.meta.totalDays }} 天
      </span>
      <n-button
        quaternary
        circle
        @click="store.toggleTheme()"
        :title="store.themeMode === 'light' ? '切换暗色模式' : '切换亮色模式'"
      >
        <template #icon>
          <n-icon v-if="store.themeMode === 'light'"><Sun /></n-icon>
          <n-icon v-else><Moon /></n-icon>
        </template>
      </n-button>
    </div>
  </div>
</template>
