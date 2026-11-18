import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from news_library import collect, read_rows


def test_archive_survives_expiry_retries_and_beijing_midnight(tmp_path):
    snapshot = tmp_path / "archive.json"
    output = tmp_path / "library"

    def save(rows):
        snapshot.write_text(json.dumps({"items": rows}))
        collect(snapshot, output)

    def item(key, first_seen):
        return dict(id=key, url=f"https://example.com/{key}", title="Personal Agent",
                    source="Example", first_seen_at=first_seen, published_at=None)

    old = item("a", "2026-11-10T15:59:59Z")
    first = item("b", "2026-11-10T16:00:00Z")
    save([old, first, first])
    day = output / "2026/2026-11-11.jsonl"
    saved = day.read_bytes()
    assert [r["id"] for r in read_rows(day)] == ["b"]
    assert "product-entry" in next(read_rows(day))["topics"]
    save([first])
    assert day.read_bytes() == saved
    later = item("c", "2026-12-23T16:00:00Z")
    save([later])
    save([later, dict(first, first_seen_at=later["first_seen_at"])])
    assert day.read_bytes() == saved
    assert [r["id"] for r in read_rows(output / "2026/2026-12-24.jsonl")] == ["c"]
    assert len(list(output.rglob("*.jsonl"))) == 2
