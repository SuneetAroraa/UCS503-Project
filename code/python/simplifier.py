import re
import spacy

nlp = spacy.load("en_core_web_sm")

WORD_REPLACEMENTS = {
    "approximately": "about",
    "assist": "help",
    "assists": "helps",
    "assisted": "helped",
    "assisting": "helping",
    "commence": "start",
    "commences": "starts",
    "commenced": "started",
    "commencing": "starting",
    "demonstrate": "show",
    "demonstrates": "shows",
    "demonstrated": "showed",
    "demonstrating": "showing",
    "numerous": "many",
    "utilize": "use",
    "utilizes": "uses",
    "utilized": "used",
    "utilizing": "using",
    "require": "need",
    "requires": "needs",
    "required": "needed",
    "requiring": "needing",
    "requirement": "need",
    "requirements": "needs",
    "obtain": "get",
    "obtains": "gets",
    "obtained": "got",
    "obtaining": "getting",
    "additional": "extra",
    "significant": "important",
}

CONTEXT_REPLACEMENTS = {
    "makes use of numerous computational resources":
        "uses a lot of computing power",

    "makes use of":
        "uses",

    "computational resources":
        "computing resources",

    "a large number of":
        "many",

    "at this point in time":
        "now",

    "due to the fact that":
        "because",
}


def simplify_words(text: str):
    protected_phrases = {}
    pattern = re.compile(
        r"\bstatistically\s+significant\b|\bsignificant\s+other\b",
        re.IGNORECASE,
    )

    def protect_phrase(match):
        placeholder = f"ZXQPROTECTED{len(protected_phrases)}QXZ"
        protected_phrases[placeholder] = match.group(0)
        return placeholder

    text = pattern.sub(protect_phrase, text)

    def replace_word(match):
        word = match.group(0)
        replacement = WORD_REPLACEMENTS.get(word.lower())

        if replacement is None:
            return word

        if word.isupper():
            return replacement.upper()

        if word.istitle():
            return replacement.capitalize()

        return replacement

    text = re.sub(r"\b[A-Za-z]+\b", replace_word, text)

    for placeholder, phrase in protected_phrases.items():
        text = text.replace(placeholder, phrase)

    return text


def simplify_sentences(text: str):
    doc = nlp(text)
    simplified_sentences = []

    for sentence in doc.sents:
        sentence_text = sentence.text.strip()

        if sentence_text.lower().startswith("although "):
            marker = next(
                (
                    token for token in sentence
                    if token.lower_ == "although"
                ),
                None,
            )

            if marker is not None and marker.dep_ == "mark":
                clause_root = marker.head

                clause_words = [
                    token for token in clause_root.subtree
                    if not token.is_punct and not token.is_space
                ]

                if clause_words:
                    clause_end = max(token.i for token in clause_words)
                    main_root = sentence.root

                    separator = next(
                        (
                            token for token in sentence
                            if token.text == ","
                            and clause_end < token.i < main_root.i
                        ),
                        None,
                    )

                    if separator is not None:
                        split_position = (
                            separator.idx - sentence.start_char
                        )

                        first_part = sentence_text[:split_position].strip()
                        second_part = sentence_text[
                            split_position + 1:
                        ].strip()

                        first_part = re.sub(
                            r"(?i)^although\s+",
                            "",
                            first_part,
                        ).strip()

                        if first_part and second_part:
                            first_part = (
                                first_part[0].upper()
                                + first_part[1:]
                            )

                            simplified_sentences.append(first_part + ".")
                            simplified_sentences.append(
                                "However, " + second_part
                            )
                            continue

        simplified_sentences.append(sentence_text)

    return " ".join(simplified_sentences)

def simplify_context(text: str):
    replacements = sorted(
        CONTEXT_REPLACEMENTS.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    )

    for phrase, replacement in replacements:
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)

        def replace_phrase(match):
            original = match.group(0)

            if original.isupper():
                return replacement.upper()

            if original[0].isupper():
                return replacement.capitalize()

            return replacement

        text = pattern.sub(replace_phrase, text)

    return text

def simplify_text(text: str):
    text = simplify_sentences(text)
    text = simplify_context(text)
    text = simplify_words(text)

    return text



if __name__ == "__main__":

    text = """
    Although the application requires significant resources,
    it provides accessibility features that assist users.
    """

    print("Original:")
    print(text)

    print("\nSimplified:")
    print(simplify_text(text))