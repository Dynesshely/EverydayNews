<script setup lang="ts">
import { useAppStore } from "../stores/app";
import type { Platform } from "../types";

const store = useAppStore();

const tabs = [
  { label: "全部", value: "all" },
  { label: "百度热搜", value: "baidu" },
  { label: "微博热搜", value: "weibo" },
  { label: "B站热门", value: "bilibili" },
];

function onChange(val: string) {
  store.setPlatform(val as Platform | "all");
}
</script>

<template>
  <n-tabs
    :value="store.currentPlatform"
    @update:value="(v: string) => onChange(v)"
    type="bar"
    size="medium"
  >
    <n-tab-pane
      v-for="tab in tabs"
      :key="tab.value"
      :name="tab.value"
      :tab="tab.label"
    />
  </n-tabs>
</template>
