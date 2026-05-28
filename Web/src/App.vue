<script setup lang="ts">
import { useAppStore } from './stores/app'
import { zhCN, dateZhCN } from 'naive-ui'
import AppHeader from './components/AppHeader.vue'
import PlatformTabs from './components/PlatformTabs.vue'
import DateNavigator from './components/DateNavigator.vue'
import SearchPanel from './components/SearchPanel.vue'
import DayView from './components/DayView.vue'
import TrendChart from './components/TrendChart.vue'

const store = useAppStore()
store.loadIndex().then(() => store.loadCurrentView())

const trendRef = ref<InstanceType<typeof TrendChart> | null>(null)

function handleShowTrend(title: string) {
  trendRef.value?.showTrend(title)
}

// Sync theme with <html> class for Tailwind dark mode
watch(() => store.themeMode, (mode) => {
  const html = document.documentElement
  if (mode === 'dark') {
    html.classList.add('dark')
  } else {
    html.classList.remove('dark')
  }
}, { immediate: true })
</script>

<template>
  <n-config-provider :theme="store.naiveTheme" :locale="zhCN" :date-locale="dateZhCN">
    <n-message-provider>
      <n-layout class="min-h-screen">
        <n-layout-header class="border-b border-gray-200 dark:border-gray-700">
          <div class="max-w-7xl mx-auto px-4 py-3">
            <AppHeader />
          </div>
        </n-layout-header>
        <n-layout-content>
          <div class="max-w-7xl mx-auto px-4 py-6 space-y-6">
            <div class="flex flex-wrap items-center gap-4">
              <DateNavigator />
              <PlatformTabs />
            </div>
            <SearchPanel />
            <DayView @show-trend="handleShowTrend" />
            <TrendChart ref="trendRef" />
          </div>
        </n-layout-content>
      </n-layout>
    </n-message-provider>
  </n-config-provider>
</template>
