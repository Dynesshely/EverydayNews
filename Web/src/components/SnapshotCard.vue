<script setup lang="ts">
import type { NewsItem, BaiduNewsItem } from "../types";
import { h } from "vue";

const props = defineProps<{
  items: NewsItem[];
  platform: string;
  limit?: number;
}>();

const limited = computed(() =>
  props.limit ? props.items.slice(0, props.limit) : props.items,
);

function rankRender(row: { rank?: number }) {
  return h(
    "span",
    {
      class:
        "tabular-nums font-semibold text-gray-500 dark:text-gray-400",
    },
    row.rank ?? "",
  );
}

function titleRender(row: { url?: string; title?: string }) {
  if (row.url) {
    return h(
      "a",
      {
        href: row.url,
        target: "_blank",
        rel: "noopener noreferrer",
        class:
          "font-medium text-gray-800 dark:text-gray-100 hover:text-blue-600 dark:hover:text-blue-400 hover:underline underline-offset-2 transition-colors",
        onClick: (e: Event) => e.stopPropagation(),
      },
      row.title ?? "",
    );
  }
  return h(
    "span",
    { class: "font-medium text-gray-800 dark:text-gray-100" },
    row.title ?? "",
  );
}

const baiduV1Columns = [
  { title: "#", key: "rank", width: 56, render: rankRender as any },
  { title: "标题", key: "title", render: titleRender as any },
  { title: "描述", key: "desc", ellipsis: { tooltip: true } },
  {
    title: "热搜指数",
    key: "heatScore",
    width: 100,
    className: "tabular-nums",
  },
];

const baiduV2Columns = [
  { title: "#", key: "rank", width: 56, render: rankRender as any },
  { title: "标题", key: "title", render: titleRender as any },
  { title: "标签", key: "tag", width: 60 },
  { title: "类型", key: "heatType", width: 80 },
];

const weiboColumns = [
  { title: "#", key: "rank", width: 56, render: rankRender as any },
  { title: "标题", key: "title", render: titleRender as any },
  { title: "热度", key: "hotness", width: 100, className: "tabular-nums" },
];

function getBaiduColumns(items: NewsItem[]) {
  const first = items[0] as BaiduNewsItem | undefined;
  return first?.version === "v1" ? baiduV1Columns : baiduV2Columns;
}

function getColumns(platform: string, items: NewsItem[]) {
  if (platform === "baidu") return getBaiduColumns(items);
  if (platform === "weibo") return weiboColumns;
  return [];
}
</script>

<template>
  <div class="min-w-0 w-full">
    <div
      class="rounded-xl border border-en-border overflow-x-auto bg-en-surface"
    >
      <n-data-table
        :columns="getColumns(platform, limited)"
        :data="limited"
        :scroll-x="platform === 'baidu' ? 720 : 520"
        size="small"
        :max-height="500"
        virtual-scroll
        striped
      >
        <template #empty>暂无数据</template>
      </n-data-table>
    </div>
    <p
      v-if="limit && items.length > limit"
      class="text-xs text-gray-400 dark:text-gray-500 mt-2 text-center tabular-nums"
    >
      仅展示前 {{ limit }} 条，共 {{ items.length }} 条
    </p>
  </div>
</template>
