import asyncio
import json
import logging
import os
import random
from typing import Type, TypeVar
import tiktoken
from dotenv import load_dotenv
from google import genai
from google.genai import types
from openai import AsyncOpenAI
from pydantic import BaseModel

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("LLMOrchestrator")

T = TypeVar("T", bound=BaseModel)


class LLMOrchestrator:
    def __init__(self, max_input_tokens: int = 3500):
        self.max_input_tokens = max_input_tokens
        self.encoder = tiktoken.get_encoding("cl100k_base")

        # Tier 1: Gemini Flash
        gemini_key = os.getenv("GEMINI_API_KEY")
        self.gemini_client = genai.Client(api_key=gemini_key) if gemini_key else None

        # Tier 2: Groq Llama 3 (OpenAI-compatible)
        groq_key = os.getenv("GROQ_API_KEY")
        self.groq_client = (
            AsyncOpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1")
            if groq_key
            else None
        )

        # Tier 3: DeepSeek (OpenAI-compatible)
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        self.deepseek_client = (
            AsyncOpenAI(api_key=deepseek_key, base_url="https://api.deepseek.com/v1")
            if deepseek_key
            else None
        )

    def smart_truncate(self, text: str) -> str:
        """Prevents 413 Payload Too Large by keeping head (title/intro) + tail (summary/dates)."""
        tokens = self.encoder.encode(text)
        if len(tokens) <= self.max_input_tokens:
            return text

        logger.warning(f"Payload too large ({len(tokens)} tokens). Truncating to {self.max_input_tokens}.")
        head_budget = int(self.max_input_tokens * 0.75)
        tail_budget = self.max_input_tokens - head_budget
        truncated = tokens[:head_budget] + tokens[-tail_budget:]
        return self.encoder.decode(truncated)

    async def _call_with_backoff(self, coro_fn, provider_name: str, retries: int = 3):
        """Handles 429 rate limits with exponential backoff + jitter."""
        for attempt in range(1, retries + 1):
            try:
                return await coro_fn()
            except Exception as e:
                err_str = str(e).lower()
                is_rate_limit = "429" in err_str or "rate limit" in err_str or "quota" in err_str
                if is_rate_limit and attempt < retries:
                    delay = (2 ** attempt) + random.uniform(0.2, 1.0)
                    logger.warning(f"[{provider_name}] 429 Rate Limit. Retrying in {delay:.2f}s (attempt {attempt}/{retries})")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"[{provider_name}] Failed: {e}")
                    raise

    async def _call_gemini(self, prompt: str) -> str:
        if not self.gemini_client:
            raise RuntimeError("GEMINI_API_KEY not configured")

        def _sync_call():
            resp = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            )
            return resp.text

        return await asyncio.to_thread(_sync_call)

    async def _call_openai_compat(self, client: AsyncOpenAI, model: str, prompt: str) -> str:
        resp = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Extract structured data and return ONLY valid JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        return resp.choices[0].message.content

    async def extract_structured(self, raw_text: str, schema_cls: Type[T], instructions: str) -> T:
        safe_text = self.smart_truncate(raw_text)
        schema_json = json.dumps(schema_cls.model_json_schema(), indent=2)
        prompt = (
            f"{instructions}\n\n"
            f"Return ONLY valid JSON matching this schema:\n{schema_json}\n\n"
            f"Source Content:\n{safe_text}"
        )

        tiers = [
            ("Gemini-Flash", lambda: self._call_gemini(prompt)),
            (
                "Groq-Llama3",
                lambda: self._call_openai_compat(self.groq_client, "llama-3.3-70b-versatile", prompt)
                if self.groq_client
                else (_ for _ in ()).throw(RuntimeError("GROQ_API_KEY not configured")),
            ),
            (
                "DeepSeek",
                lambda: self._call_openai_compat(self.deepseek_client, "deepseek-chat", prompt)
                if self.deepseek_client
                else (_ for _ in ()).throw(RuntimeError("DEEPSEEK_API_KEY not configured")),
            ),
        ]

        last_error = None
        for provider_name, fn in tiers:
            try:
                raw_json = await self._call_with_backoff(fn, provider_name)
                data = json.loads(raw_json)
                return schema_cls.model_validate(data)
            except Exception as e:
                last_error = e
                logger.warning(f"Falling back from {provider_name} to next tier...")

        raise RuntimeError(f"All LLM tiers failed. Last error: {last_error}")