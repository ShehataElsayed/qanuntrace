"""Arabic legal structure and amendment comparisons. Candidate extraction, not legal validation."""
from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from .core import reference_key
from .types import LegalRecord


@dataclass(frozen=True)
class ArticleMention:
    article: str
    instrument_hint: str | None
    start: int
    end: int

@dataclass(frozen=True)
class TextDifference:
    old_source_id: str
    new_source_id: str
    tag: str
    old_text: str
    new_text: str

_NUMBER = r"[0-9٠-٩۰-۹]+"
_ARTICLE = re.compile(r"الماد[ةه]\s*(?:\(\s*(" + _NUMBER + r")\s*\)|(?:رقم\s*)?(" + _NUMBER + r"))"
                      r"(?:\s*من\s*(?:نظام|لائحة)\s+([^\n،.؛]{1,80}))?", re.UNICODE)

def article_mentions(text: str) -> tuple[ArticleMention, ...]:
    """Extract numeric Arabic article mentions. Written-out ordinals need human review."""
    return tuple(ArticleMention(reference_key(m.group(1) or m.group(2)),
                                m.group(3).strip() if m.group(3) else None,
                                m.start(), m.end()) for m in _ARTICLE.finditer(text))

def edition_diff(old: LegalRecord, new: LegalRecord) -> tuple[TextDifference, ...]:
    """Compare same instrument/article across versions; no claim about legal effect."""
    if old.instrument_id != new.instrument_id or reference_key(old.reference) != reference_key(new.reference):
        raise ValueError("diff requires the same instrument and article")
    from hashlib import sha256
    for record in (old, new):
        if sha256(record.exact_text.encode("utf-8")).hexdigest() != record.source_hash:
            raise ValueError("source hash mismatch")
    out = []
    for tag, i, j, k, l in SequenceMatcher(None, old.exact_text, new.exact_text).get_opcodes():
        if tag != "equal":
            out.append(TextDifference(old.source_id, new.source_id, tag,
                                      old.exact_text[i:j], new.exact_text[k:l]))
    return tuple(out)

@dataclass(frozen=True)
class JudgmentLinkCandidate:
    judgment_source_id: str
    article_source_id: str
    mention: ArticleMention
    status: str = "needs_review"

def link_candidates(judgment: LegalRecord, articles: tuple[LegalRecord, ...]) -> tuple[JudgmentLinkCandidate, ...]:
    if judgment.kind != "judgment":
        raise ValueError("source must be a judgment")
    # Same article number is not enough to prove which statute the court applied.
    return tuple(JudgmentLinkCandidate(judgment.source_id, a.source_id, mention)
                 for mention in article_mentions(judgment.exact_text)
                 for a in articles if reference_key(a.reference) == mention.article)
