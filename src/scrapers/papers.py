import asyncio
import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
import httpx
from dotenv import load_dotenv
from src.schemas import ResearchPaperEntity, ResearchPaperContent, SourceInfo

load_dotenv()

ARXIV_API = "https://export.arxiv.org/api/query"
GITHUB_API = "https://api.github.com/repos"
OUTPUT_PATH = Path("data/papers.jsonl")
GITHUB_REGEX = re.compile(r"https?://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)")


async def fetch_github_stars(
    client: httpx.AsyncClient,
    repo_slug: str,
    semaphore: asyncio.Semaphore,
    headers: dict,
) -> tuple[str, int | None]:
    clean_slug = repo_slug.rstrip(".,);:]")
    if clean_slug.endswith(".git"):
        clean_slug = clean_slug[:-4]

    async with semaphore:
        try:
            resp = await client.get(f"{GITHUB_API}/{clean_slug}", headers=headers)
            if resp.status_code == 200:
                return f"https://github.com/{clean_slug}", resp.json().get("stargazers_count")
        except httpx.HTTPError:
            pass
    return f"https://github.com/{clean_slug}", None


async def scrape_papers(target_count: int = 1050) -> int:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    token = os.getenv("GITHUB_TOKEN")
    gh_headers = {"Accept": "application/vnd.github+json"}
    if token:
        gh_headers["Authorization"] = f"Bearer {token}"

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    raw_papers = []
    seen_urls = set()

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        start = 0
        batch_size = 200

        while len(raw_papers) < target_count:
            params = {
                "search_query": "(cat:cs.AI OR cat:cs.LG OR cat:cs.CL) AND all:github.com",
                "start": start,
                "max_results": batch_size,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            }
            resp = await client.get(ARXIV_API, params=params)
            resp.raise_for_status()

            root = ET.fromstring(resp.text)
            entries = root.findall("atom:entry", ns)
            if not entries:
                break

            for entry in entries:
                paper_url = entry.findtext("atom:id", default="", namespaces=ns).strip()
                if not paper_url or paper_url in seen_urls:
                    continue
                seen_urls.add(paper_url)

                title = " ".join(entry.findtext("atom:title", default="", namespaces=ns).split())
                summary = entry.findtext("atom:summary", default="", namespaces=ns)
                published = entry.findtext("atom:published", default="", namespaces=ns).strip()
                authors = [
                    a.findtext("atom:name", default="", namespaces=ns).strip()
                    for a in entry.findall("atom:author", ns)
                ]

                match = GITHUB_REGEX.search(summary)
                repo_slug = match.group(1) if match else None

                raw_papers.append(
                    {
                        "title": title,
                        "authors": authors,
                        "paper_url": paper_url,
                        "published_date": published,
                        "repo_slug": repo_slug,
                    }
                )
                if len(raw_papers) >= target_count:
                    break

            start += batch_size
            await asyncio.sleep(3)  # Respect ArXiv rate limit

        # Concurrently enrich GitHub star counts
        semaphore = asyncio.Semaphore(20)
        star_tasks = [
            fetch_github_stars(client, p["repo_slug"], semaphore, gh_headers)
            if p["repo_slug"]
            else asyncio.sleep(0, result=(None, None))
            for p in raw_papers
        ]
        star_results = await asyncio.gather(*star_tasks)

    records = []
    for paper, (gh_url, stars) in zip(raw_papers, star_results):
        entity = ResearchPaperEntity(
            source=SourceInfo(name="ArXiv", url=paper["paper_url"]),
            content=ResearchPaperContent(
                title=paper["title"],
                authors=paper["authors"],
                paper_url=paper["paper_url"],
                github_url=gh_url,
                github_stars=stars,
                published_date=paper["published_date"],
            ),
        )
        records.append(entity.model_dump())

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    print(f"[Papers] Saved {len(records)} unique papers with GitHub metrics -> {OUTPUT_PATH}")
    return len(records)


if __name__ == "__main__":
    asyncio.run(scrape_papers())
