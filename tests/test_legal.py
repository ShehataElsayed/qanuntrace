import pytest

from qanuntrace import LegalRecord, Pipeline, Query
from qanuntrace.adapters import MemoryStore
from qanuntrace.evaluation import EvalCase, evaluate
from qanuntrace.generators import CallableGenerator
from qanuntrace.legal import article_mentions, edition_diff, link_candidates


def test_mentions_candidate_only():
    mentions = article_mentions('استند الحكم إلى المادة (١٢) من نظام العمل، والمادة رقم 13.')
    assert [m.article for m in mentions] == ['12','13']
    judgment = LegalRecord.make('j','court','v1','judgment','1','وردت المادة (١٢).','fixture:j')
    a = LegalRecord.make('a','law1','v1','article','12','نص تجريبي','fixture:a')
    b = LegalRecord.make('b','law2','v1','article','١٢','نص مختلف','fixture:b')
    assert len(link_candidates(judgment,(a,b))) == 2
    assert all(x.status == 'needs_review' for x in link_candidates(judgment,(a,b)))

def test_version_diff():
    a = LegalRecord.make('a','law','v1','article','1','يجوز','fixture:a')
    b = LegalRecord.make('b','law','v2','article','1','لا يجوز','fixture:b')
    assert any(d.new_text == 'لا ' for d in edition_diff(a,b))
    with pytest.raises(ValueError):
        edition_diff(a,LegalRecord.make('x','other','v2','article','1','لا يجوز','fixture:x'))

def test_eval_abstention():
    r = LegalRecord.make('a','law','v1','article','1','نص','fixture:a')
    p = Pipeline(MemoryStore([r]), CallableGenerator(lambda *_: '[]'))
    result = evaluate(p,(EvalCase(Query('unknown',instrument_id='other'),None),))
    assert result.source_accuracy == 1 and result.abstention_accuracy == 1
