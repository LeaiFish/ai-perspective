"""Keep first-seen public news in Beijing-day JSONL files and search them offline."""
import argparse
import json
import os
import tempfile
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "data/news-library"
CONFIG = ROOT / "config/topics.json"
FIRST_DAY = "2026-11-11"
BEIJING = timezone(timedelta(hours=8))


def beijing_day(timestamp):
    instant = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    if instant.tzinfo is None:
        raise ValueError(f"First-seen time needs a timezone: {timestamp}")
    return instant.astimezone(BEIJING).date().isoformat()


def read_rows(path):
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            yield json.loads(line)


def write_day(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                     suffix=".tmp", delete=False) as stream:
        temp = Path(stream.name)
        try:
            for row in sorted(rows, key=lambda r: (r["first_seen_at"], r["id"])):
                stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
        except BaseException:
            temp.unlink(missing_ok=True)
            raise
    os.replace(temp, path)


def collect(snapshot, directory):
    from build_topics import load_topic_config, record_matches_topic

    topics = load_topic_config(CONFIG)["topics"]
    seen = {row["id"] for path in directory.glob("*/*.jsonl") for row in read_rows(path)}
    additions = defaultdict(list)
    # The input is update_news.py's sanitized public archive, never a raw feed.
    payload = json.loads(snapshot.read_text(encoding="utf-8"))
    for item in payload["items"]:
        identity = item["id"]
        day = beijing_day(item["first_seen_at"])
        if day < FIRST_DAY or identity in seen:
            continue
        record = {key: item[key] for key in ("id", "first_seen_at", "title", "source", "url")}
        record["published_at"] = item.get("published_at")
        translated = item.get("title_zh") or item.get("provided_title_zh")
        if translated and translated != record["title"]:
            record["title_zh"] = translated
        context = {**item, "title_zh": translated, "title_en": item.get("title_en") or item.get("provided_title_en")}
        record["topics"] = [t["id"] for t in topics if record_matches_topic(context, t)]
        additions[day].append(record)
        seen.add(identity)
    for day, new_rows in additions.items():
        path = directory / day[:4] / f"{day}.jsonl"
        existing = list(read_rows(path)) if path.exists() else []
        write_day(path, existing + new_rows)
    print(f"{sum(map(len, additions.values()))} new items in {len(additions)} Beijing days")


def search(args, parser):
    topics = json.loads(CONFIG.read_text(encoding="utf-8"))["topics"]
    names = {t["id"]: t["name"] for t in topics}
    names["uncategorized"] = "未分类"
    if args.list_topics:
        for slug, name in names.items():
            print(f"{slug}\t{name}")
        return
    topic = None
    if args.topic:
        if args.topic in names:
            topic = args.topic
        else:
            matches = [slug for slug, name in names.items() if args.topic.casefold() in name.casefold()]
            if len(matches) != 1:
                parser.error("专题不明确，请从 --list-topics 选择 ID")
            topic = matches[0]
    start = args.date or args.start
    end = args.date or args.end
    if start and end and start > end:
        parser.error("开始日期晚于结束日期")
    if not args.directory.is_dir():
        parser.error(f"本地归档目录不存在: {args.directory}")
    count = 0
    for path in sorted(args.directory.glob("*/*.jsonl"), reverse=True):
        day = date.fromisoformat(path.stem)
        if (start and day < start) or (end and day > end):
            continue
        for row in read_rows(path):
            if topic and topic not in (row["topics"] or ["uncategorized"]):
                continue
            count += 1
            if not args.count:
                print(f'{day}\t{row.get("title_zh") or row["title"]}\t{row["source"]}\t{row["url"]}')
    if args.count:
        print(count)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    sync = modes.add_parser("archive", help="Append new public entries by first-seen date")
    sync.add_argument("--snapshot", type=Path, default=ROOT / "data/archive.json")
    query = modes.add_parser("find", help="Search permanent local entries; no network access")
    query.add_argument("--date", type=date.fromisoformat)
    query.add_argument("--start", type=date.fromisoformat)
    query.add_argument("--end", type=date.fromisoformat)
    query.add_argument("--topic")
    query.add_argument("--list-topics", action="store_true")
    query.add_argument("--count", action="store_true")
    for mode in (sync, query):
        mode.add_argument("--directory", type=Path, default=LIBRARY)
    args = parser.parse_args()
    if args.mode == "archive":
        collect(args.snapshot, args.directory)
    else:
        if args.date and (args.start or args.end):
            parser.error("请选择单日或日期范围")
        search(args, parser)


if __name__ == "__main__":
    main()
