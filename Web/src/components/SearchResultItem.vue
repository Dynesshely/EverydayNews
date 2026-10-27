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

function getPlatformTagColor(platform: string) {
  const color = getPlatformColor(platform)
  return { color: color + '1a', textColor: color }
}

function minutesToTime(m: number): string {
  const h = Math.floor(m / 60)
  const min = m % 60
  return `${String(h).padStart(2, '0')}:${String(min).padStart(2, '0')}`
}
</script>

<template>
  <button
    type="button"
    class="w-full flex items-center gap-3 px-4 py-3 text-left cursor-pointer
           transition-colors hover:bg-gray-50 dark:hover:bg-white/5
           focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset
           focus-visible:ring-blue-500/70"
    @click="emit('click', entry)"
  >
    <n-tag
      size="small"
      round
      :bordered="false"
      :color="getPlatformTagColor(entry.platform)"
      class="shrink-0"
    >
      {{ platformLabel(entry.platform) }}
    </n-tag>
    <span
      class="shrink-0 w-8 text-right text-xs tabular-nums text-gray-400 dark:text-gray-500"
    >
      #{{ entry.rank }}
    </span>
    <span
      class="min-w-0 flex-1 truncate text-sm font-medium text-gray-900 dark:text-gray-100"
    >
      {{ entry.title }}
    </span>
    <span class="shrink-0 text-xs text-gray-400 dark:text-gray-500 whitespace-nowrap">
      {{ formatDate(entry.date) }}<span class="hidden sm:inline">&nbsp;{{ minutesToTime(entry.minutes) }}</span>
    </span>
  </button>
</template>
