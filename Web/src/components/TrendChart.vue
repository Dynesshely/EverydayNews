<script setup lang="ts">
import { useAppStore } from '../stores/app'
import { loadSearchChunk } from '../api/loader'
import type { SearchEntry, Platform } from '../types'
import { platformLabel } from '../utils/format'
import Fuse from 'fuse.js'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, DataZoomComponent, TitleComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { EChartsOption } from 'echarts'

use([LineChart, GridComponent, TooltipComponent, DataZoomComponent, TitleComponent, CanvasRenderer])

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
      textStyle: { fontSize: 14 },
    },
    tooltip: {
      trigger: 'axis',
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
    legend: { top: 30, data: [...byPlatform.keys()].map(platformLabel) },
    grid: { left: 50, right: 30, top: 70, bottom: 60 },
    xAxis: {
      type: 'category',
      data: allDates,
      axisLabel: {
        formatter: (val: string) => val.slice(4, 6) + '/' + val.slice(6, 8),
        rotate: 45,
        fontSize: 10,
      },
    },
    yAxis: {
      type: 'value',
      inverse: true,
      name: '排名',
      minInterval: 1,
      axisLabel: { fontSize: 10 },
    },
    dataZoom: [
      { type: 'slider', bottom: 10, height: 20 },
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
    <n-card size="small">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
            趋势分析
          </span>
          <n-button size="tiny" quaternary @click="trendTitle = ''">关闭</n-button>
        </div>
      </template>
      <n-spin :show="trendLoading">
        <v-chart
          v-if="trendData.length > 0"
          :option="chartOption"
          class="h-80 w-full"
          autoresize
        />
        <div v-else class="text-sm text-gray-400 dark:text-gray-500 py-8 text-center">
          暂无该话题的历史趋势数据
        </div>
      </n-spin>
    </n-card>
  </div>
</template>
