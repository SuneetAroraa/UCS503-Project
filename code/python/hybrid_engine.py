
try:
    from .preprocessing import preprocess
    from .readability import calculate_readability
    from .simplifier import simplify_text
    from .evaluation import compare_readability, summarize_improvement
    from .llm_simplifier import simplify_with_gemini
    from .meaning_check import check_meaning
except ImportError:
    from preprocessing import preprocess
    from readability import calculate_readability
    from simplifier import simplify_text
    from evaluation import compare_readability, summarize_improvement
    from llm_simplifier import simplify_with_gemini
    from meaning_check import check_meaning


def _analyse_text(original_readability, candidate_text):
    readability = calculate_readability(candidate_text)
    comparison = compare_readability(original_readability, readability)
    summary = summarize_improvement(comparison)

    return {
        "readability": readability,
        "comparison": comparison,
        "summary": summary,
    }


def _build_evaluation_table(original_readability, rule_analysis, llm_analysis):
    rule_readability = rule_analysis["readability"]
    llm_readability = (
        llm_analysis["readability"] if llm_analysis is not None else None
    )

    metrics = [
        "word_count",
        "sentence_count",
        "average_sentence_length",
        "flesch_reading_ease",
        "flesch_kincaid_grade",
        "smog_index",
        "difficult_word_count",
    ]

    def metric_value(readability, metric):
        if metric == "difficult_word_count":
            return len(readability["difficult_words"])
        return readability[metric]

    table = []

    smog_applicable = (
        original_readability["sentence_count"] >= 30
        and rule_readability["sentence_count"] >= 30
        and (
            llm_readability is None
            or llm_readability["sentence_count"] >= 30
        )
    )

    for metric in metrics:
        original_value = metric_value(original_readability, metric)
        rule_value = metric_value(rule_readability, metric)
        llm_value = (
            metric_value(llm_readability, metric)
            if llm_readability is not None
            else None
        )

        table.append({
            "metric": metric,
            "original": original_value,
            "rules": rule_value,
            "gemini": llm_value,
            "rules_change": rule_value - original_value,
            "gemini_change": (
                llm_value - original_value
                if llm_value is not None else None
            ),
            "gemini_minus_rules": (
                llm_value - rule_value
                if llm_value is not None else None
            ),
            "applicable": (
                smog_applicable if metric == "smog_index" else True
            ),
        })

    return table


def process_text_with_mode(text: str, mode: str = "rules"):
    if mode not in {"rules", "llm", "hybrid"}:
        raise ValueError("Mode must be rules, llm, or hybrid.")

    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    processed = preprocess(text)
    original_readability = calculate_readability(text)

    rule_text = simplify_text(text)
    rule_analysis = _analyse_text(original_readability, rule_text)

    llm_text = None
    llm_analysis = None
    meaning_check = None
    fallback_used = False
    fallback_reason = None

    if mode in {"llm", "hybrid"}:
        try:
            candidate = simplify_with_gemini(text)
            candidate_check = check_meaning(text, candidate)

            llm_text = candidate
            llm_analysis = _analyse_text(original_readability, candidate)
            meaning_check = candidate_check

        except Exception:
            fallback_used = True
            fallback_reason = "Gemini processing or meaning checking failed."
            meaning_check = {
                "safe": False,
                "issues": [fallback_reason],
            }

    selected_engine = "rules"
    selected_text = rule_text
    selected_analysis = rule_analysis

    if mode == "llm" and llm_analysis is not None:
        selected_engine = "llm"
        selected_text = llm_text
        selected_analysis = llm_analysis

    elif mode == "hybrid":
        if llm_analysis is not None and meaning_check["safe"]:
            selected_engine = "llm"
            selected_text = llm_text
            selected_analysis = llm_analysis
        else:
            fallback_used = True
            if fallback_reason is None:
                fallback_reason = "Meaning check rejected the Gemini output."

    metric_keys = [
        "word_count",
        "sentence_count",
        "average_sentence_length",
        "flesch_reading_ease",
        "flesch_kincaid_grade",
        "smog_index",
        "difficult_word_count",
    ]

    rule_vs_llm = {}

    for key in metric_keys:
        if key == "difficult_word_count":
            rule_value = len(rule_analysis["readability"]["difficult_words"])
            llm_value = (
                len(llm_analysis["readability"]["difficult_words"])
                if llm_analysis is not None
                else None
            )
        else:
            rule_value = rule_analysis["readability"][key]
            llm_value = (
                llm_analysis["readability"][key]
                if llm_analysis is not None
                else None
            )

        rule_vs_llm[key] = {
            "rules": rule_value,
            "llm": llm_value,
            "difference": (
                llm_value - rule_value
                if llm_value is not None
                else None
            ),
        }

    return {
        "processed": processed,
        "mode": mode,
        "selected_engine": selected_engine,
        "fallback_used": fallback_used,
        "fallback_reason": fallback_reason,
        "original_readability": original_readability,
        "simplified_text": selected_text,
        "simplified_readability": selected_analysis["readability"],
        "comparison": selected_analysis["comparison"],
        "summary": selected_analysis["summary"],
        "rule_based_text": rule_text,
        "rule_based_readability": rule_analysis["readability"],
        "rule_based_comparison": rule_analysis["comparison"],
        "rule_based_summary": rule_analysis["summary"],
        "llm_text": llm_text,
        "llm_readability": (
            llm_analysis["readability"]
            if llm_analysis is not None
            else None
        ),
        "llm_comparison": (
            llm_analysis["comparison"]
            if llm_analysis is not None
            else None
        ),
        "llm_summary": (
            llm_analysis["summary"]
            if llm_analysis is not None
            else None
        ),
        "meaning_check": meaning_check,
        "rule_vs_llm": rule_vs_llm,
        "evaluation_table": _build_evaluation_table(
            original_readability,
            rule_analysis,
            llm_analysis,
        ),
    }



    