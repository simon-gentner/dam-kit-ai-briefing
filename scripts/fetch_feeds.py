#!/usr/bin/env python3
"""Fetch new entries from every feed listed in ~/work/sources.md (kit: ai-briefing).

Prints a JSON object {"fetched_at", "sources": [...], "items": [...], "errors": [...]}
with only the entries not seen before, then records them in ~/work/state/seen.json.

  --dry-run        do not record anything as seen
  --since-hours N  ignore the seen state, return entries from the last N hours
"""
import argparse
import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

WORK = Path.home() / "work"
SOURCES = WORK / "sources.md"
STATE = WORK / "state" / "seen.json"
KEEP_DAYS = 30
MAX_AGE_DAYS = 4  # older entries are never reported (covers a weekend), only marked seen
SUMMARY_CHARS = 600
FULLTEXT_CHARS = 3000  # when a feed's description is only a teaser, take this much of the full text
ATOM = "{http://www.w3.org/2005/Atom}"
CONTENT = "{http://purl.org/rss/1.0/modules/content/}encoded"


def clean_url(url):
    parts = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parts.query) if not k.startswith("utm_")]
    return urlunsplit(parts._replace(query=urlencode(query)))


def strip_html(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def parse_date(value):
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def read_sources():
    sources = []
    for line in SOURCES.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*-\s*(.+?)\s*\|\s*(https?://\S+)\s*$", line)
        if m:
            sources.append({"name": m.group(1), "url": m.group(2)})
    return sources


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "ai-briefing/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def pick_text(summary, content):
    summary, content = strip_html(summary), strip_html(content)
    if len(summary) < 200 and len(content) > len(summary):
        return content[:FULLTEXT_CHARS]
    return summary[:SUMMARY_CHARS]


def parse_hf_papers(data):
    """Hugging Face daily papers API (https://huggingface.co/api/daily_papers)."""
    items = []
    for p in data:
        paper = p.get("paper", {})
        pid = paper.get("id") or p.get("id")
        items.append({
            "id": f"hf-paper:{pid}",
            "title": strip_html(p.get("title") or paper.get("title")),
            "link": f"https://huggingface.co/papers/{pid}",
            "published": parse_date(p.get("publishedAt") or paper.get("publishedAt")),
            "summary": strip_html(paper.get("summary") or p.get("summary"))[:SUMMARY_CHARS],
            "upvotes": paper.get("upvotes"),
        })
    return items


def parse_feed(raw, source):
    if raw.lstrip()[:1] in (b"[", b"{"):
        data = json.loads(raw)
        if isinstance(data, list) and data and "paper" in data[0]:
            items = parse_hf_papers(data)
            for item in items:
                item["source"], item["category"] = source["name"], "paper"
            return items
        raise ValueError("unknown JSON feed format")
    root = ET.fromstring(raw)
    items = []
    for it in root.iter("item"):  # RSS 2.0
        link = (it.findtext("link") or "").strip()
        items.append({
            "id": (it.findtext("guid") or link).strip(),
            "title": strip_html(it.findtext("title")),
            "link": clean_url(link),
            "published": parse_date(it.findtext("pubDate")),
            "summary": pick_text(it.findtext("description"), it.findtext(CONTENT)),
        })
    for it in root.iter(f"{ATOM}entry"):  # Atom
        link_el = it.find(f"{ATOM}link[@rel='alternate']")
        if link_el is None:
            link_el = it.find(f"{ATOM}link")
        link = link_el.get("href", "") if link_el is not None else ""
        items.append({
            "id": (it.findtext(f"{ATOM}id") or link).strip(),
            "title": strip_html(it.findtext(f"{ATOM}title")),
            "link": clean_url(link),
            "published": parse_date(it.findtext(f"{ATOM}published") or it.findtext(f"{ATOM}updated")),
            "summary": pick_text(it.findtext(f"{ATOM}summary"), it.findtext(f"{ATOM}content")),
        })
    for item in items:
        item["source"] = source["name"]
        m = re.search(r"https?://[^/]+/([a-z_-]+)/", item["link"])
        item["category"] = m.group(1) if m else None
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--since-hours", type=float)
    args = ap.parse_args()

    now = datetime.now(timezone.utc)
    seen = json.loads(STATE.read_text()) if STATE.exists() else {}
    cutoff = now - timedelta(hours=args.since_hours) if args.since_hours else None
    too_old = now - timedelta(days=MAX_AGE_DAYS)

    out, errors, sources, per_source = [], [], read_sources(), {}
    for src in sources:
        try:
            entries = parse_feed(fetch(src["url"]), src)
        except Exception as exc:  # report and continue with the other feeds
            errors.append({"source": src["name"], "error": f"{type(exc).__name__}: {exc}"})
            continue
        per_source[src["name"]] = 0
        for e in entries:
            if cutoff is not None:
                if e["published"] and e["published"] < cutoff:
                    continue
            elif e["id"] in seen:
                continue
            seen.setdefault(e["id"], now.isoformat())
            if cutoff is None and e["published"] and e["published"] < too_old:
                continue  # backlog of a newly added feed: mark seen, don't report
            out.append(e)
            per_source[src["name"]] += 1

    out.sort(key=lambda e: e["published"] or now, reverse=True)
    for e in out:
        e["published"] = e["published"].isoformat() if e["published"] else None

    if not args.dry_run and cutoff is None:
        keep_after = now - timedelta(days=KEEP_DAYS)
        seen = {k: v for k, v in seen.items() if datetime.fromisoformat(v) >= keep_after}
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps(seen, indent=0))

    json.dump({"fetched_at": now.isoformat(), "sources": [s["name"] for s in sources],
               "count": len(out), "per_source": per_source, "items": out, "errors": errors},
              sys.stdout, ensure_ascii=False, indent=1)
    print()
    return 1 if errors and not out else 0


if __name__ == "__main__":
    sys.exit(main())
