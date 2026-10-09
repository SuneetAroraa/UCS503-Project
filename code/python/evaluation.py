def compare_readability(original, simplified):
    comparison = {}

    comparison["word_count"] = {
        "original": original["word_count"],
        "simplified": simplified["word_count"],
        "change": simplified["word_count"] - original["word_count"],
    }

    comparison["sentence_count"] = {
        "original": original["sentence_count"],
        "simplified": simplified["sentence_count"],
        "change": simplified["sentence_count"] - original["sentence_count"],
    }

    comparison["average_sentence_length"] = {
        "original": original["average_sentence_length"],
        "simplified": simplified["average_sentence_length"],
        "change": (
            simplified["average_sentence_length"]
            - original["average_sentence_length"]
        ),
    }

    comparison["flesch_reading_ease"] = {
        "original": original["flesch_reading_ease"],
        "simplified": simplified["flesch_reading_ease"],
        "change": (
            simplified["flesch_reading_ease"]
            - original["flesch_reading_ease"]
        ),
    }

    comparison["flesch_kincaid_grade"] = {
        "original": original["flesch_kincaid_grade"],
        "simplified": simplified["flesch_kincaid_grade"],
        "change": (
            simplified["flesch_kincaid_grade"]
            - original["flesch_kincaid_grade"]
        ),
    }

    comparison["smog_index"] = {
        "original": original["smog_index"],
        "simplified": simplified["smog_index"],
        "change": (
            simplified["smog_index"]
            - original["smog_index"]
        ),
    }

    comparison["difficult_word_count"] = {
        "original": len(original["difficult_words"]),
        "simplified": len(simplified["difficult_words"]),
        "change": (
            len(simplified["difficult_words"])
            - len(original["difficult_words"])
        ),
    }

    return comparison


def summarize_improvement(comparison):
    flesch_change = comparison["flesch_reading_ease"]["change"]
    grade_change = comparison["flesch_kincaid_grade"]["change"]
    smog_change = comparison["smog_index"]["change"]
    difficult_word_change = comparison["difficult_word_count"]["change"]

    original_sentences = comparison["sentence_count"]["original"]
    simplified_sentences = comparison["sentence_count"]["simplified"]

    smog_applicable = (
        original_sentences >= 30
        and simplified_sentences >= 30
    )

    readability_improved = (
        flesch_change > 0
        and grade_change < 0
        and (not smog_applicable or smog_change < 0)
    )

    return {
        "readability_improved": readability_improved,
        "flesch_improvement": flesch_change,
        "grade_level_reduction": -grade_change,
        "smog_reduction": -smog_change,
        "smog_applicable": smog_applicable,
        "difficult_words_reduced": -difficult_word_change,
    }
