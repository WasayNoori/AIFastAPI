import re
from typing import Tuple

_WORD_RE = re.compile(r"\b[\w’'-]+\b", flags=re.UNICODE)

def word_count(text: str) -> int:
    if not text:
        return 0
    return len(_WORD_RE.findall(text))

def syllable_count_en(text: str) -> int:
    """
    Simple English-oriented heuristic. Works as a rough gate only.
    If target languages are non-English, swap with a better estimator per language.
    """
    if not text:
        return 0
    count = 0
    for w in _WORD_RE.findall(text.lower()):
        w2 = re.sub(r'[^a-z]', '', w)
        if not w2:
            continue
        groups = re.findall(r"[aeiouy]+", w2)
        syl = len(groups)
        if w2.endswith("e"):
            syl -= 1
        count += max(1, syl)
    return max(1, count)

def compute_ranges(src_words: int, src_syll: int | None, tolerance: float, use_syllables: bool):
    min_words = int(round(src_words * (1 - tolerance)))
    max_words = int(round(src_words * (1 + tolerance)))
    if use_syllables and src_syll is not None:
        min_syll = int(round(src_syll * (1 - tolerance)))
        max_syll = int(round(src_syll * (1 + tolerance)))
    else:
        min_syll = max_syll = None
    return (min_words, max_words, min_syll, max_syll)

def needs_adjust(
    tgt_words: int,
    tgt_syll: int | None,
    min_words: int, max_words: int,
    min_syll: int | None, max_syll: int | None
) -> bool:
    words_ok = (min_words <= tgt_words <= max_words)
    syll_ok = True
    if min_syll is not None and max_syll is not None and tgt_syll is not None:
        syll_ok = (min_syll <= tgt_syll <= max_syll)
    return not (words_ok and syll_ok)


    