"""Legal professional review checklists, not autonomous legal advice."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .types import LegalRecord

Mode = Literal['lawyer','counsel','judge']

@dataclass(frozen=True)
class ReviewStep:
    mode: Mode
    name: str
    purpose: str
    required_kinds: tuple[str, ...]
    status: str = 'needs_review'

@dataclass(frozen=True)
class ReviewPlan:
    mode: Mode
    steps: tuple[ReviewStep, ...]
    source_ids: tuple[str, ...]
    caveat: str = 'Human legal review required; this plan is not legal advice.'

_WORKFLOWS: dict[Mode, tuple[tuple[str,str,tuple[str,...]],...]] = {
    'lawyer': (
        ('issues','Identify disputed facts and legal issues',('article','regulation','judgment')),
        ('support','Locate supporting provisions and judgments',('article','judgment')),
        ('adverse','Locate adverse provisions and counterarguments',('article','judgment')),
        ('procedure','Check deadlines, jurisdiction and procedural requirements',('article','regulation')),
    ),
    'counsel': (
        ('facts','Separate stated facts from unverified assumptions',()),
        ('rule','Identify current and historical applicable rules',('article','regulation')),
        ('risk','List alternatives and uncertainty, including adverse authority',('article','judgment')),
        ('recommendation','Draft review-only options with bounded caveats',()),
    ),
    'judge': (
        ('facts','Characterize and verify facts (التكييف)',()),
        ('hierarchy','Check authority and temporal applicability; hierarchy needs local-law review',('article','regulation')),
        ('evidence','Weigh source evidence and conflicting judgments',('judgment','article')),
        ('reasoning','Produce review-only reasons (تسبيب), not a judicial decision',()),
    ),
}

def make_review_plan(mode: Mode, sources: tuple[LegalRecord,...]) -> ReviewPlan:
    if mode not in _WORKFLOWS:
        raise ValueError('unknown legal review mode')
    # A checklist does not infer law hierarchy or an outcome from source presence.
    steps = tuple(ReviewStep(mode,name,purpose,kinds) for name,purpose,kinds in _WORKFLOWS[mode])
    return ReviewPlan(mode,steps,tuple(s.source_id for s in sources))
