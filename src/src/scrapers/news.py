import asyncio
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
import dateparser
import httpx
import trafilatura
from src.schemas import NewsEntity, NewsContent, SourceInfo

NEWS_FEEDS = [
    ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("The Verge AI", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
    ("VentureBeat AI", "https://venturebeat.com/category/ai/feed/"),
    ("MIT Tech Review", "https://www.technologyreview.com/topic/artificial-intelligence/feed"),
    ("Wired AI", "https://www.wired.com/feed/tag/ai/latest/rss"),
]

OUTPUT_PATH = Path("data/news.jsonl")
SEEN_PATH = Path("data/seen_news_urls.json")


def load_seen_urls() -> set[str]:
    if SEEN_PATH.exists():
        return set(json.loads(SEEN_PATH.read_text(encoding="utf-8")))
    return set()


def parse_to_utc(raw_date: str | None) -> datetime | None:
    if not raw_date:
        return None
    dt = dateparser.parse(raw_date, settings={"RETURN_AS_TIMEZONE_AWARE": True, "TO_TIMEZONE": "UTC"})
    return dt


async def fetch_full_text(client: httpx.AsyncClient, url: str, sem: asyncio.Semaphore) -> str:
    async with sem:
        try:
            resp = await client.get(url, follow_redirects=True)
            if resp.status_code == 200:
                extracted = trafilatura.extract(resp.text)
                if extracted:
                    return extracted[:5000]  # Keep dense text within reasonable cell size
        except httpx.HTTPError:
            pass
    return ""


async def scrape_news() -> int:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    now_utc = datetime.now(timezone.utc)
    cutoff = now_utc - timedelta(hours=24)
    seen_urls = load_seen_urls()
    new_seen = set(seen_urls)

    candidates = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GraphOneBot/1.0"}

    async with httpx.AsyncClient(timeout=20.0, headers=headers, follow_redirects=True) as client:
        for source_name, feed_url in NEWS_FEEDS:
            try:
                resp = await client.get(feed_url)
                if resp.status_code != 200:
                    continue
                root = ET.fromstring(resp.text)
            except Exception:
                continue

            # Support both RSS (<item>) and Atom (<entry>)
            items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
            for item in items:
                title = (
                    item.findtext("title")
                    or item.findtext("{http://www.w3.org/2005/Atom}title")
                    or ""
                ).strip()
                link = item.findtext("link")
                if not link:
                    link_el = item.find("{http://www.w3.org/2005/Atom}link")
                    link = link_el.attrib.get("href", "") if link_el is not None else ""
                link = link.strip()
                if not title or not link:
                    continue

                raw_date = (
                    item.findtext("pubDate")
                    or item.findtext("{http://www.w3.org/2005/Atom}published")
                    or item.findtext("{http://www.w3.org/2005/Atom}updated")
                )
                pub_dt = parse_to_utc(raw_date)

                # Freshness check: strict 24h window OR unseen-URL heuristic if date is missing
                if pub_dt:
                    if pub_dt < cutoff:
                        continue
                    iso_date = pub_dt.isoformat()
                else:
                    if link in seen_urls:
                        continue
                    iso_date = now_utc.isoformat()

                new_seen.add(link)
                candidates.append((source_name, title, link, iso_date))

        # Concurrently fetch full-text content
        sem = asyncio.Semaphore(10)
        texts = await asyncio.gather(*(fetch_full_text(client, c[2], sem) for c in candidates))

    records = []
    for (source_name, title, link, iso_date), full_text in zip(candidates, texts):
        entity = NewsEntity(
            source=SourceInfo(name=source_name, url=link),
            content=NewsContent(
                title=title,
                published_date=iso_date,
                full_text=full_text or title,
            ),
        )
        records.append(entity.model_dump())

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    SEEN_PATH.write_text(json.dumps(sorted(new_seen), indent=2), encoding="utf-8")
    print(f"[News] Saved {len(records)} fresh (<24h) AI news articles -> {OUTPUT_PATH}")
    return len(records)


if __name__ == "__main__":
    asyncio.run(scrape_news())