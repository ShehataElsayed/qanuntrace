import pytest

from qanuntrace.reasoning import make_review_plan


def test_lawyer_counsel_judge_plans_are_review_only():
    for mode in ('lawyer','counsel','judge'):
        plan = make_review_plan(mode, ())
        assert plan.mode == mode
        assert len(plan.steps) == 4
        assert all(s.status == 'needs_review' for s in plan.steps)
    assert 'adverse' in [s.name for s in make_review_plan('lawyer',()).steps]
    assert 'hierarchy' in [s.name for s in make_review_plan('judge',()).steps]
    with pytest.raises(ValueError): make_review_plan('unknown',())
