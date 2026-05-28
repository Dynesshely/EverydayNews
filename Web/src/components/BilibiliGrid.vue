<script setup lang="ts">
import type { BilibiliNewsItem, NewsItem } from "../types";
import { formatNumber } from "../utils/format";

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
      <n-card
        v-for="item in bilibiliItems"
        :key="item.videoId"
        size="small"
        hoverable
        class="cursor-pointer"
        @click="openVideo(item)"
      >
        <template #cover>
          <div class="aspect-video overflow-hidden">
            <img
              v-if="item.image"
              :src="proxyImage(item.image)"
              :alt="item.title"
              class="w-full h-full object-cover"
              loading="lazy"
              referrerpolicy="no-referrer"
            />
            <div v-else class="w-full h-full bg-gray-200 dark:bg-gray-700" />
          </div>
        </template>
        <template #header>
          <span class="text-xs font-medium line-clamp-2">{{ item.title }}</span>
        </template>
        <div class="text-xs text-gray-500 dark:text-gray-400 space-y-1">
          <div class="flex justify-between">
            <span>{{ item.nickname }}</span>
            <n-tag size="tiny" :bordered="false">{{ item.category }}</n-tag>
          </div>
          <div class="flex gap-2">
            <span>▶ {{ formatNumber(item.views) }}</span>
            <span>💬 {{ formatNumber(item.danmaku) }}</span>
            <span>👍 {{ formatNumber(item.likes) }}</span>
          </div>
        </div>
      </n-card>
    </div>
    <p
      v-if="maxItems && items.length > maxItems"
      class="text-xs text-gray-400 dark:text-gray-500 mt-2 text-center"
    >
      仅展示前 {{ maxItems }} 条，共 {{ items.length }} 条
    </p>
  </div>
</template>
