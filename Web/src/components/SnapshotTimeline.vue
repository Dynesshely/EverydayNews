<script setup lang="ts">
import type { DayData } from "../types";
import SnapshotCard from "./SnapshotCard.vue";
import BilibiliGrid from "./BilibiliGrid.vue";
import { Time } from "@vicons/carbon";

const p = defineProps<{
  dayData: DayData;
  limit?: number;
  horizontal?: boolean;
  maxItemsBilibili?: number;
}>();

const timelineClass = computed(() => {
  if (!p.horizontal) return "flex flex-col gap-6";
  if (p.dayData.snapshots.length === 1) return "grid grid-cols-1";
  if (p.dayData.snapshots.length === 2) {
    return "grid grid-cols-1 md:grid-cols-2 gap-4";
  }
  return "grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4";
});
</script>

<template>
  <div :class="timelineClass">
    <!-- Bilibili detail: each snapshot as its own card -->
    <template v-if="p.dayData.platform === 'bilibili' && !p.horizontal">
      <n-card
        v-for="snapshot in p.dayData.snapshots"
        :key="`${p.dayData.date}-${snapshot.minutes}`"
        size="small"
        class="max-h-175 rounded-2xl! shadow-sm"
      >
        <template #header>
          <div
            class="flex items-center gap-1.5 text-sm font-medium text-gray-700 dark:text-gray-200"
          >
            <n-icon :size="14" class="text-gray-400 dark:text-gray-500">
              <Time />
            </n-icon>
            <span>
              采集时间
              <span class="tabular-nums">{{ snapshot.captureTime }}</span>
            </span>
          </div>
        </template>
        <template #header-extra>
          <span class="text-xs text-gray-400 tabular-nums"
            >{{ snapshot.items.length }} 个视频</span
          >
        </template>
        <div class="overflow-y-auto max-h-155 -mr-3 pr-3">
          <BilibiliGrid
            :items="snapshot.items"
            :max-items="p.maxItemsBilibili"
          />
        </div>
      </n-card>
    </template>

    <!-- Non-bilibili or horizontal bilibili -->
    <template v-else>
      <div
        v-for="snapshot in p.dayData.snapshots"
        :key="`${p.dayData.date}-${snapshot.minutes}`"
        class="min-w-0"
      >
        <div class="flex items-center gap-1.5 mb-2">
          <span
            class="w-1.5 h-1.5 rounded-full bg-gray-300 dark:bg-gray-600 shrink-0"
          ></span>
          <n-icon :size="12" class="text-gray-400 dark:text-gray-500">
            <Time />
          </n-icon>
          <span
            class="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap"
          >
            采集时间
            <span class="tabular-nums">{{ snapshot.captureTime }}</span>
          </span>
        </div>

        <SnapshotCard
          v-if="p.dayData.platform !== 'bilibili'"
          :items="snapshot.items"
          :platform="p.dayData.platform"
          :limit="p.limit"
        />
        <BilibiliGrid
          v-else
          :items="snapshot.items"
          :max-items="p.maxItemsBilibili"
        />
      </div>
    </template>
  </div>
</template>
