<script setup lang="ts">
import { useAppStore } from '../stores/app'
import type { Platform } from '../types'
import SnapshotTimeline from './SnapshotTimeline.vue'
import EmptyState from './EmptyState.vue'
import LoadingSpinner from './LoadingSpinner.vue'
import { platformLabel } from '../utils/format'

const store = useAppStore()

const emit = defineEmits<{
  (e: 'showTrend', title: string): void
}>()

function onShowTrend(title: string) {
  emit('showTrend', title)
}

function jumpToPlatform(platform: string) {
  store.setPlatform(platform as Platform)
}

const isAllPlatforms = computed(() => store.currentPlatform === 'all')

const cardStyle = (platform: string) => ({
  baidu: 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/30',
  weibo: 'text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-950/30',
  bilibili: 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/30',
}[platform] || '')

function cardLimit(platform: string): number | undefined {
  if (platform === 'bilibili') return undefined
  return 5
}

function cardMaxH(platform: string): string {
  if (platform === 'bilibili') return 'max-h-[55vh]'
  return 'max-h-[320px]'
}
</script>

<template>
  <div>
    <!-- Initial load: index not ready yet -->
    <LoadingSpinner v-if="store.indexLoading" :show="true" />

    <template v-else>
      <!-- All platforms view -->
      <div v-if="isAllPlatforms" class="flex flex-col gap-6">
        <!-- Static placeholder cards while data is loading -->
        <div v-if="store.dataLoading && store.dayDataList.length === 0" class="space-y-6">
          <div
            v-for="plat in ['baidu', 'weibo', 'bilibili']"
            :key="plat"
            class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-hidden"
          >
            <div class="px-4 py-3 font-medium text-sm border-b border-gray-100 dark:border-gray-700" :class="cardStyle(plat)">
              {{ platformLabel(plat) }}
            </div>
            <div class="p-6 flex justify-center">
              <n-spin size="small" />
            </div>
          </div>
        </div>

        <!-- Loaded cards -->
        <div
          v-for="dayData in store.dayDataList"
          :key="dayData.platform"
          class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-hidden"
        >
          <div
            class="px-4 py-3 font-medium text-sm border-b border-gray-100 dark:border-gray-700 flex items-center justify-between"
            :class="cardStyle(dayData.platform)"
          >
            <span>
              {{ platformLabel(dayData.platform) }}
              <span class="font-normal text-gray-400 dark:text-gray-500 ml-1">
                {{ dayData.snapshots.length }} 个快照
              </span>
            </span>
            <n-button
              size="tiny"
              quaternary
              @click="jumpToPlatform(dayData.platform)"
            >
              查看详情 →
            </n-button>
          </div>
          <div class="p-3 overflow-y-auto" :class="cardMaxH(dayData.platform)">
            <SnapshotTimeline
              :day-data="dayData"
              :limit="cardLimit(dayData.platform)"
              :horizontal="dayData.platform !== 'bilibili'"
              :max-items-bilibili="dayData.platform === 'bilibili' ? 3 : undefined"
              @show-trend="onShowTrend"
            />
          </div>
        </div>
      </div>

      <!-- Single platform: full-width -->
      <template v-else>
        <div v-if="store.dataLoading" class="flex justify-center py-12">
          <n-spin size="medium" />
        </div>
        <SnapshotTimeline
          v-else-if="store.dayDataList.length === 1"
          :day-data="store.dayDataList[0]"
          @show-trend="onShowTrend"
        />
        <EmptyState
          v-else
          title="无数据"
          description="该日期没有对应的热搜数据"
        />
      </template>
    </template>
  </div>
</template>
