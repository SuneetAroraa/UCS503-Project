try:
    from .nlp_model import nlp
except ImportError:
    from nlp_model import nlp


def segment_sentences(text: str):
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents]


def process_sentence(sent_span, sent_id: int):
    return {
        "id": sent_id,
        "raw_text": sent_span.text.strip(),
        "tokens": [token.text for token in sent_span],
        "pos_tags": [token.pos_ for token in sent_span],
    }


def preprocess(text: str):
    doc = nlp(text)

    return [
        process_sentence(sent, i)
        for i, sent in enumerate(doc.sents)
    ]