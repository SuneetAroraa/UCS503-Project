
import os

from google import genai
from google.genai import types


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
