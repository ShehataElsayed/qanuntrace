"""Conservative parsing of Arabic legislative references, never source identity proof."""
from __future__ import annotations

import re
from dataclasses import dataclass

from .core import reference_key

_DIG = r"[0-9٠-٩۰-۹]+"
_UNIT = {"الأولى": 1, "الأول": 1, "الثانية": 2, "الثاني": 2, "الثالثة": 3, "الثالث": 3,
         "الرابعة": 4, "الرابع": 4, "الخامسة": 5, "الخامس": 5, "السادسة": 6, "السادس": 6,
         "السابعة": 7, "السابع": 7, "الثامنة": 8, "الثامن": 8, "التاسعة": 9, "التاسع": 9,
         "العاشرة": 10, "العاشر": 10}
_TEN = {"العشرون": 20, "العشرين": 20, "الثلاثون": 30, "الثلاثين": 30,
        "الأربعون": 40, "الأربعين": 40, "الخمسون": 50, "الخمسين": 50,
        "الستون": 60, "الستين": 60, "السبعون": 70, "السبعين": 70,
        "الثمانون": 80, "الثمانين": 80, "التسعون": 90, "التسعين": 90}
_HUNDREDS = {"المائة": 100, "المئة": 100, "مائة": 100, "مئة": 100,
             "المائتين": 200, "المئتين": 200, "مائتين": 200, "مئتين": 200}
_ORD = {"الأول": 1, "الأولى": 1, "ثانياً": 2, "ثانيا": 2, "الثاني": 2,
        "الثالث": 3, "ثالثاً": 3, "ثالثا": 3, "رابعاً": 4, "رابعا": 4}
_WORD = r"[ء-يًٌٍَُِّْـ]+"
_PATTERN = re.compile(r"(?:المادة|مادة|المادّه|article)\s+([^،؛.\n!?]{1,100})", re.IGNORECASE)
_STOP = re.compile(r"\s+(?:من|في|بشأن|بموجب|حسب|وفق|التي|المتعلقة|بالنسبة)\b")

@dataclass(frozen=True)
class LegislativeReference:
    article: int | None
    repeated: int | None
    paragraph: str | None
    item: str | None
    original: str
    needs_review: bool
    reason: str | None = None


def _number(words: str) -> tuple[int | None, int]:
    """Return parsed number and number of consumed whitespace tokens, not a fuzzy guess."""
    tokens = words.split()
    if not tokens:
        return None, 0
    if reference_key(tokens[0]).isdigit():
        return int(reference_key(tokens[0])), 1
    t = tokens[0]
    if t in _UNIT:
        if len(tokens) >= 3 and tokens[1] == "و" and tokens[2] in _TEN:
            return _UNIT[t] + _TEN[tokens[2]], 3
        if len(tokens) >= 2 and tokens[1].startswith("و") and tokens[1][1:] in _TEN:
            return _UNIT[t] + _TEN[tokens[1][1:]], 2
        return _UNIT[t], 1
    if t in _TEN:
        return _TEN[t], 1
    return None, 0


def _article_number(text: str) -> int | None:
    text = text.strip(" ()")
    if " بعد " in text:
        left, right = text.split(" بعد ", 1)
        if right in _HUNDREDS:
            low, n = _number(left)
            if low is not None and n == len(left.split()):
                return _HUNDREDS[right] + low
        return None
    low, n = _number(text)
    return low if low is not None and n == len(text.split()) else None


def parse_legislative_reference(text: str) -> LegislativeReference | None:
    matches = list(_PATTERN.finditer(text))
    if not matches:
        return None
    if len(matches) != 1:
        return LegislativeReference(None, None, None, None, text, True, "multiple_articles")
    if re.search(r"(?:المادة|مادة)\s+", matches[0].group(1)):
        return LegislativeReference(None, None, None, None, text, True, "multiple_articles")
    start = matches[0].group(1)
    fragment = _STOP.split(start, 1)[0].strip()
    fragment = re.split(r"\s+(?:هل|ما|؟|,)", fragment, 1)[0].strip()
    # Clause qualifiers can occur before the article, and are retained only when explicit.
    before = text[:matches[0].start()]
    paragraph_match = re.search(r"الفقرة\s+(" + _DIG + r"|[أ-ي])\b", before)
    item_match = re.search(r"البند\s+([أ-ي]|" + _DIG + r")\b", before)
    paragraph = reference_key(paragraph_match.group(1)) if paragraph_match else None
    item = reference_key(item_match.group(1)) if item_match else None
    repeated = None
    repeated_match = re.search(r"\bالمكررة?\s*(" + _WORD + r"|" + _DIG + r")?", fragment)
    if repeated_match:
        repeated_word = repeated_match.group(1)
        repeated = _ORD.get(repeated_word or "الأول")
        if repeated is None and repeated_word and reference_key(repeated_word).isdigit():
            repeated = int(reference_key(repeated_word))
        fragment = fragment[:repeated_match.start()].strip()
    article = _article_number(fragment)
    bad = article is None or bool(repeated_match and repeated is None)
    return LegislativeReference(article, repeated, paragraph, item, text, bad,
                                "unparsed_or_ambiguous_reference" if bad else None)
