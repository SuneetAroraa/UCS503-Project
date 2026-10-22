
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

try:
    from .hybrid_engine import process_text_with_mode
    from .llm_simplifier import simplify_many_with_gemini
    from .meaning_check import check_meaning
    from .readability import calculate_readability
    from .evaluation import compare_readability, summarize_improvement
except ImportError:
    from hybrid_engine import process_text_with_mode
    from llm_simplifier import simplify_many_with_gemini
    from meaning_check import check_meaning
    from readability import calculate_readability
    from evaluation import compare_readability, summarize_improvement


app = FastAPI(
    title="Text Simplification API",
    description="Compare rule-based and Gemini text simplification.",
    version="2.1.0",
)


class TextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    mode: Literal["rules", "llm", "hybrid"] = "rules"


class BatchTextRequest(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=5)
    mode: Literal["rules", "llm", "hybrid"] = "hybrid"


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


class BatchItemResponse(BaseModel):
    index: int
    mode: str
    selected_engine: str
    fallback_used: bool
    fallback_reason: str | None

    simplified_text: str
    original_readability: ReadabilityScores
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


class BatchSimplifyResponse(BaseModel):
    mode: str
    results: list[BatchItemResponse]


def build_rule_vs_llm(rule_readability, llm_readability):
    metrics = [
        "word_count",
        "sentence_count",
        "average_sentence_length",
        "flesch_reading_ease",
        "flesch_kincaid_grade",
        "smog_index",
        "difficult_word_count",
    ]

    result = {}

    for metric in metrics:
        if metric == "difficult_word_count":
            rule_value = len(rule_readability["difficult_words"])
            llm_value = (
                len(llm_readability["difficult_words"])
                if llm_readability is not None
                else None
            )
        else:
            rule_value = rule_readability[metric]
            llm_value = (
                llm_readability[metric]
                if llm_readability is not None
                else None
            )

        result[metric] = {
            "rules": rule_value,
            "llm": llm_value,
            "difference": (
                llm_value - rule_value
                if llm_value is not None
                else None
            ),
        }

    return result


def build_evaluation_table(original, rule_readability, llm_readability):
    metrics = [
        "word_count",
        "sentence_count",
        "average_sentence_length",
        "flesch_reading_ease",
        "flesch_kincaid_grade",
        "smog_index",
        "difficult_word_count",
    ]

    def get_value(readability, metric):
        if metric == "difficult_word_count":
            return len(readability["difficult_words"])
        return readability[metric]

    rows = []

    for metric in metrics:
        original_value = get_value(original, metric)
        rule_value = get_value(rule_readability, metric)
        llm_value = (
            get_value(llm_readability, metric)
            if llm_readability is not None
            else None
        )

        if metric == "smog_index":
            applicable = (
                original["sentence_count"] >= 30
                and rule_readability["sentence_count"] >= 30
                and (
                    llm_readability is None
                    or llm_readability["sentence_count"] >= 30
                )
            )
        else:
            applicable = True

        rows.append({
            "metric": metric,
            "original": original_value,
            "rules": rule_value,
            "gemini": llm_value,
            "rules_change": rule_value - original_value,
            "gemini_change": (
                llm_value - original_value
                if llm_value is not None
                else None
            ),
            "gemini_minus_rules": (
                llm_value - rule_value
                if llm_value is not None
                else None
            ),
            "applicable": applicable,
        })

    return rows


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


@app.post("/simplify/batch", response_model=BatchSimplifyResponse)
def simplify_batch(request: BatchTextRequest):
    texts = [text.strip() for text in request.texts]

    if any(not text for text in texts):
        raise HTTPException(
            status_code=422,
            detail="Batch paragraphs cannot be empty.",
        )

    if any(len(text) > 20000 for text in texts):
        raise HTTPException(
            status_code=422,
            detail="Each paragraph must contain at most 20000 characters.",
        )

    try:
        rule_results = [
            process_text_with_mode(text, "rules")
            for text in texts
        ]

        candidates = None
        batch_error = None

        if request.mode in {"llm", "hybrid"}:
            try:
                candidates = simplify_many_with_gemini(texts)

                if (
                    not isinstance(candidates, list)
                    or len(candidates) != len(texts)
                    or any(
                        not isinstance(candidate, str) or not candidate.strip()
                        for candidate in candidates
                    )
                ):
                    raise RuntimeError(
                        "Gemini returned an invalid batch response."
                    )

            except Exception:
                batch_error = (
                    "Gemini batch processing failed; rule-based output was used."
                )

        results = []

        for index, (text, rule_result) in enumerate(
            zip(texts, rule_results)
        ):
            original_readability = rule_result["original_readability"]
            rule_text = rule_result["rule_based_text"]
            rule_readability = rule_result["rule_based_readability"]

            candidate = (
                candidates[index]
                if candidates is not None
                else None
            )

            meaning_result = (
                check_meaning(text, candidate)
                if candidate is not None
                else None
            )

            llm_readability = (
                calculate_readability(candidate)
                if candidate is not None
                else None
            )

            llm_comparison = (
                compare_readability(
                    original_readability,
                    llm_readability,
                )
                if llm_readability is not None
                else None
            )

            llm_summary = (
                summarize_improvement(llm_comparison)
                if llm_comparison is not None
                else None
            )

            use_llm = (
                candidate is not None
                and (
                    request.mode == "llm"
                    or (
                        request.mode == "hybrid"
                        and meaning_result["safe"]
                    )
                )
            )

            selected_text = candidate if use_llm else rule_text

            selected_readability = (
                llm_readability
                if use_llm
                else rule_readability
            )

            selected_comparison = (
                llm_comparison
                if use_llm
                else rule_result["rule_based_comparison"]
            )

            selected_summary = (
                llm_summary
                if use_llm
                else rule_result["rule_based_summary"]
            )

            fallback_used = (
                request.mode in {"llm", "hybrid"}
                and not use_llm
            )

            if batch_error:
                fallback_reason = batch_error
            elif (
                request.mode == "hybrid"
                and candidate is not None
                and not use_llm
            ):
                fallback_reason = (
                    "Meaning check rejected the Gemini output."
                )
            elif request.mode == "llm" and candidate is None:
                fallback_reason = (
                    "Gemini failed; rule-based output was used."
                )
            else:
                fallback_reason = None

            results.append({
                "index": index,
                "mode": request.mode,
                "selected_engine": "llm" if use_llm else "rules",
                "fallback_used": fallback_used,
                "fallback_reason": fallback_reason,
                "simplified_text": selected_text,
                "original_readability": original_readability,
                "simplified_readability": selected_readability,
                "comparison": selected_comparison,
                "summary": selected_summary,
                "rule_based_text": rule_text,
                "rule_based_readability": rule_readability,
                "rule_based_comparison": rule_result[
                    "rule_based_comparison"
                ],
                "rule_based_summary": rule_result["rule_based_summary"],
                "llm_text": candidate,
                "llm_readability": llm_readability,
                "llm_comparison": llm_comparison,
                "llm_summary": llm_summary,
                "meaning_check": meaning_result,
                "rule_vs_llm": build_rule_vs_llm(
                    rule_readability,
                    llm_readability,
                ),
                "evaluation_table": build_evaluation_table(
                    original_readability,
                    rule_readability,
                    llm_readability,
                ),
            })

        return {
            "mode": request.mode,
            "results": results,
        }

    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Batch text processing failed.",
        ) from exc
