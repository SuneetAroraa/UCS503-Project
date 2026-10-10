
import re
from collections import Counter

try:
    from .nlp_model import nlp
except ImportError:
    from nlp_model import nlp


NEGATION_PATTERN = re.compile(
    r"\b(?:not|no|never|neither|nor|without|unless|"
    r"cannot|can't|couldn't|didn't|doesn't|don't|"
    r"isn't|aren't|wasn't|weren't|won't|wouldn't|"
    r"shouldn't|mustn't|hardly|rarely)\b",
    re.IGNORECASE,
)

NUMBER_PATTERN = re.compile(
    r"(?<!\w)(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%?(?!\w)"
)

IMPORTANT_ENTITY_LABELS = {
    "PERSON",
    "ORG",
    "GPE",
    "LOC",
    "DATE",
    "TIME",
    "MONEY",
    "PERCENT",
    "QUANTITY",
    "PRODUCT",
}


def normalize_text(text: str) -> str:
    return re.sub(r"[^\w%]+", " ", text.casefold()).strip()


def extract_negations(text: str) -> Counter:
    return Counter(
        match.group(0).casefold()
        for match in NEGATION_PATTERN.finditer(text)
    )


def extract_numbers(text: str) -> Counter:
    return Counter(
        match.group(0).replace(",", "").casefold()
        for match in NUMBER_PATTERN.finditer(text)
    )


def check_meaning(original: str, candidate: str) -> dict:
    issues = []

    if not original.strip() or not candidate.strip():
        return {
            "safe": False,
            "issues": ["Original text or candidate text is empty."],
        }

    original_negations = extract_negations(original)
    candidate_negations = extract_negations(candidate)

    if original_negations != candidate_negations:
        issues.append("Negation words changed.")

    original_numbers = extract_numbers(original)
    candidate_numbers = extract_numbers(candidate)

    if original_numbers != candidate_numbers:
        issues.append("Numbers or percentages changed.")

    normalized_candidate = normalize_text(candidate)

    original_doc = nlp(original)

    for entity in original_doc.ents:
        if entity.label_ not in IMPORTANT_ENTITY_LABELS:
            continue

        entity_text = normalize_text(entity.text)

        if (
            entity_text
            and not re.search(
                r"(?<!\w)"
                + re.escape(entity_text)
                + r"(?!\w)",
                normalized_candidate,
            )
        ):
            issues.append(
                f"Named entity may have changed: {entity.text}"
            )

    return {
        "safe": len(issues) == 0,
        "issues": issues,
    }
