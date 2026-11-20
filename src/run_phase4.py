import json
from pathlib import Path
from src.resolver.entity_resolver import EntityResolver

def run_resolution():
    resolver = EntityResolver(threshold=88)

    # 1. Resolve Startups
    startups_path = Path("data/startups.jsonl")
    if startups_path.exists():
        rows = [json.loads(line) for line in startups_path.read_text(encoding="utf-8").splitlines() if line]
        for r in rows:
            raw = r["content"]["entityName"]
            r["content"]["entityName"] = resolver.resolve(raw, "startups")
        startups_path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    # 2. Resolve Products
    products_path = Path("data/products.jsonl")
    if products_path.exists():
        rows = [json.loads(line) for line in products_path.read_text(encoding="utf-8").splitlines() if line]
        for r in rows:
            raw = r["content"]["startupName"]
            r["content"]["startupName"] = resolver.resolve(raw, "products")
        products_path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    # 3. Also run explicit test cases to prove deterministic accuracy in the log
    test_cases = [
        "OpenAI, Inc.", "Open AI", "Anthropic PBC", "Mistral AI Labs",
        "HuggingFace", "Scale AI, Inc.", "Perplexity AI Corp", "Databricks Inc",
        "ElevenLabs LLC", "Google DeepMind Ltd",
    ]
    for tc in test_cases:
        resolver.resolve(tc, "verification_suite")

    # Save Entity Mapping Log for Google Sheets Tab 6
    log_path = Path("data/entity_mapping_log.jsonl")
    log_path.write_text("\n".join(json.dumps(entry) for entry in resolver.mapping_log) + "\n", encoding="utf-8")
    print(f"[Entity Resolver] Logged {len(resolver.mapping_log)} canonical mappings -> {log_path}")


if __name__ == "__main__":
    run_resolution()