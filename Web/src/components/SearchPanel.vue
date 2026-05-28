<script setup lang="ts">
import { useAppStore } from '../stores/app'
import { loadSearchChunk } from '../api/loader'
import type { SearchEntry } from '../types'
import SearchResultItem from './SearchResultItem.vue'
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
  <div class="space-y-3">
    <div class="flex items-center gap-2">
      <n-input
        v-model:value="searchQuery"
        placeholder="搜索热搜标题..."
        clearable
        round
        size="medium"
        class="flex-1 max-w-lg"
      >
        <template #prefix>
          <n-icon><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg></n-icon>
        </template>
      </n-input>
      <n-switch
        v-model:value="searchFuzzy"
        :rail-style="() => ({})"
        size="medium"
      >
        <template #checked>模糊</template>
        <template #unchecked>精确</template>
      </n-switch>
    </div>

    <n-spin :show="searching" size="small">
      <div
        v-if="searchResults.length > 0"
        class="max-h-96 overflow-y-auto rounded-lg border border-gray-100 dark:border-gray-700 divide-y divide-gray-50 dark:divide-gray-700/50"
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
        class="text-sm text-gray-400 dark:text-gray-500 py-4 text-center"
      >
        未找到匹配结果
      </div>
    </n-spin>
  </div>
</template>
