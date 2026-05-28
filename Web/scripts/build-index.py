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
        "hotness": try_int(hotness_str),
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
