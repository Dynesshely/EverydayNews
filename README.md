<p align="center">
    <a href="#"><img src="https://img.shields.io/github/repo-size/Dynesshely/EverydayNews?color=%234682B4" alt="Repo Size"></a>
    <a href="#"><img src="https://img.shields.io/github/languages/code-size/Dynesshely/EverydayNews" alt="Code Size"></a>
    <a href="https://github.com/Dynesshely/EverydayNews/commits/"><img src="https://img.shields.io/github/commit-activity/t/Dynesshely/EverydayNews" alt="Commit Activity"></a>
</p>

<p align="center">
    <a href="https://github.com/Dynesshely/EverydayNews/network/members"><img src="https://img.shields.io/github/forks/Dynesshely/EverydayNews?style=social" alt="Forks"></a>
    <a href="https://github.com/Dynesshely/EverydayNews/stargazers"><img src="https://img.shields.io/github/stars/Dynesshely/EverydayNews?style=social" alt="Stars"></a>
    <a href="https://github.com/Dynesshely/EverydayNews/watchers"><img src="https://img.shields.io/github/watchers/Dynesshely/EverydayNews?style=social" alt="Watches"></a>
</p>

# EverydayNews

中文互联网热搜榜单的**自动化采集、归档与可视化**项目。

每天 3 次定时抓取百度、微博、Bilibili 的热搜 / 热门内容，以 CSV 格式归档，并通过 Web 前端提供浏览、检索和趋势分析。目前已累积 **2.5 年 / 950+ 天 / 70 万条** 数据。

---

## 目录结构

```
EverydayNews/
├── Fetchers/CN/                   # 数据抓取脚本
│   ├── fetcher-baidu-hot-search.py
│   ├── fetcher-baidu-hot-search-v2.py
│   ├── fetcher-weibo-hot-search.py
│   └── fetcher-bilibili-hot-videos.py
│
├── News/CN/{YYYY}/{MMDD}/         # 归档数据
│   ├── 百度热搜榜.{minutes}.csv
│   ├── 微博热搜榜.{minutes}.csv
│   └── BiliBili 热门视频.{minutes}.csv
│
├── .github/workflows/             # CI/CD 调度
│   ├── launcher-cn.yml            # 定时触发抓取 + 合并到 main
│   └── build-web.yml              # 构建前端并部署到 GitHub Pages
│
└── Web/                           # Vue 3 可视化前端
    ├── src/components/            # 组件
    ├── src/stores/                # Pinia 状态管理
    ├── scripts/build-index.py     # CSV → JSON 数据预处理
    └── public/data/               # 生成的 JSON（不入库）
```

---

## 数据管线

### 采集

GitHub Actions 在 UTC+8 时间 **6:00 / 12:00 / 20:00** 自动运行：

| 平台     | 来源                | 方式                     | 单次条数 |
| -------- | ------------------- | ------------------------ | -------- |
| 百度热搜 | `top.baidu.com` API | HTTP GET + JSON 解析     | ~50      |
| 微博热搜 | `s.weibo.com`       | Selenium + BeautifulSoup | ~50      |
| B 站热门 | `api.bilibili.com`  | HTTP GET 分页 (×10)      | 200      |

采集结果以 CSV 存入 `News/CN/{YYYY}/{MMDD}/`，文件名中的分钟数表示当天 UTC+8 的抓取时刻（`hour * 60 + minute`）。

### 归档

每次抓取提交到独立分支（`fetch=baidu-hot-search` 等），由 CI 合并回 `main`，形成按日期组织的 Git 历史归档。

### 可视化

前端构建前，`scripts/build-index.py` 扫描全部 CSV，生成三组 JSON：

| 产物                             | 说明                              | 大小       |
| -------------------------------- | --------------------------------- | ---------- |
| `index.json`                     | 日期索引（每天有哪些平台 / 快照） | ~83 KB     |
| `day/{date}-{platform}.json`     | 单平台单天全量快照                | 40–300 KB  |
| `search/{platform}/{chunk}.json` | Fuse.js 搜索分块                  | 按年或按月 |

---

## Web 前端

基于 **Vue 3 + Naive UI + Tailwind CSS** 的 SPA，部署于 GitHub Pages。

### 功能

- **首页概览**：最新日期的三个平台热搜卡片，百度 / 微博各显示每个时段的 top 5，B 站每时段 3 个视频
- **日期浏览**：日期选择器，仅开放有数据的日期
- **平台切换**：全部 / 百度 / 微博 / B 站分栏，单平台详情展示全量数据
- **全文搜索**：基于 Fuse.js 的客户端模糊搜索，按日期 + 匹配度排序
- **趋势图**：点击标题查看任意话题的排名变化（ECharts）
- **亮 / 暗主题**：跟随系统或手动切换

### 技术栈

| 层       | 选型                      |
| -------- | ------------------------- |
| 框架     | Vue 3 + Vite + TypeScript |
| UI 组件  | Naive UI                  |
| 样式     | Tailwind CSS 4            |
| 状态管理 | Pinia                     |
| 搜索     | Fuse.js（客户端分块加载） |
| 图表     | ECharts + vue-echarts     |
| 图标     | @vicons/carbon            |
| 工具     | @vueuse/core              |

### 本地开发

```bash
cd Web

# 安装依赖
pnpm install

# 预处理数据（CSV → JSON）
python scripts/build-index.py

# 启动开发服务器（端口 52611）
pnpm dev

# 生产构建
pnpm build
```

---

## 数据格式

构建脚本归一化了 4 种 CSV 格式为统一的 TypeScript discriminated union：

```typescript
type NewsItem = BaiduNewsItem | WeiboNewsItem | BilibiliNewsItem

// 百度 v1（2023-2024）
{ platform: 'baidu', version: 'v1', rank, title, desc, heatScore, image, url }

// 百度 v2（2025+）
{ platform: 'baidu', version: 'v2', rank, title, tag, isTop, heatType, url }

// 微博
{ platform: 'weibo', version: 'v1', rank, title, hotness, url }

// B 站
{ platform: 'bilibili', version: 'v1', rank, title, videoId, nickname,
  category, image, views, danmaku, likes, coins, favorites, shares, comments, url }
```
