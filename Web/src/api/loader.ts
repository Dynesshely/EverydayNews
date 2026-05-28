import type { IndexData, DayData, SearchEntry, MetaInfo } from '../types'

const cache = new Map<string, unknown>()

export async function fetchJSON<T>(path: string): Promise<T> {
  if (cache.has(path)) return cache.get(path) as T
  const resp = await fetch(path)
  if (!resp.ok) throw new Error(`Failed to load ${path}: ${resp.status}`)
  const data: T = await resp.json()
  cache.set(path, data)
  return data
}

const DATA_BASE = import.meta.env.BASE_URL + 'data/'

export function loadIndex(): Promise<IndexData> {
  return fetchJSON<IndexData>(DATA_BASE + 'index.json')
}

export function loadMeta(): Promise<MetaInfo> {
  return fetchJSON<MetaInfo>(DATA_BASE + 'meta.json')
}

export function loadDay(date: string, platform: string): Promise<DayData> {
  return fetchJSON<DayData>(`${DATA_BASE}day/${date}-${platform}.json`)
}

export function loadSearchChunk(chunkKey: string): Promise<SearchEntry[]> {
  return fetchJSON<SearchEntry[]>(`${DATA_BASE}search/${chunkKey}.json`)
}
