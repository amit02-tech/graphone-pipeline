import asyncio
import json
from pathlib import Path
import httpx
from src.schemas import ProductEntity, ProductContent, PricingModel, SourceInfo

HF_SPACES_API = "https://huggingface.co/api/spaces"
OUTPUT_PATH = Path("data/products.jsonl")


def infer_pricing(space: dict) -> PricingModel:
    tags = " ".join(space.get("tags", [])).lower()
    if "enterprise" in tags:
        return PricingModel.ENTERPRISE
    if "paid" in tags or "commercial" in tags:
        return PricingModel.PAID
    if space.get("runtime", {}).get("hardware", {}).get("current") not in (None, "cpu-basic"):
        return PricingModel.FREEMIUM
    return PricingModel.FREE


async def scrape_products(target_count: int = 1200) -> int:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    records = []
    seen_ids = set()

    # Fetch multiple slices to guarantee >1,200 unique AI products
    queries = [
        {"sort": "likes", "direction": "-1", "limit": 800},
        {"sort": "trendingScore", "direction": "-1", "limit": 800},
    ]

    async with httpx.AsyncClient(timeout=30.0) as client:
        for params in queries:
            if len(records) >= target_count:
                break
            resp = await client.get(HF_SPACES_API, params=params)
            resp.raise_for_status()
            spaces = resp.json()

            for sp in spaces:
                space_id = sp.get("id")
                if not space_id or space_id in seen_ids or "/" not in space_id:
                    continue
                seen_ids.add(space_id)

                org_or_author, product_name = space_id.split("/", 1)
                entity = ProductEntity(
                    source=SourceInfo(
                        name="Hugging Face Spaces",
                        url=f"https://huggingface.co/spaces/{space_id}",
                    ),
                    content=ProductContent(
                        startupName=org_or_author,
                        productName=product_name,
                        pricingModel=infer_pricing(sp),
                    ),
                )
                records.append(entity.model_dump())

                if len(records) >= target_count:
                    break

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    print(f"[Products] Saved {len(records)} unique AI products -> {OUTPUT_PATH}")
    return len(records)


if __name__ == "__main__":
    asyncio.run(scrape_products())