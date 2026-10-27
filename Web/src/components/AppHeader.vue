<script setup lang="ts">
import { useAppStore } from "../stores/app";
import { Sun, Moon } from "@vicons/carbon";

const store = useAppStore();
</script>

<template>
  <div class="flex items-center justify-between gap-4 w-full">
    <div class="flex items-center gap-2.5 min-w-0">
      <div
        class="size-8 rounded-lg bg-en-primary flex items-center justify-center shrink-0"
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          aria-hidden="true"
        >
          <rect x="2" y="9" width="3" height="5" rx="1" fill="#fff" opacity="0.85" />
          <rect x="6.5" y="5" width="3" height="9" rx="1" fill="#fff" />
          <rect x="11" y="2" width="3" height="12" rx="1" fill="#fff" opacity="0.7" />
        </svg>
      </div>
      <div class="min-w-0 leading-tight">
        <h1 class="text-base font-semibold text-en-text truncate">
          EverydayNews
        </h1>
        <p class="text-xs text-en-text-muted">每日新闻</p>
      </div>
    </div>
    <div class="flex items-center gap-3 shrink-0">
      <div v-if="store.meta" class="hidden md:flex items-center gap-2">
        <span class="en-chip">
          {{ store.meta.dateRange[0] }} ~ {{ store.meta.dateRange[1] }}
        </span>
        <span class="en-chip">{{ store.meta.totalDays }} 天</span>
      </div>
      <n-button
        quaternary
        circle
        @click="store.toggleTheme()"
        :title="store.themeMode === 'light' ? '切换暗色模式' : '切换亮色模式'"
      >
        <template #icon>
          <n-icon v-if="store.themeMode === 'light'"><Sun /></n-icon>
          <n-icon v-else><Moon /></n-icon>
        </template>
      </n-button>
    </div>
  </div>
</template>
