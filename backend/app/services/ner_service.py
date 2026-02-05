"""
Named Entity Recognition service using spaCy.
Identifies: PERSON, ORG, DATE, GPE (locations), MONEY, etc.
"""

import spacy
from typing import Optional

# Lazy load model
_nlp = None


def get_nlp():
    """Lazy load spaCy model."""
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("⚠️  spaCy model not found. Run: python -m spacy download en_core_web_sm")
            return None
    return _nlp


def extract_entities(text: str, max_length: int = 100000) -> list[dict]:
    """
    Extract named entities from text.
    Returns list of {text, label, start, end} dicts.
    """
    nlp = get_nlp()
    if nlp is None:
        return []

    # Truncate very long texts to avoid memory issues
    if len(text) > max_length:
        text = text[:max_length]

    doc = nlp(text)

    entities = []
    seen = set()

    for ent in doc.ents:
        # Deduplicate
        key = (ent.text.strip(), ent.label_)
        if key in seen:
            continue
        seen.add(key)

        entities.append({
            "text": ent.text.strip(),
            "label": ent.label_,
            "start": ent.start_char,
            "end": ent.end_char,
        })

    return entities


def extract_entities_summary(text: str) -> dict:
    """
    Extract entities and group them by type.
    Returns {PERSON: [...], ORG: [...], DATE: [...], ...}
    """
    entities = extract_entities(text)
    grouped = {}

    for ent in entities:
        label = ent["label"]
        if label not in grouped:
            grouped[label] = []
        if ent["text"] not in grouped[label]:
            grouped[label].append(ent["text"])

    return grouped
