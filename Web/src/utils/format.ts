export function formatNumber(n: number): string {
  if (n >= 1_0000_0000) return (n / 1_0000_0000).toFixed(1) + '亿'
  if (n >= 1_0000) return (n / 1_0000).toFixed(1) + '万'
  return n.toLocaleString()
}

export function formatDate(dateKey: string): string {
  if (dateKey.length !== 8) return dateKey
  const y = dateKey.slice(0, 4)
  const m = dateKey.slice(4, 6)
  const d = dateKey.slice(6, 8)
  return `${y}-${m}-${d}`
}

export function platformLabel(platform: string): string {
  const map: Record<string, string> = {
    baidu: '百度热搜',
    weibo: '微博热搜',
    bilibili: 'B站热门',
  }
  return map[platform] || platform
}
