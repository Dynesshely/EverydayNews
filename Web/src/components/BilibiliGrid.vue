<script setup lang="ts">
import type { BilibiliNewsItem, NewsItem } from "../types";
import { formatNumber } from "../utils/format";
import { PlayOutline, Chat, ThumbsUp } from "@vicons/carbon";

const props = defineProps<{
  items: NewsItem[];
  maxItems?: number;
}>();

const bilibiliItems = computed(() => {
  const casted = props.items as BilibiliNewsItem[];
  return props.maxItems ? casted.slice(0, props.maxItems) : casted;
});

function proxyImage(url: string): string {
  if (!url) return "";
  if (import.meta.env.DEV) {
    return url.replace(/^https:\/\/(i\d+)\.hdslb\.com\//, "/proxy/bimg-$1/");
  }
  return url;
}

function openVideo(item: BilibiliNewsItem) {
  window.open(item.url, "_blank");
}
</script>

<template>
  <div>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      <div
        v-for="item in bilibiliItems"
        :key="item.videoId"
        class="group cursor-pointer rounded-2xl border border-en-border bg-en-surface overflow-hidden shadow-en-card hover:shadow-md hover:border-gray-300 dark:hover:border-gray-700 transition-all duration-200"
        @click="openVideo(item)"
      >
        <div class="aspect-video overflow-hidden bg-gray-100 dark:bg-gray-800">
          <img
            v-if="item.image"
            :src="proxyImage(item.image)"
            :alt="item.title"
            class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
            loading="lazy"
            referrerpolicy="no-referrer"
          />
          <div v-else class="w-full h-full bg-gray-200 dark:bg-gray-700" />
        </div>
        <div class="p-3 space-y-2">
          <h3
            class="text-sm font-medium leading-snug line-clamp-2 text-gray-900 dark:text-gray-100 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors"
          >
            {{ item.title }}
          </h3>
          <div
            class="flex items-center justify-between gap-2 text-xs text-gray-500 dark:text-gray-400"
          >
            <span class="truncate">{{ item.nickname }}</span>
            <n-tag size="tiny" :bordered="false" class="shrink-0">{{
              item.category
            }}</n-tag>
          </div>
          <div
            class="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400"
          >
            <span class="inline-flex items-center gap-1">
              <n-icon :size="13"><PlayOutline /></n-icon>
              <span class="tabular-nums">{{ formatNumber(item.views) }}</span>
            </span>
            <span class="inline-flex items-center gap-1">
              <n-icon :size="13"><Chat /></n-icon>
              <span class="tabular-nums">{{ formatNumber(item.danmaku) }}</span>
            </span>
            <span class="inline-flex items-center gap-1">
              <n-icon :size="13"><ThumbsUp /></n-icon>
              <span class="tabular-nums">{{ formatNumber(item.likes) }}</span>
            </span>
          </div>
        </div>
      </div>
    </div>
    <p
      v-if="maxItems && items.length > maxItems"
      class="text-xs text-gray-400 dark:text-gray-500 mt-2 text-center tabular-nums"
    >
      仅展示前 {{ maxItems }} 条，共 {{ items.length }} 条
    </p>
  </div>
</template>
