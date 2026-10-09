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
    text = """The system makes use of numerous computational resources to process a large number of files."""

    result = process_text(text)

    print("ORIGINAL TEXT")
    print(text)

    print("\nSIMPLIFIED TEXT")
    print(result["simplified_text"])

    print("\nORIGINAL READABILITY")
    print(result["original_readability"])

    print("\nSIMPLIFIED READABILITY")
    print(result["simplified_readability"])

    print("\nCOMPARISON")

    for metric, values in result["comparison"].items():
        print(
            f"{metric}: "
            f"{values['original']} → "
            f"{values['simplified']} "
            f"({values['change']:+.2f})"
        )

    print("\nIMPROVEMENT SUMMARY")

    print(
        "Readability improved:",
        "YES" if result["summary"]["readability_improved"] else "NO"
    )

    print(
        f"Flesch improvement: "
        f"{result['summary']['flesch_improvement']:.2f}"
    )

    print(
        f"Grade-level reduction: "
        f"{result['summary']['grade_level_reduction']:.2f}"
    )

    if result["summary"]["smog_applicable"]:
        print(
            f"SMOG reduction: "
            f"{result['summary']['smog_reduction']:.2f}"
        )
    else:
        print("SMOG reduction: N/A (text has fewer than 30 sentences)")

    print(
        f"Difficult words reduced: "
        f"{result['summary']['difficult_words_reduced']}"
    )

if __name__ == "__main__":
    main()