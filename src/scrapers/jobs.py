import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import dateparser
import httpx
from src.resolver.entity_resolver import EntityResolver
from src.schemas import JobEntity, JobContent, SourceInfo

GREENHOUSE_BOARDS = [
    ("Anthropic", "https://boards-api.greenhouse.io/v1/boards/anthropic/jobs"),
    ("Scale AI", "https://boards-api.greenhouse.io/v1/boards/scaleai/jobs"),
    ("xAI", "https://boards-api.greenhouse.io/v1/boards/xai/jobs"),
    ("Cohere", "https://boards-api.greenhouse.io/v1/boards/cohere/jobs"),
]
REMOTEOK_AI_API = "https://remoteok.com/api?tag=ai"
OUTPUT_PATH = Path("data/jobs.jsonl")


def infer_role_family(title: str) -> str:
    t = title.lower()
    if any(k in t for k in ("research", "scientist", "ml ", "machine learning", "ai ")):
        return "AI Research"
    if any(k in t for k in ("engineer", "developer", "architect", "sre", "devops", "infra")):
        return "Engineering"
    if any(k in t for k in ("product", "design", "ux")):
        return "Product & Design"
    if any(k in t for k in ("sales", "account", "marketing", "growth", "gtm")):
        return "Sales & Marketing"
    return "Operations & Other"


async def scrape_jobs() -> int:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    resolver = EntityResolver()
    now_utc = datetime.now(timezone.utc)
    cutoff = now_utc - timedelta(hours=24)
    records = []
    seen_urls = set()

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GraphOneBot/1.0"}

    async with httpx.AsyncClient(timeout=20.0, headers=headers, follow_redirects=True) as client:
        # Boards 1-4: Greenhouse AI company boards
        for company_raw, url in GREENHOUSE_BOARDS:
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    continue
                jobs = resp.json().get("jobs", [])
            except Exception:
                continue

            for j in jobs:
                job_url = j.get("absolute_url")
                updated_at = j.get("updated_at")
                if not job_url or job_url in seen_urls or not updated_at:
                    continue

                pub_dt = dateparser.parse(updated_at, settings={"RETURN_AS_TIMEZONE_AWARE": True, "TO_TIMEZONE": "UTC"})
                if not pub_dt or pub_dt < cutoff:
                    continue

                seen_urls.add(job_url)
                title = (j.get("title") or "").strip()
                loc = (j.get("location", {}).get("name") or "").lower()
                is_remote = "remote" in loc or "remote" in title.lower()

                entity = JobEntity(
                    source=SourceInfo(name=f"Greenhouse ({company_raw})", url=job_url),
                    content=JobContent(
                        company=resolver.resolve(company_raw, "jobs"),
                        title=title,
                        date=pub_dt.isoformat(),
                        is_remote=is_remote,
                        role_family=infer_role_family(title),
                    ),
                )
                records.append(entity.model_dump())

        # Board 5: RemoteOK AI Jobs
        try:
            resp = await client.get(REMOTEOK_AI_API)
            if resp.status_code == 200:
                for item in resp.json()[1:]:  # First element is API metadata
                    job_url = item.get("url")
                    raw_date = item.get("date")
                    if not job_url or job_url in seen_urls or not raw_date:
                        continue

                    pub_dt = dateparser.parse(raw_date, settings={"RETURN_AS_TIMEZONE_AWARE": True, "TO_TIMEZONE": "UTC"})
                    if not pub_dt or pub_dt < cutoff:
                        continue

                    seen_urls.add(job_url)
                    company_raw = item.get("company") or "Unknown"
                    title = (item.get("position") or "").strip()

                    entity = JobEntity(
                        source=SourceInfo(name="RemoteOK AI", url=job_url),
                        content=JobContent(
                            company=resolver.resolve(company_raw, "jobs"),
                            title=title,
                            date=pub_dt.isoformat(),
                            is_remote=True,
                            role_family=infer_role_family(title),
                        ),
                    )
                    records.append(entity.model_dump())
        except Exception:
            pass

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    print(f"[Jobs] Saved {len(records)} fresh (<24h) AI jobs -> {OUTPUT_PATH}")
    return len(records)


if __name__ == "__main__":
    asyncio.run(scrape_jobs())