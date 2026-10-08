import spacy
import textstat

nlp = spacy.load("en_core_web_sm")


def count_words(doc):
    return len([
        token for token in doc
        if not token.is_punct and not token.is_space
    ])


def count_sentences(doc):
    return len(list(doc.sents))


def average_sentence_length(doc):
    sentences = list(doc.sents)

    if not sentences:
        return 0

    total_words = sum(
        len([
            token for token in sentence
            if not token.is_punct and not token.is_space
        ])
        for sentence in sentences
    )

    return total_words / len(sentences)


def find_difficult_words(doc):
    difficult_words = []

    for token in doc:
        if (
            token.is_alpha
            and not token.is_stop
            and len(token.text) >= 7
            and textstat.syllable_count(token.text) >= 3
        ):
            difficult_words.append(token.text.lower())

    return sorted(set(difficult_words))


def calculate_readability(text: str):

    doc = nlp(text)

    return {
        "word_count": count_words(doc),
        "sentence_count": count_sentences(doc),
        "average_sentence_length": average_sentence_length(doc),
        "flesch_reading_ease": textstat.flesch_reading_ease(text),
        "flesch_kincaid_grade": textstat.flesch_kincaid_grade(text),
        "smog_index": textstat.smog_index(text),
        "difficult_words": find_difficult_words(doc),
    }


if __name__ == "__main__":

    text = """
    The implementation of the system requires significant computational resources.
    The application provides intelligent assistance to users who experience difficulty
    understanding complex written content.
    """

    scores = calculate_readability(text)

    for key, value in scores.items():
        print(f"{key}: {value}")