// === Index & Meta ===

export interface IndexData {
  days: Record<string, DayIndex>
  meta: MetaInfo
}

export interface DayIndex {
  baidu?: number[]
  weibo?: number[]
  bilibili?: number[]
}

export interface MetaInfo {
  dateRange: [string, string]
  totalDays: number
  platforms: string[]
}

// === Per-day snapshots ===

export interface DayData {
  date: string
  platform: Platform
  snapshots: Snapshot[]
}

export interface Snapshot {
  minutes: number
  captureTime: string
  items: NewsItem[]
}

export type Platform = 'baidu' | 'weibo' | 'bilibili'

// === Unified News Items (discriminated union) ===

export interface BaiduNewsItem {
  platform: 'baidu'
  version: 'v1' | 'v2'
  rank: number
  title: string
  url: string
  // v1 fields
  desc?: string
  heatScore?: number
  image?: string
  // v2 fields
  tag?: string
  isTop?: boolean
  heatType?: string
}

export interface WeiboNewsItem {
  platform: 'weibo'
  version: 'v1'
  rank: number
  title: string
  url: string
  hotness: number
}

export interface BilibiliNewsItem {
  platform: 'bilibili'
  version: 'v1'
  rank: number
  title: string
  url: string
  videoId: string
  nickname: string
  category: string
  image: string
  publishTime: string
  views: number
  danmaku: number
  likes: number
  coins: number
  favorites: number
  shares: number
  comments: number
}

export type NewsItem = BaiduNewsItem | WeiboNewsItem | BilibiliNewsItem

// === Search ===

export interface SearchEntry {
  title: string
  date: string
  minutes: number
  platform: Platform
  rank: number
}

// === Theme ===

export type ThemeMode = 'light' | 'dark'
