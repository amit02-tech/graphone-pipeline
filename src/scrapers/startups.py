import asyncio
import json
from pathlib import Path
import httpx
from src.schemas import StartupEntity, StartupContent, StartupData, SourceInfo

YC_API_URL = "https://yc-oss.github.io/api/companies/all.json"
OUTPUT_PATH = Path("data/startups.jsonl")


async def scrape_startups(target_count: int = 1200) -> int:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    records = []
    seen_names = set()

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(YC_API_URL)
        resp.raise_for_status()
        companies = resp.json()

    # Prioritize AI/ML/SaaS startups first, then fill to target_count
    companies.sort(
        key=lambda c: any(
            kw in str(c.get("tags", [])).lower() or kw in str(c.get("one_liner", "")).lower()
            for kw in ("ai", "artificial intelligence", "machine learning", "llm")
        ),
        reverse=True,
    )

    for comp in companies:
        name = (comp.get("name") or "").strip()
        slug = comp.get("slug")
        if not name or name.lower() in seen_names:
            continue
        seen_names.add(name.lower())

        url = comp.get("url") or (f"https://www.ycombinator.com/companies/{slug}" if slug else comp.get("website"))
        if not url:
            continue

        emp_count = comp.get("team_size")
        try:
            emp_count = int(emp_count) if emp_count is not None else None
        except (ValueError, TypeError):
            emp_count = None

        entity = StartupEntity(
            source=SourceInfo(name="Y Combinator Directory", url=url),
            content=StartupContent(
                entityName=name,
                data=StartupData(employeeCount=emp_count),
            ),
        )
        records.append(entity.model_dump())

        if len(records) >= target_count:
            break

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    print(f"[Startups] Saved {len(records)} unique startups -> {OUTPUT_PATH}")
    return len(records)


if __name__ == "__main__":
    asyncio.run(scrape_startups())