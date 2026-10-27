<script setup lang="ts">
import { useAppStore } from './stores/app'
import { zhCN, dateZhCN } from 'naive-ui'
import type { GlobalThemeOverrides } from 'naive-ui'
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

// Naive UI 主题覆盖，与 main.css 中的 en-* 设计变量保持一致
const themeOverrides = computed<GlobalThemeOverrides>(() => {
  const dark = store.themeMode === 'dark'
  const primary = dark ? '#4f8ff7' : '#2563eb'
  const primaryHover = dark ? '#6ea3f8' : '#3b76f0'
  const primaryPressed = dark ? '#3f7de0' : '#1d4ed8'
  const surface = dark ? '#141519' : '#ffffff'
  const surfaceAlt = dark ? '#1c1e24' : '#f0f1f4'
  const border = dark ? '#26282f' : '#e3e5e9'
  const textPrimary = dark ? '#e8eaee' : '#1f2329'
  const textSecondary = dark ? '#a7adb8' : '#5b6470'
  const textMuted = dark ? '#6b7280' : '#8b93a1'
  return {
    common: {
      primaryColor: primary,
      primaryColorHover: primaryHover,
      primaryColorPressed: primaryPressed,
      primaryColorSuppl: primary,
      fontSize: '14px',
      borderRadius: '8px',
      borderRadiusSmall: '6px',
      bodyColor: dark ? '#0c0d10' : '#f6f7f9',
      cardColor: surface,
      modalColor: surface,
      popoverColor: surface,
      tableColor: surface,
      inputColor: surface,
      inputColorDisabled: surfaceAlt,
      actionColor: surfaceAlt,
      hoverColor: dark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(15, 23, 42, 0.04)',
      borderColor: border,
      dividerColor: border,
      textColorBase: textPrimary,
      textColor1: textPrimary,
      textColor2: textSecondary,
      textColor3: textMuted,
      placeholderColor: textMuted,
      iconColor: textMuted,
    },
    Button: {
      fontWeight: '500',
    },
    Card: {
      borderRadius: '12px',
      borderColor: border,
      boxShadow: dark ? 'none' : '0 1px 2px rgba(15, 23, 42, 0.05)',
    },
    Input: {
      border: `1px solid ${border}`,
      borderHover: `1px solid ${primaryHover}`,
      borderFocus: `1px solid ${primary}`,
      boxShadowFocus: `0 0 0 2px ${dark ? 'rgba(79, 143, 247, 0.25)' : 'rgba(37, 99, 235, 0.15)'}`,
    },
    Tabs: {
      tabFontWeightActive: '600',
      tabTextColorBar: textSecondary,
      tabTextColorBarHover: textPrimary,
      tabTextColorBarActive: primary,
      barColor: primary,
      tabBorderColor: border,
    },
    DataTable: {
      thColor: surfaceAlt,
      thColorHover: surfaceAlt,
      tdColor: surface,
      tdColorHover: surfaceAlt,
      borderColor: border,
      thTextColor: textSecondary,
      tdTextColor: textPrimary,
      thFontWeight: '600',
    },
    Switch: {
      railColorActive: primary,
    },
    DatePicker: {
      panelColor: surface,
      panelBoxShadow: dark
        ? '0 4px 16px rgba(0, 0, 0, 0.4)'
        : '0 4px 16px rgba(15, 23, 42, 0.08)',
      itemColorHover: surfaceAlt,
    },
  }
})

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
  <n-config-provider
    :theme="store.naiveTheme"
    :theme-overrides="themeOverrides"
    :locale="zhCN"
    :date-locale="dateZhCN"
  >
    <n-message-provider>
      <n-layout class="min-h-screen">
        <n-layout-header class="en-header">
          <div class="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center">
            <AppHeader />
          </div>
        </n-layout-header>
        <n-layout-content>
          <div class="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-6">
            <section class="space-y-1.5">
              <h2 class="text-2xl font-semibold tracking-tight text-en-text">
                每日热搜档案
              </h2>
              <p class="text-sm text-en-text-secondary">
                收录百度、微博、B站每日热搜快照，可按日期与平台浏览，支持标题检索与趋势回看。
              </p>
            </section>

            <section class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div class="min-w-0 overflow-x-auto">
                <PlatformTabs />
              </div>
              <div class="shrink-0 self-start sm:self-auto">
                <DateNavigator />
              </div>
            </section>

            <SearchPanel />

            <DayView @show-trend="handleShowTrend" />
            <TrendChart ref="trendRef" />
          </div>
        </n-layout-content>
      </n-layout>
    </n-message-provider>
  </n-config-provider>
</template>
