<script setup lang="ts">
import { useAppStore } from '../stores/app'
import { loadSearchChunk } from '../api/loader'
import type { SearchEntry } from '../types'
import SearchResultItem from './SearchResultItem.vue'
import { Search } from '@vicons/carbon'
import Fuse from 'fuse.js'

const store = useAppStore()
const searchQuery = ref('')
const searchFuzzy = ref(true)
const searchResults = ref<SearchEntry[]>([])
const searching = ref(false)

const fuseInstances = new Map<string, Fuse<SearchEntry>>()

async function getFuse(chunkKey: string): Promise<Fuse<SearchEntry>> {
  if (fuseInstances.has(chunkKey)) return fuseInstances.get(chunkKey)!
  const data = await loadSearchChunk(chunkKey)
  const fuse = new Fuse(data, {
    keys: ['title'],
    threshold: searchFuzzy.value ? 0.4 : 0.0,
    distance: 100,
    minMatchCharLength: 2,
  })
  fuseInstances.set(chunkKey, fuse)
  return fuse
}

function getChunkKeys(): string[] {
  // Generate chunk keys for the current platform filter
  const platform = store.currentPlatform
  const platforms = platform === 'all' ? ['baidu', 'weibo', 'bilibili'] : [platform]
  const keys: string[] = []

  // Always search all years (chunks are small for Baidu/Weibo, monthly for Bilibili)
  for (const plat of platforms) {
    if (store.index) {
      const dates = Object.keys(store.index.days)
      const yearMonths = new Set<string>()
      for (const d of dates) {
        const chunk = plat === 'bilibili' ? d.slice(0, 6) : d.slice(0, 4)
        yearMonths.add(chunk)
      }
      for (const y of yearMonths) {
        keys.push(`${plat}/${y}`)
      }
    }
  }

  return keys
}

async function doSearch() {
  const q = searchQuery.value.trim()
  if (!q || q.length < 1) {
    searchResults.value = []
    store.searchResults = []
    return
  }
  searching.value = true

  const chunkKeys = getChunkKeys()
  const allResults: { entry: SearchEntry; score: number }[] = []

  const batchSize = 3
  for (let i = 0; i < chunkKeys.length; i += batchSize) {
    const batch = chunkKeys.slice(i, i + batchSize)
    const fuseList = await Promise.all(batch.map(k => getFuse(k).catch(() => null)))
    for (const fuse of fuseList) {
      if (!fuse) continue
      const results = fuse.search(q, { limit: 50 })
      for (const r of results) {
        allResults.push({ entry: r.item, score: r.score ?? 0 })
      }
    }
  }

  // Sort by date desc, score asc, then rank asc
  allResults.sort((a, b) =>
    b.entry.date.localeCompare(a.entry.date) ||
    a.score - b.score ||
    a.entry.rank - b.entry.rank,
  )
  const top = allResults.slice(0, 200)
  searchResults.value = top.map(r => r.entry)
  store.searchResults = searchResults.value
  searching.value = false
}

const debouncedSearch = useDebounceFn(doSearch, 300)

watch(searchQuery, () => debouncedSearch())
watch(() => store.currentPlatform, () => {
  fuseInstances.clear()
  if (searchQuery.value.trim()) doSearch()
})

const emit = defineEmits<{
  (e: 'showTrend', title: string): void
  (e: 'navigate', date: string, platform: string): void
}>()

function handleResultClick(entry: SearchEntry) {
  store.setDate(entry.date)
  store.setPlatform(entry.platform)
}
</script>

<template>
  <section class="en-card overflow-hidden">
    <div class="px-5 pt-5 pb-4 sm:px-6 sm:pt-6 sm:pb-5">
      <h2 class="text-base font-semibold text-gray-900 dark:text-gray-100">
        热搜档案搜索
      </h2>
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
        跨平台检索历史热搜标题，点击结果可跳转到对应日期与平台。
      </p>

      <div class="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center">
        <n-input
          v-model:value="searchQuery"
          placeholder="输入热搜关键词，例如：科技、赛事、人物…"
          clearable
          round
          size="large"
          class="flex-1"
        >
          <template #prefix>
            <n-icon :size="18"><Search /></n-icon>
          </template>
        </n-input>
        <div class="flex items-center gap-2 shrink-0 self-end sm:self-auto">
          <span class="text-xs text-gray-400 dark:text-gray-500 whitespace-nowrap">
            匹配方式
          </span>
          <n-switch v-model:value="searchFuzzy" size="medium">
            <template #checked>模糊匹配</template>
            <template #unchecked>精确匹配</template>
          </n-switch>
        </div>
      </div>
    </div>

    <div
      v-if="searchResults.length > 0 || (searchQuery.trim().length >= 1 || searching)"
      class="px-3 pb-3 sm:px-4 sm:pb-4"
    >
      <n-spin :show="searching" size="small">
        <div
          v-if="searchResults.length > 0"
          class="max-h-96 overflow-y-auto rounded-xl border border-gray-100 dark:border-white/10
                 divide-y divide-gray-100 dark:divide-white/5"
        >
          <SearchResultItem
            v-for="(entry, idx) in searchResults"
            :key="`${entry.date}-${entry.minutes}-${entry.platform}-${idx}`"
            :entry="entry"
            @click="handleResultClick"
          />
        </div>
        <div
          v-else-if="searchQuery.trim().length >= 1 && !searching"
          class="py-8 text-center rounded-xl border border-dashed border-gray-200 dark:border-white/10"
        >
          <p class="text-sm text-gray-400 dark:text-gray-500">
            未找到与「{{ searchQuery.trim() }}」匹配的热搜记录
          </p>
          <p class="mt-1 text-xs text-gray-300 dark:text-gray-600">
            尝试更换关键词，或切换为模糊匹配
          </p>
        </div>
      </n-spin>
    </div>
  </section>
</template>
