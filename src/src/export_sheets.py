import json
import re
from pathlib import Path
import pandas as pd

ILLEGAL_CHAR_RE = re.compile(r"[\000-\010]|[\013-\014]|[\016-\037]")


def clean_str(val):
    if isinstance(val, str):
        return ILLEGAL_CHAR_RE.sub("", val)[:32000]
    return val


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def export_all():
    out_file = Path("data/GraphOne_Data_Output.xlsx")

    # 1. Startups
    startups_raw = load_jsonl(Path("data/startups.jsonl"))
    df_startups = pd.DataFrame([
        {
            "schemaVersion": r["schemaVersion"],
            "recordType": r["recordType"],
            "source.name": r["source"]["name"],
            "source.url": r["source"]["url"],
            "content.entityName": r["content"]["entityName"],
            "content.data.employeeCount": r["content"]["data"].get("employeeCount"),
            "collectedAt": r["collectedAt"],
        }
        for r in startups_raw
    ])

    # 2. Products
    products_raw = load_jsonl(Path("data/products.jsonl"))
    df_products = pd.DataFrame([
        {
            "schemaVersion": r["schemaVersion"],
            "recordType": r["recordType"],
            "source.name": r["source"]["name"],
            "source.url": r["source"]["url"],
            "content.startupName": r["content"]["startupName"],
            "content.productName": r["content"].get("productName"),
            "content.pricingModel": r["content"]["pricingModel"],
            "collectedAt": r["collectedAt"],
        }
        for r in products_raw
    ])

    # 3. Research Papers
    papers_raw = load_jsonl(Path("data/papers.jsonl"))
    df_papers = pd.DataFrame([
        {
            "schemaVersion": r["schemaVersion"],
            "recordType": r["recordType"],
            "source.name": r["source"]["name"],
            "source.url": r["source"]["url"],
            "content.title": clean_str(r["content"]["title"]),
            "content.authors": ", ".join(r["content"].get("authors", [])),
            "content.paper_url": r["content"]["paper_url"],
            "content.github_url": r["content"].get("github_url"),
            "content.github_stars": r["content"].get("github_stars"),
            "content.published_date": r["content"]["published_date"],
            "collectedAt": r["collectedAt"],
        }
        for r in papers_raw
    ])

    # 4. Jobs
    jobs_raw = load_jsonl(Path("data/jobs.jsonl"))
    df_jobs = pd.DataFrame([
        {
            "schemaVersion": r["schemaVersion"],
            "recordType": r["recordType"],
            "source.name": r["source"]["name"],
            "source.url": r["source"]["url"],
            "content.company": r["content"]["company"],
            "content.title": clean_str(r["content"].get("title", "")),
            "content.date": r["content"]["date"],
            "content.is_remote": r["content"]["is_remote"],
            "content.role_family": r["content"]["role_family"],
            "collectedAt": r["collectedAt"],
        }
        for r in jobs_raw
    ])

    # 5. News
    news_raw = load_jsonl(Path("data/news.jsonl"))
    df_news = pd.DataFrame([
        {
            "schemaVersion": r["schemaVersion"],
            "recordType": r["recordType"],
            "source.name": r["source"]["name"],
            "source.url": r["source"]["url"],
            "content.title": clean_str(r["content"]["title"]),
            "content.published_date": r["content"]["published_date"],
            "content.full_text": clean_str(r["content"]["full_text"]),
            "collectedAt": r["collectedAt"],
        }
        for r in news_raw
    ])

    # 6. Entity Mapping Log
    log_raw = load_jsonl(Path("data/entity_mapping_log.jsonl"))
    df_log = pd.DataFrame(log_raw)

    with pd.ExcelWriter(out_file, engine="openpyxl") as writer:
        df_startups.to_excel(writer, sheet_name="Startups", index=False)
        df_products.to_excel(writer, sheet_name="Products", index=False)
        df_papers.to_excel(writer, sheet_name="Research Papers", index=False)
        df_jobs.to_excel(writer, sheet_name="Jobs", index=False)
        df_news.to_excel(writer, sheet_name="News", index=False)
        df_log.to_excel(writer, sheet_name="Entity Mapping Log", index=False)

    print(f"Successfully exported all 6 tabs -> {out_file.resolve()}")
    print(f"Row counts | Startups: {len(df_startups)}, Products: {len(df_products)}, Papers: {len(df_papers)}, Jobs: {len(df_jobs)}, News: {len(df_news)}, Mappings: {len(df_log)}")


if __name__ == "__main__":
    export_all()