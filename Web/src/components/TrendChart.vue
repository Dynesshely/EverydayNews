<script setup lang="ts">
import { useAppStore } from '../stores/app'
import { loadSearchChunk } from '../api/loader'
import type { SearchEntry, Platform } from '../types'
import { platformLabel } from '../utils/format'
import Fuse from 'fuse.js'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, DataZoomComponent, TitleComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { EChartsOption } from 'echarts'

use([LineChart, GridComponent, TooltipComponent, DataZoomComponent, TitleComponent, LegendComponent, CanvasRenderer])

const store = useAppStore()
const trendTitle = ref('')
const trendLoading = ref(false)
interface TrendPoint { date: string; rank: number; platform: Platform }
const trendData = ref<TrendPoint[]>([])

const fuseInstances = new Map<string, Fuse<SearchEntry>>()

async function getFuse(chunkKey: string): Promise<Fuse<SearchEntry>> {
  if (fuseInstances.has(chunkKey)) return fuseInstances.get(chunkKey)!
  const data = await loadSearchChunk(chunkKey)
  const fuse = new Fuse(data, { keys: ['title'], threshold: 0.0, minMatchCharLength: 2 })
  fuseInstances.set(chunkKey, fuse)
  return fuse
}

function getChunkKeys(): string[] {
  if (!store.index) return []
  const dates = Object.keys(store.index.days)
  const yearMonths = new Set<string>()
  for (const d of dates) {
    yearMonths.add(d.slice(0, 4))
  }
  const keys: string[] = []
  for (const y of yearMonths) {
    keys.push(`baidu/${y}`, `weibo/${y}`)
  }
  for (const d of dates) {
    keys.push(`bilibili/${d.slice(0, 6)}`)
  }
  return [...new Set(keys)]
}

async function showTrend(title: string) {
  trendTitle.value = title
  trendLoading.value = true
  trendData.value = []

  const chunkKeys = getChunkKeys()
  const results: SearchEntry[] = []

  const batchSize = 5
  for (let i = 0; i < chunkKeys.length; i += batchSize) {
    const batch = chunkKeys.slice(i, i + batchSize)
    const fuseList = await Promise.all(
      batch.map(k => getFuse(k).catch(() => null)),
    )
    for (const fuse of fuseList) {
      if (!fuse) continue
      const r = fuse.search(title, { limit: 200 })
      results.push(...r.map(rr => rr.item))
    }
  }

  // Deduplicate and convert
  const seen = new Set<string>()
  results.forEach(r => {
    const key = `${r.date}-${r.platform}-${r.minutes}`
    if (!seen.has(key)) {
      seen.add(key)
      trendData.value.push({ date: r.date, rank: r.rank, platform: r.platform })
    }
  })

  trendData.value.sort((a, b) => a.date.localeCompare(b.date) || (a.rank as number) - (b.rank as number))
  trendLoading.value = false
}

const isDark = computed(() => store.themeMode === 'dark')

const chartOption = computed<EChartsOption>(() => {
  const byPlatform = new Map<string, TrendPoint[]>()
  for (const item of trendData.value) {
    if (!byPlatform.has(item.platform)) byPlatform.set(item.platform, [])
    byPlatform.get(item.platform)!.push(item)
  }

  const colors: Record<string, string> = {
    baidu: '#ef4444',
    weibo: '#f97316',
    bilibili: '#3b82f6',
  }

  const series: EChartsOption['series'] = []
  const allDates = [...new Set(trendData.value.map(d => d.date))].sort()

  const textColor = isDark.value ? '#e5e7eb' : '#374151'
  const subTextColor = isDark.value ? '#9ca3af' : '#6b7280'
  const lineColor = isDark.value ? 'rgba(255, 255, 255, 0.08)' : 'rgba(15, 23, 42, 0.08)'

  for (const [platform, items] of byPlatform) {
    series.push({
      name: platformLabel(platform),
      type: 'line',
      data: items.map(i => [i.date, i.rank]),
      smooth: true,
      symbol: 'none',
      lineStyle: { color: colors[platform] || '#6b7280', width: 2 },
      itemStyle: { color: colors[platform] || '#6b7280' },
      emphasis: { focus: 'series' },
    })
  }

  return {
    title: {
      text: `"${trendTitle.value}" 排名趋势`,
      left: 'center',
      textStyle: { fontSize: 14, fontWeight: 600, color: textColor },
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: isDark.value ? '#1e2025' : '#ffffff',
      borderColor: isDark.value ? 'rgba(255, 255, 255, 0.12)' : 'rgba(15, 23, 42, 0.1)',
      textStyle: { color: textColor, fontSize: 12 },
      formatter: (params: unknown) => {
        const items = params as { seriesName: string; value: [string, number] }[]
        if (!items?.length) return ''
        const date = items[0].value[0]
        const y = date.slice(0, 4)
        const m = date.slice(4, 6)
        const d = date.slice(6, 8)
        return `<div class="text-sm">
          <div class="font-medium mb-1">${y}-${m}-${d}</div>
          ${items.map(i => `<div>${i.seriesName}: <b>#${i.value[1]}</b></div>`).join('')}
        </div>`
      },
    },
    legend: {
      top: 30,
      data: [...byPlatform.keys()].map(platformLabel),
      textStyle: { color: subTextColor, fontSize: 11 },
    },
    grid: { left: 50, right: 30, top: 70, bottom: 60 },
    xAxis: {
      type: 'category',
      data: allDates,
      axisLabel: {
        formatter: (val: string) => val.slice(4, 6) + '/' + val.slice(6, 8),
        rotate: 45,
        fontSize: 10,
        color: subTextColor,
      },
      axisLine: { lineStyle: { color: lineColor } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      inverse: true,
      name: '排名',
      minInterval: 1,
      nameTextStyle: { color: subTextColor, fontSize: 11 },
      axisLabel: { fontSize: 10, color: subTextColor },
      splitLine: { lineStyle: { color: lineColor } },
    },
    dataZoom: [
      {
        type: 'slider',
        bottom: 10,
        height: 20,
        borderColor: 'transparent',
        backgroundColor: isDark.value ? 'rgba(255, 255, 255, 0.04)' : 'rgba(15, 23, 42, 0.03)',
        fillerColor: isDark.value ? 'rgba(59, 130, 246, 0.25)' : 'rgba(59, 130, 246, 0.15)',
        handleStyle: { color: '#3b82f6' },
        moveHandleStyle: { color: '#3b82f6' },
        textStyle: { color: subTextColor, fontSize: 10 },
      },
      { type: 'inside' },
    ],
    series,
  }
})

// Expose showTrend to parent
defineExpose({ showTrend })

const emit = defineEmits<{
  (e: 'showTrend', title: string): void
}>()
</script>

<template>
  <div v-if="trendTitle" class="mt-8">
    <n-card size="small" class="trend-card shadow-sm">
      <template #header>
        <div class="flex items-center justify-between gap-3">
          <div class="min-w-0">
            <span class="text-sm font-semibold text-gray-900 dark:text-gray-100">
              趋势分析
            </span>
            <span class="ml-2 text-xs text-gray-400 dark:text-gray-500 truncate">
              「{{ trendTitle }}」在各平台的排名变化
            </span>
          </div>
          <n-button size="tiny" quaternary class="shrink-0" @click="trendTitle = ''">
            关闭
          </n-button>
        </div>
      </template>
      <n-spin :show="trendLoading">
        <v-chart
          v-if="trendData.length > 0"
          :option="chartOption"
          class="h-72 sm:h-80 lg:h-96 w-full"
          autoresize
        />
        <div v-else class="py-12 text-center">
          <p class="text-sm text-gray-400 dark:text-gray-500">
            暂无该话题的历史趋势数据
          </p>
        </div>
      </n-spin>
    </n-card>
  </div>
</template>

<style scoped>
.trend-card {
  --n-border-radius: 16px;
}
</style>
