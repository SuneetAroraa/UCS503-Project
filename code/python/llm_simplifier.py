
import os

from google import genai
from google.genai import types
from dotenv import load_dotenv
import json

load_dotenv()

MODEL_NAME = "gemini-3.8-flash"

SYSTEM_INSTRUCTION = """
You are a text simplification system.

Rewrite the supplied text in clear, simple English.

Rules:
- Preserve the original meaning and intent.
- Preserve negations, numbers, names, dates, and factual claims.
- Preserve technical terms when replacing them could change their meaning.
- Do not remove important information.
- Preserve paragraph breaks.
- Use shorter sentences where appropriate.
- Return only the simplified text, without explanations or quotation marks.
"""

_client = None


def get_gemini_client():
    global _client

    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    if _client is None:
        _client = genai.Client(
            api_key=os.environ["GEMINI_API_KEY"]
        )

    return _client


def simplify_with_gemini(text: str) -> str:
    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    client = get_gemini_client()

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=text,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.2,
            max_output_tokens=4096,
        ),
    )

    simplified_text = (response.text or "").strip()

    if not simplified_text:
        raise RuntimeError("Gemini returned an empty response.")

    return simplified_text


def simplify_many_with_gemini(texts: list[str]) -> list[str]:
    if not texts:
        return []

    if len(texts) > 5:
        raise ValueError("A batch can contain at most 5 paragraphs.")

    if any(not text.strip() for text in texts):
        raise ValueError("Batch paragraphs cannot be empty.")

    client = get_gemini_client()

    items = [
        {"id": index, "text": text}
        for index, text in enumerate(texts)
    ]

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=json.dumps(items, ensure_ascii=False),
        config=types.GenerateContentConfig(
            system_instruction=(
                "Simplify each text independently using clear, simple English. "
                "Preserve its meaning, negations, numbers, names, dates, and "
                "technical terms. Preserve paragraph boundaries. Keep every "
                "placeholder such as [[L1]] exactly unchanged and do not "
                "delete, duplicate, or invent placeholders. Do not combine "
                "texts or change their IDs. Return only a valid JSON array "
                "of objects with exactly these fields: id and text. "
                "Every input ID must occur exactly once."
            ),
            temperature=0.2,
            max_output_tokens=4096,
        ),
    )

    raw = (response.text or "").strip()

    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines).strip()

    try:
        results = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Gemini returned invalid batch JSON.") from exc

    if not isinstance(results, list) or len(results) != len(texts):
        raise RuntimeError("Gemini returned an incomplete batch.")

    indexed_results = {}

    for item in results:
        if not isinstance(item, dict):
            raise RuntimeError("Gemini returned an invalid batch item.")

        item_id = item.get("id")
        simplified = item.get("text")

        if (
            not isinstance(item_id, int)
            or isinstance(item_id, bool)
            or item_id < 0
            or item_id >= len(texts)
            or item_id in indexed_results
            or not isinstance(simplified, str)
            or not simplified.strip()
        ):
            raise RuntimeError("Gemini returned an invalid batch result.")

        indexed_results[item_id] = simplified.strip()

    if len(indexed_results) != len(texts):
        raise RuntimeError("Gemini omitted one or more batch items.")

    return [indexed_results[index] for index in range(len(texts))]
