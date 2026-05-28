<script setup lang="ts">
import type { SearchEntry } from '../types'
import { formatDate, platformLabel } from '../utils/format'

defineProps<{ entry: SearchEntry }>()

const emit = defineEmits<{
  (e: 'click', entry: SearchEntry): void
}>()

function getPlatformColor(platform: string) {
  const map: Record<string, string> = {
    baidu: '#ef4444',
    weibo: '#f97316',
    bilibili: '#3b82f6',
  }
  return map[platform] || '#6b7280'
}

function minutesToTime(m: number): string {
  const h = Math.floor(m / 60)
  const min = m % 60
  return `${String(h).padStart(2, '0')}:${String(min).padStart(2, '0')}`
}
</script>

<template>
  <div
    class="flex items-center gap-3 px-4 py-3 rounded-lg bg-white dark:bg-gray-800
           border border-gray-100 dark:border-gray-700 cursor-pointer
           hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
    @click="emit('click', entry)"
  >
    <n-tag
      size="small"
      :color="{ color: getPlatformColor(entry.platform), textColor: '#fff', borderColor: getPlatformColor(entry.platform) }"
    >
      {{ platformLabel(entry.platform) }}
    </n-tag>
    <span class="text-sm text-gray-400 dark:text-gray-500 w-8 text-right">
      #{{ entry.rank }}
    </span>
    <span class="text-sm font-medium text-gray-900 dark:text-gray-100 flex-1 truncate">
      {{ entry.title }}
    </span>
    <span class="text-xs text-gray-400 dark:text-gray-500 whitespace-nowrap">
      {{ formatDate(entry.date) }} {{ minutesToTime(entry.minutes) }}
    </span>
  </div>
</template>
