"""build-index.py — Scan News/CN/ CSV files and generate JSON data for the web app.

Output structure:
  public/data/
    index.json                  — day-level index, always loaded first
    meta.json                   — stats summary
    day/{YYYYMMDD}-{platform}.json — per-day per-platform snapshots, lazy loaded
    search/{platform}/{chunk}.json — search index chunks
"""

import csv
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
NEWS_DIR = ROOT.parent / "News" / "CN"
OUT_DIR = ROOT / "public" / "data"

# {platform} / {chunk} -> list of search entries
search_chunks: dict[str, list[dict]] = defaultdict(list)
# YYYYMMDD -> {platform: [minute, ...]}
day_index: dict[str, dict[str, list[int]]] = defaultdict(dict)


def detect_platform_and_version(headers: list[str], filename: str) -> tuple[str, str]:
    """Return (platform, version) based on CSV headers."""
    if "视频 ID" in headers:
        return "bilibili", "v1"
    if "热度类型" in headers:
        return "baidu", "v2"
    if "热搜指数" in headers:
        return "baidu", "v1"
    if "热点" in headers:
        return "weibo", "v1"
    # fallback by filename
    if "BiliBili" in filename or "bilibili" in filename.lower():
        return "bilibili", "v1"
    if "微博" in filename:
        return "weibo", "v1"
    if "百度" in filename:
        return "baidu", "v2"
    raise ValueError(f"Cannot detect platform for {filename} with headers {headers}")


def extract_minutes(filename: str) -> int:
    m = re.search(r"\.(\d+)\.csv$", filename)
    return int(m.group(1)) if m else 0


def minutes_to_time(minutes: int) -> str:
    h, m = divmod(minutes, 60)
    return f"{h:02d}:{m:02d}"


def parse_csv(filepath: Path) -> list[dict]:
    """Parse a CSV file, handling utf-8-sig BOM."""
    with open(filepath, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return [row for row in reader if any(v.strip() for v in row.values())]


def normalize_items(rows: list[dict], platform: str, version: str) -> list[dict]:
    """Normalize raw CSV rows to unified item dicts."""
    items = []
    for idx, row in enumerate(rows):
        try:
            if platform == "baidu":
                item = normalize_baidu(row, version, idx)
            elif platform == "weibo":
                item = normalize_weibo(row, idx)
            elif platform == "bilibili":
                item = normalize_bilibili(row, idx)
            else:
                continue
            if item:
                items.append(item)
        except Exception:
            continue
    return items


def try_int(val: str) -> int:
    try:
        return int(val.strip())
    except (ValueError, AttributeError):
        return 0


def normalize_baidu(row: dict, version: str, idx: int) -> dict | None:
    title = (row.get("热搜标题") or "").strip()
    if not title:
        return None
    item: dict = {
        "platform": "baidu",
        "version": version,
        "rank": idx + 1,
        "title": title,
        "url": (row.get("链接地址") or "").strip(),
    }
    if version == "v1":
        item["desc"] = (row.get("描述") or "").strip()
        item["heatScore"] = try_int(row.get("热搜指数", ""))
        item["image"] = (row.get("封图链接") or "").strip()
    else:
        item["tag"] = (row.get("标签") or "").strip()
        item["isTop"] = row.get("是否置顶", "").strip() == "是"
        item["heatType"] = (row.get("热度类型") or "").strip()
    return item


def parse_weibo_hotness(text: str) -> int:
    """解析微博热度值。

    微博「热点」列有两种形态：纯数字（"2954496"），或带分类前缀的
    「剧集 96023」「电影 108384」「综艺 41009」等（影视/综艺类条目）。
    历史实现直接 int()，后者会解析失败变成 0，导致前端热度显示成 0。
    这里统一取出其中的数值部分；广告/置顶行可能为空，返回 0。
    """
    raw = (text or "").strip()
    if not raw:
        return 0
    if raw.isdigit():
        return int(raw)
    match = re.search(r"\d+", raw)
    return int(match.group(0)) if match else 0


def normalize_weibo(row: dict, idx: int) -> dict | None:
    title = (row.get("标题") or "").strip()
    if not title:
        return None
    hotness_str = (row.get("热点") or "").strip()
    return {
        "platform": "weibo",
        "version": "v1",
        "rank": idx + 1,
        "title": title,
        "url": (row.get("链接") or "").strip(),
        "hotness": parse_weibo_hotness(hotness_str),
    }


def normalize_bilibili(row: dict, idx: int) -> dict | None:
    title = (row.get("标题") or "").strip()
    if not title:
        return None
    video_id = (row.get("视频 ID") or "").strip()
    return {
        "platform": "bilibili",
        "version": "v1",
        "rank": idx + 1,
        "title": title,
        "url": f"https://www.bilibili.com/video/av{video_id}" if video_id else "",
        "videoId": video_id,
        "nickname": (row.get("用户昵称") or "").strip(),
        "category": (row.get("归属类别") or "").strip(),
        "image": (row.get("图片") or "").strip().replace("http://", "https://"),
        "publishTime": (row.get("发布时间") or "").strip(),
        "views": try_int(row.get("观看人数", "")),
        "danmaku": try_int(row.get("弹幕数", "")),
        "likes": try_int(row.get("点赞数", "")),
        "coins": try_int(row.get("投币数", "")),
        "favorites": try_int(row.get("收藏数", "")),
        "shares": try_int(row.get("分享数", "")),
        "comments": try_int(row.get("评论数", "")),
    }


# ---------------------------------------------------------------------------
# 链接自愈（link healing）
#
# 历史成因：2023-10 起的微博抓取脚本 fetcher-weibo-hot-search.py 存在 off-by-one——
#   title 取 urls_titles[i + 1].get_text()，而 url 取 urls_titles[i]['href']、
#   热度取 hotness[i]。但微博页面里「置顶」行的 td.td-02 只有 <a> 没有 <span>，
#   所以 span 集合天然比 a 集合少一个：hotness[i] 配 title[i+1] 恰好是对齐的，
#   真正的错位只发生在 url 上（url[i] 属于 title[i-1]，整段滞后一行）。
#   另有置顶/广告行的 href 是 javascript:void(0)，被脚本用字符串拼接成
#   "https://s.weibo.comjavascript:void(0);" 这种无效 URL。
#
# 抓取端已修正；News/ 下的历史 CSV 属于不可变归档，构建脚本不回写它们，
# 因此这里在生成 JSON 时做一次只读自愈：
#   1) 先按「url 的 q/word 参数与哪一行的标题一致」统计整段的错位方向；
#   2) 只有确认方向（明显占优）时才整体重对齐，并在 ±1 邻域内逐行校验标题，
#      匹配不到的行把 url 置空（前端 titleRender 会自动降级为纯文本，避免点错页面）；
#   3) 只动 url；hotness / rank / title / tag 等其它字段保持原值（热度本来就没错位）；
#   4) 任何非 http(s) 开头的链接（含 javascript:void(0) 拼接串）一律置空。
# 检测不到错位方向时保持原样（宁可不动，也不要改坏正常数据，例如百度的标题改写）。
# ---------------------------------------------------------------------------

_HTTP_URL_RE = re.compile(r"^https?://", re.IGNORECASE)
# 只接受正常域名（含可选端口）：用于挡掉 https://s.weibo.comjavascript:void(0); 这类拼接垃圾。
_HOST_RE = re.compile(r"^[A-Za-z0-9.-]+\.[A-Za-z]{2,}(:\d+)?$")
# 标题比较时去掉 # 话题符号与所有空白（含全角空格、换行）。
_TITLE_STRIP_RE = re.compile(r"[\s#]+")


def normalize_title(text: str) -> str:
    """规范化标题用于比较：去 # 与空白，英文统一小写。"""
    if not text:
        return ""
    return _TITLE_STRIP_RE.sub("", text).casefold()


def is_http_url(url: str) -> bool:
    """判断是否为有效的 http(s) 链接；javascript: 拼接串、空串一律判为无效。"""
    if not url:
        return False
    if not _HTTP_URL_RE.match(url):
        return False
    if "javascript:" in url.lower():
        return False
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    return bool(_HOST_RE.match(parsed.netloc))


def url_query_word(url: str) -> str:
    """取 URL 里 q / word 查询参数的规范化标题（微博用 q，百度用 word）。

    parse_qs 内部已经做过 percent-decoding，并把 "+" 还原成空格
    （百度链接里的空格就是编码成 "+" 的），所以这里不再二次 unquote。
    """
    if not url:
        return ""
    try:
        query = parse_qs(urlparse(url).query, keep_blank_values=False)
    except ValueError:
        return ""
    for key in ("q", "word"):
        values = query.get(key)
        if values:
            return normalize_title(values[0])
    return ""


def detect_link_shift(items: list[dict]) -> str:
    """统计 url 与自身/上一行/下一行标题的匹配数，判断整段链接是否错位。

    返回：
      "prev"    —— 链接整体滞后一行（url[i] 属于 title[i-1]）
      "next"    —— 链接整体提前一行
      "self"    —— 链接与自身标题一致，正常
      "unknown" —— 无法判断（行数太少或没有明显占优的方向）
    """
    n = len(items)
    if n < 2:
        return "unknown"
    hit_self = hit_prev = hit_next = 0
    for i, item in enumerate(items):
        word = url_query_word(item.get("url", ""))
        if not word:
            continue
        if word == normalize_title(item.get("title", "")):
            hit_self += 1
        if i > 0 and word == normalize_title(items[i - 1].get("title", "")):
            hit_prev += 1
        if i + 1 < n and word == normalize_title(items[i + 1].get("title", "")):
            hit_next += 1

    threshold = max(1, int(n * 0.3))
    ranking = sorted(
        ((hit_prev, "prev"), (hit_next, "next"), (hit_self, "self")),
        reverse=True,
    )
    best_count, best_dir = ranking[0]
    runner_up = ranking[1][0]
    if best_count < threshold:
        return "unknown"
    # 必须「显著」占优：次高项达到最高项的 1.5 倍以上就不下结论，避免误伤个例改写。
    if runner_up > 0 and best_count < runner_up * 1.5:
        return "unknown"
    return best_dir


def heal_snapshot_links(items: list[dict]) -> dict:
    """对单个快照的 items 做链接自愈，返回统计信息。

    只重排/清理 url 列；hotness、rank、title 等其它字段一律保持原值。
    原因：微博页面里「置顶」行的 td.td-02 只有 <a> 没有 <span>，所以
    span 集合天然比 a 集合少一个，旧脚本用 hotness[i] 配 a[i+1] 的标题
    恰好是对齐的，错位只发生在 url 上（详见上方注释）。
    """
    stats = {"direction": "unknown", "repaired": 0, "cleared": 0}
    n = len(items)
    if not n:
        return stats

    # 先过滤无效链接（空串、javascript:void(0) 拼接串等）
    urls: list[str] = []
    for item in items:
        raw = (item.get("url") or "").strip()
        urls.append(raw if is_http_url(raw) else "")

    direction = detect_link_shift(items)
    stats["direction"] = direction

    if direction in ("prev", "next"):
        # prev：url[i] 实际属于 title[i-1]，所以 title[i] 的正确链接在 url[i+1] 上；
        # next 方向对称。邻域查找顺序按方向优先，最后才回退到自身。
        offsets = (1, 0, -1) if direction == "prev" else (-1, 0, 1)
        new_urls: list[str] = []
        for i, item in enumerate(items):
            title_key = normalize_title(item.get("title", ""))
            matched = -1
            for offset in offsets:
                j = i + offset
                if 0 <= j < n and urls[j] and url_query_word(urls[j]) == title_key:
                    matched = j
                    break
            if matched < 0:
                # 邻域内都找不到与标题对应的链接（置顶/广告行、末行无法还原），置空。
                new_urls.append("")
                stats["cleared"] += 1
            else:
                new_urls.append(urls[matched])
                if matched != i:
                    stats["repaired"] += 1
        for i, item in enumerate(items):
            item["url"] = new_urls[i]
    else:
        # 无需/无法判断错位：只丢掉无效链接，不动顺序。
        for i, item in enumerate(items):
            if urls[i] != (item.get("url") or "").strip():
                item["url"] = ""
                stats["cleared"] += 1

    return stats


def make_search_entry(item: dict, date_key: str, minutes: int) -> dict:
    return {
        "title": item["title"],
        "date": date_key,
        "minutes": minutes,
        "platform": item["platform"],
        "rank": item["rank"],
    }


def get_search_chunk_key(platform: str, date_key: str) -> str:
    """Determine search chunk key. Bilibili uses monthly chunks, others yearly."""
    if platform == "bilibili":
        return f"{platform}/{date_key[:6]}"  # YYYYMM
    return f"{platform}/{date_key[:4]}"       # YYYY


def main():
    if not NEWS_DIR.exists():
        print(f"News directory not found: {NEWS_DIR}")
        return

    # --- Phase 0: pre-scan to count work ---
    _log("Phase 0: counting directories and files...")
    day_dirs: list[Path] = []
    csv_files_total = 0
    for year_dir in sorted(NEWS_DIR.iterdir()):
        if not year_dir.is_dir() or not year_dir.name.isdigit():
            continue
        for day_dir in sorted(year_dir.iterdir()):
            if not day_dir.is_dir():
                continue
            date_key = year_dir.name + day_dir.name
            if not date_key.isdigit() or len(date_key) != 8:
                continue
            day_dirs.append(day_dir)
            csv_files_total += len(list(day_dir.glob("*.csv")))
    print(f"Found {len(day_dirs)} days, {csv_files_total} CSV files")

    # --- Phase 1: scan and parse ---
    _log("Phase 1: scanning CSV files...")
    day_data_by_date: dict[str, dict] = defaultdict(lambda: {"date": "", "snapshots": []})
    dates: list[str] = []
    csvs_processed = 0
    skipped_count = 0
    # 链接自愈统计（只用于日志，不写盘）
    heal_stats = {"prev": 0, "next": 0, "self": 0, "unknown": 0,
                  "repaired": 0, "cleared": 0}

    for day_idx, day_dir in enumerate(day_dirs):
        date_key = day_dir.parent.name + day_dir.name
        dates.append(date_key)

        snapshots_by_key: dict[str, list[dict]] = defaultdict(list)
        day_csv_count = 0

        for csv_file in sorted(day_dir.glob("*.csv")):
            csvs_processed += 1
            filename = csv_file.name
            minutes = extract_minutes(filename)

            try:
                rows = parse_csv(csv_file)
            except Exception as e:
                _log(f"  SKIP: {csv_file} — {e}")
                skipped_count += 1
                continue

            if not rows:
                skipped_count += 1
                continue

            headers = list(rows[0].keys())
            try:
                platform, version = detect_platform_and_version(headers, filename)
            except ValueError as e:
                _log(f"  SKIP: {csv_file} — {e}")
                skipped_count += 1
                continue

            items = normalize_items(rows, platform, version)
            if not items:
                skipped_count += 1
                continue

            snapshot_key = f"{platform}|{minutes}"
            snapshots_by_key[snapshot_key].extend(items)

            # Build search index
            chunk_key = get_search_chunk_key(platform, date_key)
            for item in items:
                search_chunks[chunk_key].append(make_search_entry(item, date_key, minutes))

            # Register in day index
            if platform not in day_index[date_key]:
                day_index[date_key][platform] = []
            if minutes not in day_index[date_key][platform]:
                day_index[date_key][platform].append(minutes)

            day_csv_count += 1

        # Build per-platform day data
        platform_snapshots: dict[str, list[dict]] = defaultdict(list)
        for snapshot_key, items in snapshots_by_key.items():
            platform, minutes_str = snapshot_key.split("|")
            minutes = int(minutes_str)
            platform_snapshots[platform].append({
                "minutes": minutes,
                "captureTime": minutes_to_time(minutes),
                "items": items,
            })

        for platform, snapshots in platform_snapshots.items():
            snapshots.sort(key=lambda s: s["minutes"])
            # 链接自愈：只改内存中即将写盘的数据，不回写 News/ 下的历史 CSV。
            if platform in ("weibo", "baidu"):
                for snapshot in snapshots:
                    snapshot_stats = heal_snapshot_links(snapshot["items"])
                    heal_stats[snapshot_stats["direction"]] += 1
                    heal_stats["repaired"] += snapshot_stats["repaired"]
                    heal_stats["cleared"] += snapshot_stats["cleared"]
            day_data_by_date[f"{date_key}-{platform}"] = {
                "date": date_key,
                "platform": platform,
                "snapshots": snapshots,
            }

        # Progress: overwrite current line
        pct = (day_idx + 1) / len(day_dirs) * 100
        _progress(f"  Scanning: {day_idx + 1}/{len(day_dirs)} days ({pct:.1f}%)"
                  f" | {csvs_processed}/{csv_files_total} CSVs"
                  f" | {skipped_count} skipped")

    _progress_done()

    # Sort dates
    dates.sort()
    total_days = len(dates)

    # 链接自愈汇总（写盘前先打出来，便于对照校验脚本）
    _log("Phase 1.5: link healing summary")
    _log(f"  shifted snapshots: prev={heal_stats['prev']} next={heal_stats['next']}"
         f" normal={heal_stats['self']} undecided={heal_stats['unknown']}")
    _log(f"  rows: url_repaired={heal_stats['repaired']} url_cleared={heal_stats['cleared']}")

    # --- Phase 2: write day files ---
    _log("Phase 2: writing day files...")
    day_out = OUT_DIR / "day"
    day_out.mkdir(parents=True, exist_ok=True)
    day_files = list(day_data_by_date.items())
    for idx, (file_key, data) in enumerate(day_files):
        with open(day_out / f"{file_key}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        if (idx + 1) % 200 == 0 or idx + 1 == len(day_files):
            pct = (idx + 1) / len(day_files) * 100
            _progress(f"  Writing: {idx + 1}/{len(day_files)} day files ({pct:.1f}%)")
    _progress_done()

    # --- Phase 3: write index and search chunks ---
    _log("Phase 3: writing index and search chunks...")

    # index.json
    index_sorted = {d: {p: sorted(v) for p, v in platforms.items()} for d, platforms in day_index.items()}
    with open(OUT_DIR / "index.json", "w", encoding="utf-8") as f:
        json.dump({
            "days": index_sorted,
            "meta": {
                "dateRange": [dates[0], dates[-1]] if dates else ["", ""],
                "totalDays": total_days,
                "platforms": ["baidu", "weibo", "bilibili"],
            },
        }, f, ensure_ascii=False)
    _log(f"  Wrote index.json ({len(day_index)} days)")

    # search/*.json
    search_out = OUT_DIR / "search"
    chunk_items = list(search_chunks.items())
    for idx, (chunk_key, entries) in enumerate(chunk_items):
        chunk_path = search_out / chunk_key
        chunk_path.parent.mkdir(parents=True, exist_ok=True)
        with open(f"{chunk_path}.json", "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False)
        _progress(f"  Writing search chunks: {idx + 1}/{len(chunk_items)}")
    _progress_done()

    # meta.json
    with open(OUT_DIR / "meta.json", "w", encoding="utf-8") as f:
        json.dump({
            "dateRange": [dates[0], dates[-1]] if dates else ["", ""],
            "totalDays": total_days,
            "platforms": ["baidu", "weibo", "bilibili"],
            "totalSnapshots": sum(len(v) for v in day_index.values()),
            "totalItems": sum(len(v) for v in search_chunks.values()),
        }, f, ensure_ascii=False)

    total_items = sum(len(v) for v in search_chunks.values())
    print(f"\nDone: {total_days} days, {len(day_files)} day files,"
          f" {len(search_chunks)} search chunks, {total_items} items"
          f" ({skipped_count} CSVs skipped)")
    print(f"Output: {OUT_DIR}")


# --- terminal helpers ---

_TERM_WIDTH = 0

def _term_width() -> int:
    global _TERM_WIDTH
    if not _TERM_WIDTH:
        try:
            _TERM_WIDTH = os.get_terminal_size().columns
        except Exception:
            _TERM_WIDTH = 80
    return _TERM_WIDTH


def _log(msg: str) -> None:
    """Print a persistent log line (always visible after it prints)."""
    print(msg, flush=True)


def _progress(msg: str) -> None:
    """Overwrite the current line with progress; next _progress or _progress_done will replace it."""
    width = _term_width()
    sys.stderr.write("\r" + msg[:width - 1])
    sys.stderr.flush()


def _progress_done() -> None:
    """End the progress line and move to a permanent newline."""
    sys.stderr.write("\n")
    sys.stderr.flush()


if __name__ == "__main__":
    main()
