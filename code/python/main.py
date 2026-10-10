if __package__:
    from .preprocessing import preprocess
    from .readability import calculate_readability
    from .simplifier import simplify_text
    from .evaluation import compare_readability, summarize_improvement
else:
    from preprocessing import preprocess
    from readability import calculate_readability
    from simplifier import simplify_text
    from evaluation import compare_readability, summarize_improvement


def process_text(text: str):
    processed = preprocess(text)

    original_readability = calculate_readability(text)

    simplified_text = simplify_text(text)

    simplified_readability = calculate_readability(simplified_text)

    comparison = compare_readability(
        original_readability,
        simplified_readability
    )

    summary = summarize_improvement(comparison)

    return {
        "processed": processed,
        "original_readability": original_readability,
        "simplified_text": simplified_text,
        "simplified_readability": simplified_readability,
        "comparison": comparison,
        "summary": summary,
    }


def main():
    print("TEXT SIMPLIFIER")
    text = input("Enter text to simplify: ").strip()

    if not text:
        print("No text entered. Exiting.")
        return

    result = process_text(text)

    print("\n" + "=" * 65)
    print("TEXT SIMPLIFICATION RESULTS")
    print("=" * 65)

    print("\nORIGINAL TEXT")
    print(text)

    print("\nSIMPLIFIED TEXT")
    print(result["simplified_text"])

    labels = {
        "word_count": "Word Count",
        "sentence_count": "Sentence Count",
        "average_sentence_length": "Avg Sentence Length",
        "flesch_reading_ease": "Flesch Reading Ease",
        "flesch_kincaid_grade": "Grade Level",
        "smog_index": "SMOG Index",
        "difficult_word_count": "Difficult Words",
    }

    print("\n" + "-" * 65)
    print(f"{'METRIC':<26}{'ORIGINAL':>12}{'SIMPLIFIED':>14}{'CHANGE':>12}")
    print("-" * 65)

    for metric, label in labels.items():
        values = result["comparison"][metric]

        original = values["original"]
        simplified = values["simplified"]
        change = values["change"]

        print(
            f"{label:<26}"
            f"{original:>12.2f}"
            f"{simplified:>14.2f}"
            f"{change:>+12.2f}"
        )

    print("-" * 65)

    summary = result["summary"]

    print("\nIMPROVEMENT SUMMARY")
    print(
        "Readability improved:",
        "YES" if summary["readability_improved"] else "NO"
    )
    print(f"Flesch improvement: {summary['flesch_improvement']:.2f}")
    print(f"Grade-level reduction: {summary['grade_level_reduction']:.2f}")

    if summary["smog_applicable"]:
        print(f"SMOG reduction: {summary['smog_reduction']:.2f}")
    else:
        print("SMOG reduction: N/A (text has fewer than 30 sentences)")

    print(f"Difficult words reduced: {summary['difficult_words_reduced']}")
    print("=" * 65)


if __name__ == "__main__":
    main()