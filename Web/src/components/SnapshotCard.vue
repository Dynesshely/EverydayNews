<script setup lang="ts">
import type { NewsItem, BaiduNewsItem } from "../types";
import { computed, h, ref } from "vue";
import { useElementSize } from "@vueuse/core";

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
  { title: "#", key: "rank", width: 48, render: rankRender as any },
  {
    title: "标题",
    key: "title",
    ellipsis: { tooltip: true },
    render: titleRender as any,
  },
  { title: "描述", key: "desc", ellipsis: { tooltip: true } },
  {
    title: "热搜指数",
    key: "heatScore",
    width: 88,
    className: "tabular-nums",
  },
];

const baiduV2Columns = [
  { title: "#", key: "rank", width: 48, render: rankRender as any },
  {
    title: "标题",
    key: "title",
    ellipsis: { tooltip: true },
    render: titleRender as any,
  },
  { title: "标签", key: "tag", width: 60, ellipsis: { tooltip: true } },
  // 「NORMAL / HOT / NEW」是固定词，宽度必须够，否则会折行撑高行高
  { title: "类型", key: "heatType", width: 88, ellipsis: { tooltip: true } },
];

const weiboColumns = [
  { title: "#", key: "rank", width: 48, render: rankRender as any },
  {
    title: "标题",
    key: "title",
    ellipsis: { tooltip: true },
    render: titleRender as any,
  },
  { title: "热度", key: "hotness", width: 88, className: "tabular-nums" },
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

// --- 宽度自适应 ---------------------------------------------------------
// 卡片在「全部」视图里是多列并排（md 2 列 / xl 3 列），可用宽度远小于
// 单平台全宽视图。这里按容器实测宽度决定表格宽度：
//   · 容器够宽 → 表格宽度 = 容器宽度，列自适应铺满，不出现横向滚动；
//   · 容器过窄 → 才把宽度钉在最小可读宽度上，允许横向滚动。
// 固定列宽之和之外，标题列至少保留 minTitleWidth，避免被挤成一条缝。
const wrapperRef = ref<HTMLElement | null>(null);
const { width: wrapperWidth } = useElementSize(wrapperRef);

const minTitleWidth = 150;

const columns = computed(() => getColumns(props.platform, limited.value));

/** 固定宽度列的宽度之和（不含自适应列）。 */
const fixedColumnsWidth = computed(() =>
  columns.value.reduce(
    (sum, col: any) => sum + (typeof col.width === "number" ? col.width : 0),
    0,
  ),
);

/** 表格最小可读宽度：固定列 + 标题列下限 + 自适应列下限。 */
const minTableWidth = computed(() => {
  const autoCount = columns.value.filter(
    (col: any) => typeof col.width !== "number",
  ).length;
  // 自适应列里除标题之外还有（百度 v1 的「描述」），给它一个下限。
  const extraAuto = Math.max(0, autoCount - 1) * 110;
  return fixedColumnsWidth.value + minTitleWidth + extraAuto;
});

/** 传给 n-data-table 的 scroll-x。
 *  · 容器够宽：不传（表格 min-width 为 100%，直接铺满容器，不出现横向滚动）；
 *  · 容器过窄：钉在最小可读宽度，允许横向滚动。
 * 注意不能把 scroll-x 直接设成容器宽度：单平台全宽视图里表格有纵向滚动条，
 * 纵向滚动条会占掉几个像素，反而制造出 6px 的横向滚动。
 */
const scrollX = computed(() => {
  const available = Math.floor(wrapperWidth.value);
  if (!available) return undefined; // 首次渲染尚未测得宽度，交给浏览器自适应
  return available >= minTableWidth.value ? undefined : minTableWidth.value;
});
</script>

<template>
  <div ref="wrapperRef" class="min-w-0 w-full">
    <div class="rounded-xl border border-en-border bg-en-surface">
      <n-data-table
        :columns="columns"
        :data="limited"
        :scroll-x="scrollX"
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
