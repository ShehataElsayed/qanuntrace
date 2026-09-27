from qanuntrace.metrics import assess_labeled_cases, quote_metrics
from qanuntrace.types import Answer, Finding


def test_quote_rate_and_unknown_labels():
    a = Answer('verified_quote', (Finding('verified_quote','exact'), Finding('needs_review','interpretation')),
               'text', ())
    assert quote_metrics(a).strict_quote_rate == 0.5
    assert quote_metrics(Answer('abstained',(),'',())).strict_quote_rate is None
    report = assess_labeled_cases(((True,True),(False,None)))
    assert report.faithfulness_agreement == 0.5 and report.relevance_agreement == 1.0
    assert report.missing_labels == 1
