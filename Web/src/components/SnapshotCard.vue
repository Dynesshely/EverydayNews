<script setup lang="ts">
import type { NewsItem, BaiduNewsItem } from '../types'
import { h } from 'vue'

const props = defineProps<{
  items: NewsItem[]
  platform: string
  limit?: number
}>()

const limited = computed(() =>
  props.limit ? props.items.slice(0, props.limit) : props.items
)

function titleRender(row: { url?: string; title?: string }) {
  if (row.url) {
    return h('a', {
      href: row.url,
      target: '_blank',
      rel: 'noopener noreferrer',
      class: 'text-blue-600 dark:text-blue-400 hover:underline',
      onClick: (e: Event) => e.stopPropagation(),
    }, row.title ?? '')
  }
  return row.title ?? ''
}

const baiduV1Columns = [
  { title: '#', key: 'rank', width: 50 },
  { title: '标题', key: 'title', render: titleRender as any },
  { title: '描述', key: 'desc', ellipsis: { tooltip: true } },
  { title: '热搜指数', key: 'heatScore', width: 100 },
]

const baiduV2Columns = [
  { title: '#', key: 'rank', width: 50 },
  { title: '标题', key: 'title', render: titleRender as any },
  { title: '标签', key: 'tag', width: 60 },
  { title: '类型', key: 'heatType', width: 80 },
]

const weiboColumns = [
  { title: '#', key: 'rank', width: 50 },
  { title: '标题', key: 'title', render: titleRender as any },
  { title: '热度', key: 'hotness', width: 100 },
]

function getBaiduColumns(items: NewsItem[]) {
  const first = items[0] as BaiduNewsItem | undefined
  return first?.version === 'v1' ? baiduV1Columns : baiduV2Columns
}

function getColumns(platform: string, items: NewsItem[]) {
  if (platform === 'baidu') return getBaiduColumns(items)
  if (platform === 'weibo') return weiboColumns
  return []
}
</script>

<template>
  <div>
    <n-data-table
      :columns="getColumns(platform, limited)"
      :data="limited"
      size="small"
      :max-height="500"
      virtual-scroll
      striped
    >
      <template #empty>暂无数据</template>
    </n-data-table>
    <p v-if="limit && items.length > limit" class="text-xs text-gray-400 dark:text-gray-500 mt-2 text-center">
      仅展示前 {{ limit }} 条，共 {{ items.length }} 条
    </p>
  </div>
</template>
