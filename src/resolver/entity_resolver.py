import re
from rapidfuzz import fuzz, process

CANONICAL_AI_STARTUPS = [
    "OpenAI", "Anthropic", "Google DeepMind", "Hugging Face", "Scale AI",
    "Mistral AI", "Perplexity AI", "Groq", "Cohere", "Databricks",
    "xAI", "Stability AI", "Midjourney", "Runway", "ElevenLabs",
    "Character.AI", "Inflection AI", "Adept", "Weights & Biases", "LangChain",
    "Pinecone", "Weaviate", "Qdrant", "Modal", "Together AI",
    "Fireworks AI", "Anyscale", "Replicate", "Vercel", "Supabase",
    "Cursor", "Cognition", "Glean", "Harvey", "Sierra",
    "Figure AI", "Anduril", "Palantir", "Cerebras", "SambaNova",
    "CoreWeave", "Lambda", "Poolside", "Magic", "Sakana AI",
    "Synthesia", "HeyGen", "Jasper", "Writer", "Abridge",
]

LEGAL_SUFFIX_REGEX = re.compile(
    r"\b(inc\.?|llc\.?|ltd\.?|corp\.?|corporation|pbc|gmbh|co\.?|technologies|technology|labs)\b",
    re.IGNORECASE,
)


class EntityResolver:
    def __init__(self, threshold: int = 88):
        self.threshold = threshold
        self.canonical_list = CANONICAL_AI_STARTUPS
        self.norm_to_canonical = {self._normalize(name): name for name in self.canonical_list}
        self.mapping_log: list[dict] = []

    @staticmethod
    def _normalize(name: str) -> str:
        cleaned = LEGAL_SUFFIX_REGEX.sub("", name)
        cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", cleaned)
        return " ".join(cleaned.lower().split())

    def resolve(self, raw_name: str, source_dataset: str = "unknown") -> str:
        if not raw_name or not raw_name.strip():
            return raw_name

        norm = self._normalize(raw_name)

        # 1. Exact normalized match
        if norm in self.norm_to_canonical:
            canonical = self.norm_to_canonical[norm]
            self._log(raw_name, canonical, "EXACT_NORMALIZED", 100.0, source_dataset)
            return canonical

        # 2. High-confidence fuzzy match against canonical seed list
        match = process.extractOne(
            norm,
            list(self.norm_to_canonical.keys()),
            scorer=fuzz.token_sort_ratio,
        )
        if match and match[1] >= self.threshold:
            canonical = self.norm_to_canonical[match[0]]
            self._log(raw_name, canonical, "FUZZY_MATCH", round(float(match[1]), 2), source_dataset)
            return canonical

        # 3. Clean fallback (strip legal suffixes only)
        cleaned_display = re.sub(r"\s+", " ", LEGAL_SUFFIX_REGEX.sub("", raw_name)).strip(" ,.-")
        final_name = cleaned_display or raw_name.strip()
        if final_name != raw_name.strip():
            self._log(raw_name, final_name, "SUFFIX_STRIPPED", 95.0, source_dataset)
        return final_name

    def _log(self, raw: str, canonical: str, match_type: str, score: float, dataset: str):
        self.mapping_log.append(
            {
                "raw_name": raw,
                "canonical_name": canonical,
                "match_type": match_type,
                "confidence_score": score,
                "source_dataset": dataset,
            }
        )