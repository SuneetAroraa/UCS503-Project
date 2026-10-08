import re
import spacy

nlp = spacy.load("en_core_web_sm")

WORD_REPLACEMENTS = {
    "approximately": "about",
    "assist": "help",
    "commence": "start",
    "demonstrate": "show",
    "numerous": "many",
    "utilize": "use",
    "require": "need",
    "requires": "needs",
    "obtain": "get",
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
    def replace_word(match):
        word = match.group(0)
        replacement = WORD_REPLACEMENTS.get(word.lower())

        if replacement is None:
            return word

        if word[0].isupper():
            return replacement.capitalize()

        return replacement

    return re.sub(r"\b[A-Za-z]+\b", replace_word, text)

def simplify_sentences(text: str):
    doc = nlp(text)
    simplified_sentences = []

    for sentence in doc.sents:
        sentence_text = sentence.text.strip()

        if sentence_text.lower().startswith("although "):
            parts = sentence_text.split(",", 1)

            if len(parts) == 2:
                first_part = parts[0]
                second_part = parts[1].strip()

                first_part = first_part[len("although "):]

                first_part = first_part.strip()
                second_part = second_part.strip()

                first_part = first_part[0].upper() + first_part[1:]
                second_part = second_part[0].upper() + second_part[1:]

                simplified_sentences.append(first_part + ".")
                simplified_sentences.append(second_part)

                continue

        simplified_sentences.append(sentence_text)

    return " ".join(simplified_sentences)

def simplify_text(text: str):
    text = simplify_sentences(text)
    text = simplify_context(text)
    text = simplify_words(text)

    return text

def simplify_context(text: str):
    for complex_phrase, simple_phrase in CONTEXT_REPLACEMENTS.items():
        text = text.replace(complex_phrase, simple_phrase)

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