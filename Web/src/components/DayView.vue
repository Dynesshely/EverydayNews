<script setup lang="ts">
import { useAppStore } from "../stores/app";
import type { Platform } from "../types";
import SnapshotTimeline from "./SnapshotTimeline.vue";
import EmptyState from "./EmptyState.vue";
import LoadingSpinner from "./LoadingSpinner.vue";
import { platformLabel } from "../utils/format";
import { ArrowRight } from "@vicons/carbon";

const store = useAppStore();

const emit = defineEmits<{
  (e: "showTrend", title: string): void;
}>();

function onShowTrend(title: string) {
  emit("showTrend", title);
}

function jumpToPlatform(platform: string) {
  store.setPlatform(platform as Platform);
}

const isAllPlatforms = computed(() => store.currentPlatform === "all");

const dotStyle = (platform: string) =>
  ({
    baidu: "bg-red-500",
    weibo: "bg-orange-500",
    bilibili: "bg-blue-500",
  })[platform] || "bg-gray-400";

function cardLimit(platform: string): number | undefined {
  if (platform === "bilibili") return undefined;
  return 5;
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
        <div
          v-if="store.dataLoading && store.dayDataList.length === 0"
          class="space-y-6"
        >
          <div
            v-for="plat in ['baidu', 'weibo', 'bilibili']"
            :key="plat"
            class="en-card rounded-2xl overflow-hidden"
          >
            <div
              class="flex items-center gap-2 px-4 py-3 border-b border-gray-100 dark:border-gray-800"
            >
              <span
                class="w-2 h-2 rounded-full shrink-0"
                :class="dotStyle(plat)"
              ></span>
              <span
                class="text-sm font-semibold text-gray-900 dark:text-gray-100"
              >
                {{ platformLabel(plat) }}
              </span>
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
          class="en-card rounded-2xl overflow-hidden"
        >
          <div
            class="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-gray-800"
          >
            <div class="flex items-center gap-2">
              <span
                class="w-2 h-2 rounded-full shrink-0"
                :class="dotStyle(dayData.platform)"
              ></span>
              <span
                class="text-sm font-semibold text-gray-900 dark:text-gray-100"
              >
                {{ platformLabel(dayData.platform) }}
              </span>
              <span
                class="text-xs text-gray-400 dark:text-gray-500 tabular-nums"
              >
                {{ dayData.snapshots.length }} 个快照
              </span>
            </div>
            <n-button
              size="tiny"
              quaternary
              @click="jumpToPlatform(dayData.platform)"
            >
              <span class="inline-flex items-center gap-1">
                查看详情
                <n-icon :size="12"><ArrowRight /></n-icon>
              </span>
            </n-button>
          </div>
          <div class="p-3">
            <SnapshotTimeline
              :day-data="dayData"
              :limit="cardLimit(dayData.platform)"
              :horizontal="dayData.platform !== 'bilibili'"
              :max-items-bilibili="
                dayData.platform === 'bilibili' ? 3 : undefined
              "
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
