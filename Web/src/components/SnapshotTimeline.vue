<script setup lang="ts">
import type { DayData } from '../types'
import SnapshotCard from './SnapshotCard.vue'
import BilibiliGrid from './BilibiliGrid.vue'

const p = defineProps<{
  dayData: DayData
  limit?: number
  horizontal?: boolean
  maxItemsBilibili?: number
}>()

const emit = defineEmits<{
  (e: 'showTrend', title: string): void
}>()
</script>

<template>
  <div :class="p.horizontal ? 'grid grid-cols-3 gap-4' : 'space-y-6'">
    <div
      v-for="snapshot in p.dayData.snapshots"
      :key="`${p.dayData.date}-${snapshot.minutes}`"
    >
      <div class="flex items-center gap-2 mb-2">
        <span class="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
          {{ snapshot.captureTime }}
        </span>
      </div>

      <SnapshotCard
        v-if="p.dayData.platform !== 'bilibili'"
        :items="snapshot.items"
        :platform="p.dayData.platform"
        :limit="p.limit"
      />
      <BilibiliGrid
        v-else
        :items="snapshot.items"
        :max-items="p.maxItemsBilibili ?? 12"
      />
    </div>
  </div>
</template>
