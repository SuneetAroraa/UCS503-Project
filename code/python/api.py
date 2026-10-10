
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

try:
    from .hybrid_engine import process_text_with_mode
except ImportError:
    from hybrid_engine import process_text_with_mode


app = FastAPI(
    title="Text Simplification API",
    description="Compare rule-based and Gemini text simplification.",
    version="2.0.0",
)


class TextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    mode: Literal["rules", "llm", "hybrid"] = "rules"


class HealthResponse(BaseModel):
    status: str


class ProcessedSentence(BaseModel):
    id: int
    raw_text: str
    tokens: list[str]
    pos_tags: list[str]


class ReadabilityScores(BaseModel):
    word_count: int
    sentence_count: int
    average_sentence_length: float
    flesch_reading_ease: float
    flesch_kincaid_grade: float
    smog_index: float
    difficult_words: list[str]


class MetricComparison(BaseModel):
    original: int | float
    simplified: int | float
    change: int | float


class ImprovementSummary(BaseModel):
    readability_improved: bool
    flesch_improvement: float
    grade_level_reduction: float
    smog_reduction: float
    smog_applicable: bool
    difficult_words_reduced: int


class MeaningCheck(BaseModel):
    safe: bool
    issues: list[str]


class RuleVsLLMMetric(BaseModel):
    rules: int | float
    llm: int | float | None
    difference: int | float | None


class EvaluationRow(BaseModel):
    metric: str
    original: int | float
    rules: int | float
    gemini: int | float | None
    rules_change: int | float
    gemini_change: int | float | None
    gemini_minus_rules: int | float | None
    applicable: bool

class SimplifyResponse(BaseModel):
    processed: list[ProcessedSentence]
    mode: str
    selected_engine: str
    fallback_used: bool
    fallback_reason: str | None

    original_readability: ReadabilityScores
    simplified_text: str
    simplified_readability: ReadabilityScores
    comparison: dict[str, MetricComparison]
    summary: ImprovementSummary

    rule_based_text: str
    rule_based_readability: ReadabilityScores
    rule_based_comparison: dict[str, MetricComparison]
    rule_based_summary: ImprovementSummary

    llm_text: str | None
    llm_readability: ReadabilityScores | None
    llm_comparison: dict[str, MetricComparison] | None
    llm_summary: ImprovementSummary | None

    meaning_check: MeaningCheck | None
    rule_vs_llm: dict[str, RuleVsLLMMetric]
    evaluation_table: list[EvaluationRow]


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok"}


@app.post("/simplify", response_model=SimplifyResponse)
def simplify(request: TextRequest):
    text = request.text.strip()

    if not text:
        raise HTTPException(
            status_code=422,
            detail="Text cannot be empty.",
        )

    try:
        return process_text_with_mode(text, request.mode)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Text processing failed.",
        ) from exc
