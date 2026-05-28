import { defineStore } from 'pinia'
import type {
  IndexData, DayData, Platform, SearchEntry, ThemeMode, MetaInfo,
} from '../types'
import { loadIndex, loadDay, loadMeta } from '../api/loader'
import { darkTheme } from 'naive-ui'
import type { GlobalTheme } from 'naive-ui'

const THEME_KEY = 'everydaynews-theme'

function getSavedTheme(): ThemeMode {
  try {
    const saved = localStorage.getItem(THEME_KEY)
    if (saved === 'dark' || saved === 'light') return saved
  } catch { /* ignore */ }
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export const useAppStore = defineStore('app', {
  state: () => ({
    index: null as IndexData | null,
    meta: null as MetaInfo | null,
    currentDate: '' as string,
    currentPlatform: 'all' as Platform | 'all',
    dayDataList: [] as DayData[],
    indexLoading: false,
    dataLoading: false,
    searchQuery: '',
    searchResults: [] as SearchEntry[],
    themeMode: getSavedTheme(),
  }),

  getters: {
    naiveTheme(): GlobalTheme | null {
      return this.themeMode === 'dark' ? darkTheme : null
    },
    availableDates(): string[] {
      if (!this.index) return []
      return Object.keys(this.index.days).sort()
    },
    latestDate(): string {
      const dates = this.availableDates
      return dates.length > 0 ? dates[dates.length - 1] : ''
    },
  },

  actions: {
    async loadIndex() {
      this.indexLoading = true
      const [index, meta] = await Promise.all([loadIndex(), loadMeta()])
      this.index = index
      this.meta = meta
      if (!this.currentDate) {
        this.currentDate = this.latestDate
      }
      this.indexLoading = false
    },

    async loadCurrentView() {
      if (!this.currentDate) return
      if (this.currentPlatform === 'all') {
        await this.loadAllPlatforms(this.currentDate)
      } else {
        await this.loadDayData(this.currentDate, this.currentPlatform)
      }
    },

    async loadDayData(date: string, platform: string) {
      this.dataLoading = true
      this.dayDataList = [await loadDay(date, platform)]
      this.dataLoading = false
    },

    async loadAllPlatforms(date: string) {
      this.dataLoading = true
      const platforms: Platform[] = ['baidu', 'weibo', 'bilibili']
      const results = await Promise.allSettled(
        platforms.map(p => loadDay(date, p))
      )
      this.dayDataList = results
        .filter((r): r is PromiseFulfilledResult<DayData> => r.status === 'fulfilled')
        .map(r => r.value)
      this.dataLoading = false
    },

    setDate(date: string) {
      this.currentDate = date
      if (this.currentPlatform === 'all') {
        this.loadAllPlatforms(date)
      } else {
        this.loadDayData(date, this.currentPlatform)
      }
    },

    async setPlatform(platform: Platform | 'all') {
      this.currentPlatform = platform
      if (!this.currentDate) return
      if (platform === 'all') {
        await this.loadAllPlatforms(this.currentDate)
      } else {
        await this.loadDayData(this.currentDate, platform)
      }
    },

    toggleTheme() {
      this.themeMode = this.themeMode === 'light' ? 'dark' : 'light'
      try { localStorage.setItem(THEME_KEY, this.themeMode) } catch { /* ignore */ }
    },
  },
})
