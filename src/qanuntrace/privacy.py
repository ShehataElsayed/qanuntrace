"""Boundary controls for model-bound case text. Detection is incomplete by design."""
from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

SensitiveKind = Literal["email", "phone", "national_id", "commercial_register", "custom"]

@dataclass(frozen=True)
class SensitiveSpan:
    start: int
    end: int
    kind: SensitiveKind

@dataclass(frozen=True)
class RedactedText:
    text: str
    spans: tuple[SensitiveSpan, ...]
    needs_review: bool = True

# Deliberately bounded syntax examples, not an assertion of complete PII coverage.
_EMAIL = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])")
_PHONE = re.compile(r"(?<!\d)(?:\+966|00966|0)5\d{8}(?!\d)")
_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
_ID = re.compile(r"(?<!\d)[12]\d{9}(?!\d)")
_REGISTER = re.compile(r"(?:سجل\s+تجاري|رقم\s+السجل)\s*[:：-]?\s*([0-9٠-٩]{10})")


def detect(text: str) -> tuple[SensitiveSpan, ...]:
    candidates: list[SensitiveSpan] = []
    candidates += [SensitiveSpan(m.start(), m.end(), "email") for m in _EMAIL.finditer(text)]
    candidates += [SensitiveSpan(m.start(), m.end(), "phone") for m in _PHONE.finditer(text)]
    normalized = text.translate(_DIGITS)
    candidates += [SensitiveSpan(m.start(), m.end(), "national_id")
                   for m in _ID.finditer(normalized)]
    candidates += [SensitiveSpan(m.start(1), m.end(1), "commercial_register")
                   for m in _REGISTER.finditer(text)]
    accepted: list[SensitiveSpan] = []
    for span in sorted(candidates, key=lambda s: (s.start, -(s.end-s.start))):
        if not accepted or span.start >= accepted[-1].end:
            accepted.append(span)
    return tuple(accepted)


def redact(text: str, custom: Callable[[str], tuple[SensitiveSpan, ...]] | None = None
           ) -> RedactedText:
    spans = list(detect(text))
    if custom:
        spans.extend(custom(text))
    ordered = sorted(spans, key=lambda s: (s.start, -s.end))
    for index, span in enumerate(ordered):
        if (span.start < 0 or span.end > len(text) or span.end <= span.start
            or (index and span.start < ordered[index-1].end)):
            raise ValueError("sensitive spans overlap or are out of bounds")
    parts: list[str] = []
    cursor = 0
    for span in ordered:
        parts.append(text[cursor:span.start])
        parts.append(f"[REDACTED_{span.kind.upper()}]")
        cursor = span.end
    parts.append(text[cursor:])
    return RedactedText("".join(parts), tuple(ordered))


def safe_model_payload(text: str, *, reviewed: bool = False,
                       custom: Callable[[str], tuple[SensitiveSpan, ...]] | None = None) -> str:
    """Block remote transfer until a human-approved policy has reviewed PII misses."""
    result = redact(text, custom)
    if not reviewed:
        raise PermissionError("PII review and transfer authorization required")
    return result.text
