<script setup lang="ts">
import type { DayData } from "../types";
import SnapshotCard from "./SnapshotCard.vue";
import BilibiliGrid from "./BilibiliGrid.vue";

const p = defineProps<{
  dayData: DayData;
  limit?: number;
  horizontal?: boolean;
  maxItemsBilibili?: number;
}>();
</script>

<template>
  <div :class="p.horizontal ? 'grid grid-cols-3 gap-4' : 'flex flex-col gap-6'">
    <!-- Bilibili detail: each snapshot as its own card -->
    <template v-if="p.dayData.platform === 'bilibili' && !p.horizontal">
      <n-card
        v-for="snapshot in p.dayData.snapshots"
        :key="`${p.dayData.date}-${snapshot.minutes}`"
        size="small"
        :title="snapshot.captureTime"
        class="max-h-175"
      >
        <template #header-extra>
          <span class="text-xs text-gray-400"
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
      >
        <div class="flex items-center gap-2 mb-2">
          <span
            class="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap"
          >
            {{ snapshot.captureTime }}
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
